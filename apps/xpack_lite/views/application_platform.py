import hashlib

import uuid_utils.compat as uuid
from django.db.models import QuerySet
from rest_framework.request import Request
from rest_framework.views import APIView

from application.models import Application, ApplicationAccessToken
from common.auth.authenticate import TokenAuth
from common.auth.authentication import get_is_permissions
from common.constants.permission_constants import PermissionConstants, RoleConstants
from common.exception.app_exception import AppApiException
from common.result import result
from xpack_lite.models import ApplicationSetting
from xpack_lite.services import is_admin


PLATFORM_CONFIG_DEFAULTS = {
    'wechat': {
        'app_id': '',
        'app_secret': '',
        'token': '',
        'encoding_aes_key': '',
        'is_certification': False,
        'callback_url': '',
    },
    'dingtalk': {'client_id': '', 'client_secret': '', 'callback_url': ''},
    'wecom': {
        'app_id': '',
        'agent_id': '',
        'secret': '',
        'token': '',
        'encoding_aes_key': '',
        'callback_url': '',
    },
    'lark': {'app_id': '', 'app_secret': '', 'verification_token': '', 'callback_url': ''},
    'slack': {'signing_secret': '', 'bot_user_token': '', 'callback_url': ''},
    'wecomBot': {'token': '', 'encoding_aes_key': '', 'callback_url': ''},
}

OPTIONAL_FIELDS = {
    'wechat': {'callback_url', 'is_certification'},
    'dingtalk': {'callback_url'},
    'wecom': {'callback_url'},
    'lark': {'callback_url', 'verification_token'},
    'slack': {'callback_url'},
    'wecomBot': {'callback_url'},
}

PLATFORM_STORE_KEY = 'platforms'

APPLICATION_SETTING_FIELDS = [
    'show_history',
    'draggable',
    'show_guide',
    'avatar',
    'show_avatar',
    'float_icon',
    'disclaimer',
    'disclaimer_value',
    'custom_theme',
    'user_avatar',
    'show_user_avatar',
    'show_share',
    'float_location',
    'chat_background',
]


def _require_platform(platform_type):
    if platform_type not in PLATFORM_CONFIG_DEFAULTS:
        raise AppApiException(500, 'Unsupported platform')


def _get_application(application_id, workspace_id=None):
    queryset = QuerySet(Application).filter(id=application_id)
    if workspace_id:
        queryset = queryset.filter(workspace_id=workspace_id)
    application = queryset.first()
    if application is None:
        raise AppApiException(404, 'Application does not exist')
    return application


def _require_workspace_access(
    request,
    workspace_id,
    application_id,
    permission=PermissionConstants.APPLICATION_READ,
):
    application = _get_application(application_id, workspace_id)
    if not get_is_permissions(
        request,
        workspace_id=workspace_id,
        application_id=application_id,
    )(
        permission.get_workspace_application_permission(),
        permission.get_workspace_permission_workspace_manage_role(),
        RoleConstants.WORKSPACE_MANAGE.get_workspace_role(),
    ):
        raise AppApiException(403, 'No permission to access')
    return application


def _require_system_access(request, application_id):
    if not is_admin(request.user.id):
        raise AppApiException(403, 'No permission to access')
    return _get_application(application_id)


def _get_access_token(application):
    access_token, _ = ApplicationAccessToken.objects.get_or_create(
        application=application,
        defaults={
            'access_token': hashlib.md5(str(uuid.uuid7()).encode()).hexdigest()[8:24],
            'is_active': True,
        },
    )
    return access_token


def _get_application_setting(application):
    setting, _ = ApplicationSetting.objects.get_or_create(application=application)
    return setting


def _application_setting_to_dict(setting):
    return {field: getattr(setting, field) for field in APPLICATION_SETTING_FIELDS}


def _update_application_setting(setting, payload):
    update_fields = []
    for field in APPLICATION_SETTING_FIELDS:
        if field not in payload:
            continue
        setattr(setting, field, payload.get(field))
        update_fields.append(field)
    if update_fields:
        setting.save(update_fields=update_fields)
    return _application_setting_to_dict(setting)


def _platforms_meta(access_token):
    authentication_value = access_token.authentication_value or {}
    platforms = authentication_value.get(PLATFORM_STORE_KEY)
    return platforms if isinstance(platforms, dict) else {}


def _save_platforms_meta(access_token, platforms):
    authentication_value = dict(access_token.authentication_value or {})
    authentication_value[PLATFORM_STORE_KEY] = platforms
    access_token.authentication_value = authentication_value
    access_token.save(update_fields=['authentication_value'])


def _platform_config(access_token, platform_type):
    defaults = PLATFORM_CONFIG_DEFAULTS[platform_type]
    platform_meta = _platforms_meta(access_token).get(platform_type) or {}
    config = platform_meta.get('config') if isinstance(platform_meta, dict) else {}
    return {**defaults, **(config or {})}


def _platform_exists(platform_type, config):
    required_fields = set(PLATFORM_CONFIG_DEFAULTS[platform_type]) - OPTIONAL_FIELDS.get(platform_type, set())
    return all(bool(config.get(field)) for field in required_fields)


def _platform_status(access_token):
    platforms = _platforms_meta(access_token)
    data = {}
    for platform_type in PLATFORM_CONFIG_DEFAULTS:
        meta = platforms.get(platform_type) or {}
        config = _platform_config(access_token, platform_type)
        exists = _platform_exists(platform_type, config)
        data[platform_type] = [exists, bool(meta.get('is_active')) if exists else False]
    return data


class WorkspaceApplicationPlatformStatusView(APIView):
    authentication_classes = [TokenAuth]

    def get(self, request: Request, workspace_id, application_id):
        application = _require_workspace_access(
            request,
            workspace_id,
            application_id,
            PermissionConstants.APPLICATION_ACCESS_READ,
        )
        return result.success(_platform_status(_get_access_token(application)))

    def post(self, request: Request, workspace_id, application_id):
        application = _require_workspace_access(
            request,
            workspace_id,
            application_id,
            PermissionConstants.APPLICATION_ACCESS_EDIT,
        )
        access_token = _get_access_token(application)
        platform_type = request.data.get('type')
        _require_platform(platform_type)
        platforms = _platforms_meta(access_token)
        meta = platforms.get(platform_type) or {}
        config = _platform_config(access_token, platform_type)
        platforms[platform_type] = {
            **meta,
            'config': config,
            'is_active': bool(request.data.get('status')) and _platform_exists(platform_type, config),
        }
        _save_platforms_meta(access_token, platforms)
        return result.success(True)


class WorkspaceApplicationPlatformConfigView(APIView):
    authentication_classes = [TokenAuth]

    def get(self, request: Request, workspace_id, application_id, platform_type):
        _require_platform(platform_type)
        application = _require_workspace_access(
            request,
            workspace_id,
            application_id,
            PermissionConstants.APPLICATION_ACCESS_READ,
        )
        return result.success(_platform_config(_get_access_token(application), platform_type))

    def post(self, request: Request, workspace_id, application_id, platform_type):
        _require_platform(platform_type)
        application = _require_workspace_access(
            request,
            workspace_id,
            application_id,
            PermissionConstants.APPLICATION_ACCESS_EDIT,
        )
        access_token = _get_access_token(application)
        platforms = _platforms_meta(access_token)
        meta = platforms.get(platform_type) or {}
        config = {**PLATFORM_CONFIG_DEFAULTS[platform_type], **(request.data or {})}
        exists = _platform_exists(platform_type, config)
        platforms[platform_type] = {
            **meta,
            'config': config,
            'is_active': bool(meta.get('is_active')) and exists,
        }
        _save_platforms_meta(access_token, platforms)
        return result.success(config)


class WorkspaceApplicationSettingView(APIView):
    authentication_classes = [TokenAuth]

    def get(self, request: Request, workspace_id, application_id):
        application = _require_workspace_access(
            request,
            workspace_id,
            application_id,
            PermissionConstants.APPLICATION_READ,
        )
        return result.success(_application_setting_to_dict(_get_application_setting(application)))

    def put(self, request: Request, workspace_id, application_id):
        application = _require_workspace_access(
            request,
            workspace_id,
            application_id,
            PermissionConstants.APPLICATION_EDIT,
        )
        return result.success(_update_application_setting(_get_application_setting(application), request.data or {}))


class SystemApplicationPlatformStatusView(APIView):
    authentication_classes = [TokenAuth]

    def get(self, request: Request, application_id):
        application = _require_system_access(request, application_id)
        return result.success(_platform_status(_get_access_token(application)))

    def post(self, request: Request, application_id):
        application = _require_system_access(request, application_id)
        access_token = _get_access_token(application)
        platform_type = request.data.get('type')
        _require_platform(platform_type)
        platforms = _platforms_meta(access_token)
        meta = platforms.get(platform_type) or {}
        config = _platform_config(access_token, platform_type)
        platforms[platform_type] = {
            **meta,
            'config': config,
            'is_active': bool(request.data.get('status')) and _platform_exists(platform_type, config),
        }
        _save_platforms_meta(access_token, platforms)
        return result.success(True)


class SystemApplicationPlatformConfigView(APIView):
    authentication_classes = [TokenAuth]

    def get(self, request: Request, application_id, platform_type):
        _require_platform(platform_type)
        application = _require_system_access(request, application_id)
        return result.success(_platform_config(_get_access_token(application), platform_type))

    def post(self, request: Request, application_id, platform_type):
        _require_platform(platform_type)
        application = _require_system_access(request, application_id)
        access_token = _get_access_token(application)
        platforms = _platforms_meta(access_token)
        meta = platforms.get(platform_type) or {}
        config = {**PLATFORM_CONFIG_DEFAULTS[platform_type], **(request.data or {})}
        exists = _platform_exists(platform_type, config)
        platforms[platform_type] = {
            **meta,
            'config': config,
            'is_active': bool(meta.get('is_active')) and exists,
        }
        _save_platforms_meta(access_token, platforms)
        return result.success(config)


class SystemApplicationSettingView(APIView):
    authentication_classes = [TokenAuth]

    def get(self, request: Request, application_id):
        application = _require_system_access(request, application_id)
        return result.success(_application_setting_to_dict(_get_application_setting(application)))

    def put(self, request: Request, application_id):
        application = _require_system_access(request, application_id)
        return result.success(_update_application_setting(_get_application_setting(application), request.data or {}))
