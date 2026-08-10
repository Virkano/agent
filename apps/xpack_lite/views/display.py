from rest_framework.request import Request
from rest_framework.views import APIView

from common.result import result
from xpack_lite.models import PlatformDisplaySetting
from xpack_lite.services import DEFAULT_DISPLAY_SETTING


def _normalize_display_value(value):
    if hasattr(value, 'name') and hasattr(value, 'size'):
        return ''
    if value in ['true', 'True']:
        return True
    if value in ['false', 'False']:
        return False
    return value


class PlatformDisplaySettingView(APIView):
    def get_authenticators(self):
        if self.request and self.request.method == 'GET':
            return []
        from common.auth.authenticate import TokenAuth
        return [TokenAuth()]

    def get(self, request: Request):
        setting, _ = PlatformDisplaySetting.objects.get_or_create(
            id='default',
            defaults={'meta': DEFAULT_DISPLAY_SETTING},
        )
        return result.success({**DEFAULT_DISPLAY_SETTING, **(setting.meta or {})})

    def put(self, request: Request):
        setting, _ = PlatformDisplaySetting.objects.get_or_create(
            id='default',
            defaults={'meta': DEFAULT_DISPLAY_SETTING},
        )
        incoming = {
            key: _normalize_display_value(value)
            for key, value in request.data.items()
            if key in DEFAULT_DISPLAY_SETTING
        }
        setting.meta = {**DEFAULT_DISPLAY_SETTING, **(setting.meta or {}), **incoming}
        setting.save(update_fields=['meta'])
        return result.success(True)
