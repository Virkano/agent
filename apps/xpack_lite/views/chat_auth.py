import json

from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _
from rest_framework.request import Request
from rest_framework.views import APIView

from application.models import ApplicationAccessToken, ChatUserType
from common.auth.common import ChatAuthentication, ChatUserToken, FileToken
from common.auth.authenticate import ChatTokenAuth, TokenAuth
from common.constants.authentication_type import AuthenticationType
from common.exception.app_exception import AppApiException
from common.result import result
from common.utils.common import password_encrypt, password_verify
from common.utils.rsa_util import decrypt
from maxkb.const import CONFIG
from system_manage.models.chat_user import ChatUser
from users.models import User
from xpack_lite.models import ChatAuthSetting, ChatPlatform
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


def _create_chat_user_token(application_access_token, chat_user):
    token = ChatUserToken(
        application_access_token.application_id,
        None,
        application_access_token.access_token,
        AuthenticationType.CHAT_USER,
        ChatUserType.CHAT_USER,
        chat_user.id,
        ChatAuthentication('login'),
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
        if (
            application_access_token.authentication
            and application_access_token.authentication_value.get('type') == 'login'
            and not is_auth_chat_user(chat_user.id, application_access_token.application_id)
        ):
            raise AppApiException(1002, _('The chat user is not authorized.'))

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
