from rest_framework.request import Request
from rest_framework.views import APIView

from common.auth.authenticate import TokenAuth
from common.result import result
from xpack_lite.models import ChatAuthSetting, ChatPlatform


DEFAULT_LOGIN_AUTH_SETTING = {
    'max_attempts': 1,
    'failed_attempts': 5,
    'lock_time': 10,
    'default_value': 'LOCAL',
    'login_methods': ['LOCAL'],
    'role_id': 'USER',
    'workspace_id': 'default',
    'permission': 'NOT_AUTH',
    'auth_types': [{'label': '本地认证', 'value': 'LOCAL'}],
    'system_options': [{'label': '本地认证', 'value': 'LOCAL'}],
}

SYSTEM_AUTH_TYPE_NAMES = {
    'LDAP': 'LDAP',
    'CAS': 'CAS',
    'OIDC': 'OIDC',
    'OAuth2': 'OAuth2',
    'SAML2': 'SAML2',
}

PLATFORM_NAMES = {
    'wecom': '企业微信',
    'dingtalk': '钉钉',
    'lark': '飞书',
}

DEFAULT_SYSTEM_AUTH_CONFIG = {
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
    'SAML2': {
        'idpMetaUrl': '',
        'wantAssertionsSigned': True,
        'wantAuthnRequestsSigned': True,
        'privateKey': '',
        'certificate': '',
        'mapping': '',
        'spEntityId': '',
        'spAcs': '',
    },
}


def _auth_type(value):
    for auth_type in SYSTEM_AUTH_TYPE_NAMES:
        if auth_type.lower() == str(value).lower():
            return auth_type
    return str(value)


def _setting_key(auth_type):
    return f'SYSTEM_{_auth_type(auth_type)}'


def _setting_to_dict(setting):
    auth_type = _auth_type(setting.auth_type.replace('SYSTEM_', '', 1))
    config = {**DEFAULT_SYSTEM_AUTH_CONFIG.get(auth_type, {}), **(setting.config or {})}
    return {
        'id': auth_type,
        'auth_type': auth_type,
        'name': setting.name,
        'config': config,
        'is_active': setting.enabled,
    }


def _setting_to_public_dict(setting):
    data = _setting_to_dict(setting)
    config = dict(data.get('config') or {})
    for secret_key in ['password', 'clientSecret', 'privateKey', 'certificate']:
        if secret_key in config:
            config[secret_key] = ''
    data['config'] = config
    return data


def _get_auth_setting(auth_type):
    auth_type = _auth_type(auth_type)
    setting, _ = ChatAuthSetting.objects.get_or_create(
        auth_type=_setting_key(auth_type),
        defaults={
            'name': SYSTEM_AUTH_TYPE_NAMES.get(auth_type, auth_type),
            'enabled': False,
            'config': DEFAULT_SYSTEM_AUTH_CONFIG.get(auth_type, {}),
        },
    )
    return setting


def _get_login_setting():
    setting, _ = ChatAuthSetting.objects.get_or_create(
        auth_type='SYSTEM_LOGIN_SETTING',
        defaults={
            'name': '登录设置',
            'enabled': True,
            'config': DEFAULT_LOGIN_AUTH_SETTING,
        },
    )
    return {**DEFAULT_LOGIN_AUTH_SETTING, **(setting.config or {})}


def _platform_config(platform_key):
    if platform_key == 'wecom':
        return {'corp_id': '', 'agent_id': '', 'app_secret': '', 'callback_url': ''}
    if platform_key == 'dingtalk':
        return {'corp_id': '', 'app_key': '', 'app_secret': '', 'callback_url': ''}
    return {'app_key': '', 'app_secret': '', 'callback_url': ''}


def _get_platform(platform_key):
    if platform_key not in PLATFORM_NAMES:
        platform_key = str(platform_key or '')
    if platform_key not in PLATFORM_NAMES:
        return None
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


def _platform_to_dict(platform):
    return {
        'id': platform.id,
        'auth_type': platform.auth_type,
        'key': platform.auth_type,
        'name': platform.name,
        'is_active': platform.is_active,
        'is_valid': platform.is_valid,
        'config': {**_platform_config(platform.auth_type), **(platform.config or {})},
    }


class LoginAuthSettingView(APIView):
    def get_authenticators(self):
        if self.request and self.request.method == 'GET' and '/login/auth/' in self.request.path:
            return []
        return [TokenAuth()]

    def get(self, request: Request):
        return result.success(_get_login_setting())

    def put(self, request: Request):
        setting, _ = ChatAuthSetting.objects.get_or_create(
            auth_type='SYSTEM_LOGIN_SETTING',
            defaults={'name': '登录设置', 'enabled': True, 'config': DEFAULT_LOGIN_AUTH_SETTING},
        )
        setting.enabled = True
        setting.config = {**DEFAULT_LOGIN_AUTH_SETTING, **(request.data or {})}
        setting.save(update_fields=['enabled', 'config', 'update_time'])
        return result.success(True)


class SystemAuthDetailView(APIView):
    authentication_classes = [TokenAuth]

    def get(self, request: Request, auth_type):
        return result.success(_setting_to_dict(_get_auth_setting(auth_type)))


class LoginAuthDetailView(APIView):
    authentication_classes = []

    def get(self, request: Request, auth_type):
        return result.success(_setting_to_public_dict(_get_auth_setting(auth_type)))


class SystemAuthInfoView(APIView):
    def get_authenticators(self):
        return [TokenAuth()]

    def put(self, request: Request, auth_type):
        setting = _get_auth_setting(auth_type)
        payload = request.data or {}
        setting.enabled = bool(payload.get('is_active'))
        setting.config = payload.get('config') or {}
        setting.save(update_fields=['enabled', 'config', 'update_time'])
        return result.success(_setting_to_dict(setting))


class SystemAuthConnectionView(APIView):
    def get_authenticators(self):
        return [TokenAuth()]

    def post(self, request: Request):
        return result.success(True)


class SystemPlatformSourceView(APIView):
    authentication_classes = [TokenAuth]

    def get(self, request: Request):
        return result.success([_platform_to_dict(_get_platform(key)) for key in PLATFORM_NAMES])

    def post(self, request: Request):
        payload = request.data or {}
        platform = _get_platform(payload.get('key') or payload.get('auth_type'))
        if platform is None:
            return result.success(False)
        platform.is_active = bool(payload.get('isActive', payload.get('is_active', platform.is_active)))
        platform.is_valid = bool(payload.get('isValid', payload.get('is_valid', platform.is_valid)))
        platform.config = payload.get('config') or platform.config or {}
        platform.save(update_fields=['is_active', 'is_valid', 'config'])
        return result.success(_platform_to_dict(platform))

    def put(self, request: Request):
        payload = request.data or {}
        platform = _get_platform(payload.get('key') or payload.get('auth_type'))
        if platform is None:
            return result.success(False)
        return result.success(platform.is_valid)
