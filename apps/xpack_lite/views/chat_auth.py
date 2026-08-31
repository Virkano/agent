import json
import re

import requests
import uuid_utils.compat as uuid
from django.db import IntegrityError, transaction
from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _
from rest_framework.request import Request
from rest_framework.views import APIView

from application.models import ApplicationAccessToken, ChatUserType
from common.auth.common import ChatAuthentication, ChatUserToken, FileToken
from common.auth.authenticate import ChatTokenAuth, TokenAuth
from common.constants.authentication_type import AuthenticationType
from common.constants.permission_constants import Group
from common.exception.app_exception import AppApiException
from common.result import result
from common.utils.common import get_random_chars, password_encrypt, password_verify
from common.utils.rsa_util import decrypt
from telecom_ai_agent.const import CONFIG
from knowledge.models import Knowledge
from system_manage.models.chat_user import (
    ChatUser,
    ResourceChatUserGroupAuthorize,
    UserGroup,
    UserGroupRelation,
)
from system_manage.models.resource_mapping import ResourceMapping
from users.models import User
from xpack_lite.models import ChatAuthSetting, ChatExternalAccount, ChatPlatform
from xpack_lite.services import chat_user_to_dict, is_admin, is_auth_chat_user


AUTH_TYPE_NAMES = {
    'LDAP': 'LDAP',
    'CAS': 'CAS',
    'OIDC': 'OIDC',
    'OAuth2': 'OAuth2',
}

DEFAULT_AUTH_CONFIG = {
    'LDAP': {
        'ldap_server': '',
        'base_dn': '',
        'password': '',
        'ou': '',
        'ldap_filter': '',
        'ldap_mapping': '',
    },
    'CAS': {
        'ldpUri': '',
        'validateUrl': '',
        'redirectUrl': '',
    },
    'OIDC': {
        'authEndpoint': '',
        'tokenEndpoint': '',
        'userInfoEndpoint': '',
        'scope': '',
        'state': '',
        'clientId': '',
        'clientSecret': '',
        'fieldMapping': '{"username": "preferred_username", "email": "email"}',
        'redirectUrl': '',
    },
    'OAuth2': {
        'authEndpoint': '',
        'tokenEndpoint': '',
        'userInfoEndpoint': '',
        'scope': '',
        'clientId': '',
        'clientSecret': '',
        'redirectUrl': '',
        'fieldMapping': '',
    },
}

PLATFORM_NAMES = {
    'wecom': '企业微信',
    'dingtalk': '钉钉',
    'lark': '飞书',
}

DINGTALK_USER_GROUP_ID = 'dingtalk'
DINGTALK_USER_GROUP_NAME = '钉钉用户组'


def _request_data(request):
    payload = dict(request.data or {})
    encrypted_data = payload.get('encryptedData')
    if encrypted_data:
        try:
            decrypted = json.loads(decrypt(encrypted_data) or '{}')
        except Exception:
            raise AppApiException(500, 'Invalid encrypted data')
        if isinstance(decrypted, dict):
            payload.update(decrypted)
    return payload


def _get_application_access_token(access_token):
    application_access_token = QuerySet(ApplicationAccessToken).filter(
        access_token=access_token,
        is_active=True,
    ).first()
    if application_access_token is None:
        raise AppApiException(404, 'Invalid access_token')
    return application_access_token


def _create_chat_user_token(application_access_token, chat_user, auth_type='login'):
    token = ChatUserToken(
        application_access_token.application_id,
        None,
        application_access_token.access_token,
        AuthenticationType.CHAT_USER,
        ChatUserType.CHAT_USER,
        chat_user.id,
        ChatAuthentication(auth_type),
    ).to_token()
    file_token = FileToken(
        str(chat_user.id),
        AuthenticationType.CHAT_USER.value,
        application_id=str(application_access_token.application_id),
    ).to_token()
    return token, file_token


def _set_file_cookie(request, response, file_token):
    is_https = request.scheme == 'https'
    response.set_cookie(
        key='mk_file_auth',
        value=file_token,
        max_age=7 * 24 * 3600,
        path=CONFIG.get_chat_path(),
        secure=is_https,
        httponly=True,
        samesite='None' if is_https else 'Lax',
    )
    return response


def _require_admin(request):
    if not is_admin(request.user.id):
        raise AppApiException(403, 'No permission to access')


def _auth_type(value):
    for auth_type in AUTH_TYPE_NAMES:
        if auth_type.lower() == str(value).lower():
            return auth_type
    raise AppApiException(500, 'Unsupported auth type')


def _setting_to_dict(setting):
    auth_type = _auth_type(setting.auth_type)
    config = {**DEFAULT_AUTH_CONFIG.get(auth_type, {}), **(setting.config or {})}
    return {
        'id': auth_type,
        'auth_type': auth_type,
        'name': setting.name,
        'config': config,
        'is_active': setting.enabled,
    }


def _get_setting(auth_type):
    auth_type = _auth_type(auth_type)
    setting, _ = ChatAuthSetting.objects.get_or_create(
        auth_type=auth_type,
        defaults={
            'name': AUTH_TYPE_NAMES[auth_type],
            'enabled': False,
            'config': DEFAULT_AUTH_CONFIG.get(auth_type, {}),
        },
    )
    return setting


def _platform_config(platform_key):
    if platform_key == 'wecom':
        return {'corp_id': '', 'agent_id': '', 'app_secret': '', 'callback_url': ''}
    return {'app_key': '', 'app_secret': '', 'callback_url': ''}


def _platform_to_dict(platform):
    key = platform.auth_type
    return {
        'id': platform.id,
        'auth_type': key,
        'key': key,
        'name': platform.name,
        'is_active': platform.is_active,
        'is_valid': platform.is_valid,
        'config': {**_platform_config(key), **(platform.config or {})},
    }


def _platform_to_public_dict(platform):
    data = _platform_to_dict(platform)
    config = dict(data.get('config') or {})
    config.pop('app_secret', None)
    data['config'] = config
    return data


def _get_platform(platform_key):
    if platform_key not in PLATFORM_NAMES:
        raise AppApiException(500, 'Unsupported platform')
    platform, _ = ChatPlatform.objects.get_or_create(
        auth_type=platform_key,
        defaults={
            'name': PLATFORM_NAMES[platform_key],
            'is_active': False,
            'is_valid': False,
            'config': _platform_config(platform_key),
        },
    )
    return platform


def _require_platform_enabled(platform_key):
    platform = _get_platform(platform_key)
    if not platform.is_active or not platform.is_valid:
        raise AppApiException(1002, _('Authentication information is incorrect'))
    return platform


def _ensure_platform_allowed(application_access_token, platform_key):
    if not application_access_token.authentication:
        return
    authentication_value = application_access_token.authentication_value or {}
    if authentication_value.get('type') != 'login':
        return
    if platform_key not in (authentication_value.get('login_value') or []):
        raise AppApiException(1002, _('Authentication information is incorrect'))


def _ensure_chat_user_authorized(application_access_token, chat_user):
    if (
        application_access_token.authentication
        and application_access_token.authentication_value.get('type') == 'login'
        and not is_auth_chat_user(chat_user.id, application_access_token.application_id)
    ):
        raise AppApiException(1002, _('The chat user is not authorized.'))


def _ensure_dingtalk_user_group():
    group, _ = UserGroup.objects.get_or_create(
        id=DINGTALK_USER_GROUP_ID,
        defaults={'name': DINGTALK_USER_GROUP_NAME},
    )
    return group


def _ensure_chat_user_in_platform_group(chat_user, platform_key):
    if platform_key != 'dingtalk':
        return
    group = _ensure_dingtalk_user_group()
    UserGroupRelation.objects.get_or_create(
        user=chat_user,
        group=group,
        defaults={'id': uuid.uuid7()},
    )


def _ensure_platform_group_authorized(application_access_token, platform_key):
    if platform_key != 'dingtalk':
        return
    group = _ensure_dingtalk_user_group()
    application = getattr(application_access_token, 'application', None)
    workspace_id = getattr(application, 'workspace_id', None) or 'default'
    application_id = str(application_access_token.application_id)
    ResourceChatUserGroupAuthorize.objects.update_or_create(
        user_group=group,
        resource_id=application_id,
        resource_type=Group.APPLICATION.value,
        defaults={'workspace_id': workspace_id, 'is_auth': True},
    )
    knowledge_ids = list(
        ResourceMapping.objects.filter(
            source_type=Group.APPLICATION.value,
            source_id=application_id,
            target_type=Group.KNOWLEDGE.value,
        ).values_list('target_id', flat=True)
    )
    knowledge_workspace_map = {
        str(row.id): row.workspace_id
        for row in Knowledge.objects.filter(id__in=knowledge_ids).only('id', 'workspace_id')
    }
    for knowledge_id in knowledge_ids:
        ResourceChatUserGroupAuthorize.objects.update_or_create(
            user_group=group,
            resource_id=knowledge_id,
            resource_type=Group.KNOWLEDGE.value,
            defaults={'workspace_id': knowledge_workspace_map.get(str(knowledge_id), workspace_id), 'is_auth': True},
        )


def _unique_chat_username(platform_key, external_id):
    normalized = re.sub(r'[^a-zA-Z0-9_@.-]', '_', str(external_id or 'user'))
    return f'{platform_key}_{normalized}'[:150]


def _unique_chat_nick_name(preferred_name, platform_key):
    base_name = (preferred_name or PLATFORM_NAMES.get(platform_key) or platform_key).strip()[:120]
    for _attempt in range(10):
        nick_name = f'{base_name}_{get_random_chars(6)}'[:150]
        if not ChatUser.objects.filter(nick_name=nick_name).exists():
            return nick_name
    return f'{platform_key}_{get_random_chars(16)}'


def _get_or_create_external_chat_user(platform_key, external_id, profile):
    account = ChatExternalAccount.objects.select_related('chat_user').filter(
        platform=platform_key,
        external_id=external_id,
    ).first()
    if account is not None:
        account.profile = profile
        account.union_id = profile.get('unionId') or profile.get('union_id') or account.union_id
        account.open_id = profile.get('openId') or profile.get('open_id') or account.open_id
        account.save(update_fields=['profile', 'union_id', 'open_id', 'update_time'])
        _ensure_chat_user_in_platform_group(account.chat_user, platform_key)
        return account.chat_user

    username = _unique_chat_username(platform_key, external_id)
    if ChatUser.objects.filter(username=username).exists():
        username = f'{username[:130]}_{get_random_chars(8)}'

    with transaction.atomic():
        try:
            chat_user = ChatUser.objects.create(
                username=username,
                nick_name=_unique_chat_nick_name(
                    profile.get('nick') or profile.get('name') or profile.get('nickname'),
                    platform_key,
                ),
                password=password_encrypt(get_random_chars(32)),
                source=platform_key,
                email=profile.get('email') or None,
                phone=profile.get('mobile') or profile.get('phone') or '',
                is_active=True,
            )
            ChatExternalAccount.objects.create(
                chat_user=chat_user,
                platform=platform_key,
                external_id=external_id,
                union_id=profile.get('unionId') or profile.get('union_id') or '',
                open_id=profile.get('openId') or profile.get('open_id') or '',
                profile=profile,
            )
        except IntegrityError:
            account = ChatExternalAccount.objects.select_related('chat_user').get(
                platform=platform_key,
                external_id=external_id,
            )
            _ensure_chat_user_in_platform_group(account.chat_user, platform_key)
            return account.chat_user
    _ensure_chat_user_in_platform_group(chat_user, platform_key)
    return chat_user


def _request_dingtalk_user(config, code):
    client_id = config.get('app_key')
    client_secret = config.get('app_secret')
    if not client_id or not client_secret:
        raise AppApiException(500, _('Authentication information is incorrect'))

    def get_dingtalk_error(data):
        if not isinstance(data, dict):
            return _('Authentication information is incorrect')
        message = data.get('message') or data.get('msg') or data.get('error_description') or data.get('error')
        error_code = data.get('code') or data.get('errcode')
        if error_code and message:
            return f'DingTalk error {error_code}: {message}'
        return message or _('Authentication information is incorrect')

    try:
        token_response = requests.post(
            'https://api.dingtalk.com/v1.0/oauth2/userAccessToken',
            json={
                'clientId': client_id,
                'clientSecret': client_secret,
                'code': code,
                'grantType': 'authorization_code',
            },
            timeout=10,
        )
        try:
            token_data = token_response.json()
        except ValueError:
            token_data = {}
        if not token_response.ok:
            raise AppApiException(1002, get_dingtalk_error(token_data))
        user_access_token = token_data.get('accessToken')
        if not user_access_token:
            raise AppApiException(1002, get_dingtalk_error(token_data))

        user_response = requests.get(
            'https://api.dingtalk.com/v1.0/contact/users/me',
            headers={'x-acs-dingtalk-access-token': user_access_token},
            timeout=10,
        )
        try:
            user_data = user_response.json()
        except ValueError:
            user_data = {}
        if not user_response.ok:
            raise AppApiException(1002, get_dingtalk_error(user_data))
    except AppApiException:
        raise
    except Exception as e:
        raise AppApiException(1002, f'DingTalk authentication failed: {e}')

    external_id = user_data.get('unionId') or user_data.get('openId')
    if not external_id:
        raise AppApiException(1002, _('Authentication information is incorrect'))
    return external_id, user_data


class ChatAuthTypeView(APIView):
    authentication_classes = [TokenAuth]

    def get(self, request: Request):
        data = [{'label': '账号登录', 'value': 'LOCAL', 'auth_type': 'LOCAL', 'name': '账号登录'}]
        for auth_type in AUTH_TYPE_NAMES:
            setting = _get_setting(auth_type)
            if setting.enabled:
                data.append({
                    'label': setting.name,
                    'value': setting.auth_type,
                    'auth_type': setting.auth_type,
                    'name': setting.name,
                })
        for platform in ChatPlatform.objects.filter(is_active=True, is_valid=True).exclude(auth_type='LOCAL').order_by('name'):
            data.append({
                'label': platform.name,
                'value': platform.auth_type,
                'auth_type': platform.auth_type,
                'name': platform.name,
            })
        return result.success(data)


class ChatAuthDetailView(APIView):
    authentication_classes = [TokenAuth]

    def get(self, request: Request, auth_type):
        _require_admin(request)
        return result.success(_setting_to_dict(_get_setting(auth_type)))


class ChatAuthInfoView(APIView):
    authentication_classes = [TokenAuth]

    def put(self, request: Request, auth_type):
        _require_admin(request)
        setting = _get_setting(auth_type)
        payload = request.data or {}
        setting.enabled = bool(payload.get('is_active'))
        setting.config = payload.get('config') or {}
        setting.save(update_fields=['enabled', 'config', 'update_time'])
        return result.success(_setting_to_dict(setting))


class ChatAuthConnectionView(APIView):
    authentication_classes = [TokenAuth]

    def post(self, request: Request):
        _require_admin(request)
        return result.success(True)


class ChatAuthPlatformSourceView(APIView):
    authentication_classes = [TokenAuth]

    def get(self, request: Request):
        _require_admin(request)
        return result.success([_platform_to_dict(_get_platform(key)) for key in PLATFORM_NAMES])

    def post(self, request: Request):
        _require_admin(request)
        payload = request.data or {}
        key = payload.get('key') or payload.get('auth_type')
        platform = _get_platform(key)
        platform.is_active = bool(payload.get('isActive', payload.get('is_active', platform.is_active)))
        platform.is_valid = bool(payload.get('isValid', payload.get('is_valid', True)))
        platform.config = payload.get('config') or platform.config or {}
        platform.save(update_fields=['is_active', 'is_valid', 'config'])
        return result.success(_platform_to_dict(platform))

    def put(self, request: Request):
        _require_admin(request)
        return result.success(True)


class PublicChatQrTypeView(APIView):
    authentication_classes = []

    def get(self, request: Request):
        platforms = ChatPlatform.objects.filter(is_active=True, is_valid=True).exclude(auth_type='LOCAL').order_by('name')
        return result.success([
            {'key': platform.auth_type, 'value': platform.name, 'auth_type': platform.auth_type, 'name': platform.name}
            for platform in platforms
        ])


class PublicChatQrPlatformSourceView(APIView):
    authentication_classes = []

    def get(self, request: Request):
        platforms = ChatPlatform.objects.filter(is_active=True, is_valid=True).exclude(auth_type='LOCAL').order_by('name')
        return result.success([_platform_to_public_dict(platform) for platform in platforms])


class DingTalkChatUserCallbackView(APIView):
    authentication_classes = []

    def get(self, request: Request):
        code = request.query_params.get('code')
        access_token = request.query_params.get('accessToken') or request.query_params.get('access_token')
        if not code or not access_token:
            raise AppApiException(500, _('Authentication information is incorrect'))

        platform = _require_platform_enabled('dingtalk')
        application_access_token = _get_application_access_token(access_token)
        _ensure_platform_allowed(application_access_token, 'dingtalk')
        external_id, profile = _request_dingtalk_user(platform.config or {}, code)
        chat_user = _get_or_create_external_chat_user('dingtalk', external_id, profile)
        if not chat_user.is_active:
            raise AppApiException(1005, _('The user has been disabled, please contact the administrator!'))
        _ensure_platform_group_authorized(application_access_token, 'dingtalk')
        _ensure_chat_user_authorized(application_access_token, chat_user)

        token, file_token = _create_chat_user_token(application_access_token, chat_user, 'dingtalk')
        response = result.success({'token': token})
        return _set_file_cookie(request, response, file_token)


class LocalChatUserLoginView(APIView):
    def post(self, request: Request, access_token):
        payload = _request_data(request)
        username = payload.get('username')
        password = payload.get('password')
        if not username or not password:
            raise AppApiException(500, _('The username or password is incorrect'))

        application_access_token = _get_application_access_token(access_token)
        chat_user = QuerySet(ChatUser).filter(username=username, source__in=['LOCAL', 'SYSTEM']).first()
        if chat_user is None:
            raise AppApiException(500, _('The username or password is incorrect'))
        if not password_verify(password, chat_user.password):
            if chat_user.source == 'SYSTEM':
                system_user = QuerySet(User).filter(username=username, is_active=True).first()
                if system_user is not None and password_verify(password, system_user.password):
                    chat_user.password = system_user.password
                    chat_user.save(update_fields=['password'])
                else:
                    raise AppApiException(500, _('The username or password is incorrect'))
            else:
                raise AppApiException(500, _('The username or password is incorrect'))
        if not chat_user.is_active:
            raise AppApiException(1005, _('The user has been disabled, please contact the administrator!'))
        _ensure_chat_user_authorized(application_access_token, chat_user)

        token, file_token = _create_chat_user_token(application_access_token, chat_user)
        response = result.success({'token': token})
        return _set_file_cookie(request, response, file_token)


class LocalChatUserLogoutView(APIView):
    authentication_classes = [ChatTokenAuth]

    def post(self, request: Request):
        response = result.success(True)
        response.delete_cookie('mk_file_auth', path=CONFIG.get_chat_path())
        return response


class LocalChatUserProfileView(APIView):
    authentication_classes = [ChatTokenAuth]

    def get(self, request: Request):
        chat_user_id = getattr(request.auth, 'chat_user_id', None)
        chat_user = QuerySet(ChatUser).filter(id=chat_user_id, is_active=True).first()
        if chat_user is None:
            raise AppApiException(1002, 'Authentication information is incorrect')
        return result.success(chat_user_to_dict(chat_user))


class LocalChatUserResetPasswordView(APIView):
    authentication_classes = [ChatTokenAuth]

    def post(self, request: Request):
        payload = _request_data(request)
        password = payload.get('password')
        re_password = payload.get('re_password')
        if not password or password != re_password:
            raise AppApiException(500, 'Passwords do not match')
        chat_user_id = getattr(request.auth, 'chat_user_id', None)
        updated = ChatUser.objects.filter(id=chat_user_id, is_active=True).update(password=password_encrypt(password))
        if not updated:
            raise AppApiException(1002, 'Authentication information is incorrect')
        return result.success(True)
