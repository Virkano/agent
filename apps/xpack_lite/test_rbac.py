from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from common.exception.app_exception import AppApiException
from xpack_lite.views.rbac import _require_chat_user_manager


class ChatUserManagerGuardTests(SimpleTestCase):
    def test_workspace_alias_requires_workspace_manager(self):
        request = SimpleNamespace(path='/admin/api/workspace/chat_user', user=SimpleNamespace(id='u1'))
        with patch('xpack_lite.views.rbac.is_workspace_manager', return_value=False):
            with self.assertRaises(AppApiException) as ctx:
                _require_chat_user_manager(request)
        self.assertEqual(ctx.exception.code, 403)

    def test_system_alias_accepts_default_workspace_manager(self):
        request = SimpleNamespace(path='/admin/api/system/chat_user', user=SimpleNamespace(id='u1'))
        with patch('xpack_lite.views.rbac.is_admin', return_value=False), patch(
            'xpack_lite.views.rbac.is_workspace_manager', return_value=True
        ):
            _require_chat_user_manager(request)

    def test_system_alias_rejects_unprivileged_user(self):
        request = SimpleNamespace(path='/admin/api/system/group', user=SimpleNamespace(id='u1'))
        with patch('xpack_lite.views.rbac.is_admin', return_value=False), patch(
            'xpack_lite.views.rbac.is_workspace_manager', return_value=False
        ):
            with self.assertRaises(AppApiException) as ctx:
                _require_chat_user_manager(request)
        self.assertEqual(ctx.exception.code, 403)
