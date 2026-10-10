from types import SimpleNamespace

from django.test import TestCase
from rest_framework.test import APIClient

from application.models import Application
from common.constants.permission_constants import PermissionConstants
from system_manage.models import UserGroup
from users.models import User


class ApplicationResourcePermissionTests(TestCase):
    workspace_id = 'resource-permission-ws'

    def setUp(self):
        self.user = User.objects.create(
            username='application-resource-reviewer',
            nick_name='application-resource-reviewer',
            password='x',
            role='USER',
        )
        self.application = Application.objects.create(
            workspace_id=self.workspace_id,
            name='资源权限测试智能体',
        )
        UserGroup.objects.create(id='resource-permission-group', name='资源权限测试用户组')
        self.client = APIClient()

    def authenticate(self, *permissions, roles=()):
        self.client.force_authenticate(
            user=self.user,
            token=SimpleNamespace(
                role_list=list(roles),
                permission_list=list(permissions),
            ),
        )

    def application_permission(self, permission):
        return f'{permission.value}:/WORKSPACE/{self.workspace_id}/APPLICATION/{self.application.id}'

    def assert_app_code(self, response, expected_code):
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['code'], expected_code)

    def test_application_setting_uses_resource_read_and_edit_permissions(self):
        url = f'/admin/api/workspace/{self.workspace_id}/application/{self.application.id}/setting'
        read_permission = self.application_permission(PermissionConstants.APPLICATION_READ)
        edit_permission = self.application_permission(PermissionConstants.APPLICATION_EDIT)

        self.authenticate(read_permission)
        self.assert_app_code(self.client.get(url), 200)
        self.assert_app_code(self.client.put(url, {'show_history': False}, format='json'), 403)

        self.authenticate(read_permission, edit_permission)
        response = self.client.put(url, {'show_history': False}, format='json')
        self.assert_app_code(response, 200)

    def test_chat_user_page_uses_resource_read_and_edit_permissions(self):
        base_url = (
            f'/admin/api/workspace/{self.workspace_id}/APPLICATION/'
            f'{self.application.id}/user_group'
        )
        read_permission = self.application_permission(PermissionConstants.APPLICATION_CHAT_USER_READ)
        edit_permission = self.application_permission(PermissionConstants.APPLICATION_CHAT_USER_EDIT)

        self.authenticate(read_permission)
        self.assert_app_code(self.client.get(base_url), 200)
        self.assert_app_code(self.client.put(base_url, [], format='json'), 403)

        self.authenticate(read_permission, edit_permission)
        self.assert_app_code(self.client.put(base_url, [], format='json'), 200)

    def test_application_access_platform_uses_access_permissions(self):
        status_url = (
            f'/admin/api/workspace/{self.workspace_id}/application/'
            f'{self.application.id}/platform/status'
        )
        config_url = (
            f'/admin/api/workspace/{self.workspace_id}/application/'
            f'{self.application.id}/platform/wechat'
        )
        read_permission = self.application_permission(PermissionConstants.APPLICATION_ACCESS_READ)
        edit_permission = self.application_permission(PermissionConstants.APPLICATION_ACCESS_EDIT)

        self.authenticate(read_permission)
        self.assert_app_code(self.client.get(status_url), 200)
        self.assert_app_code(self.client.get(config_url), 200)
        self.assert_app_code(
            self.client.post(status_url, {'type': 'wechat', 'status': False}, format='json'),
            403,
        )
        self.assert_app_code(self.client.post(config_url, {}, format='json'), 403)

        self.authenticate(read_permission, edit_permission)
        self.assert_app_code(
            self.client.post(status_url, {'type': 'wechat', 'status': False}, format='json'),
            200,
        )
        self.assert_app_code(self.client.post(config_url, {}, format='json'), 200)

    def test_workspace_manager_remains_compatible(self):
        role = f'WORKSPACE_MANAGE:/WORKSPACE/{self.workspace_id}'
        setting_url = f'/admin/api/workspace/{self.workspace_id}/application/{self.application.id}/setting'
        chat_user_url = (
            f'/admin/api/workspace/{self.workspace_id}/APPLICATION/'
            f'{self.application.id}/user_group'
        )

        self.authenticate(roles=(role,))
        self.assert_app_code(self.client.get(setting_url), 200)
        self.assert_app_code(self.client.put(setting_url, {'show_history': True}, format='json'), 200)
        self.assert_app_code(self.client.get(chat_user_url), 200)
        self.assert_app_code(self.client.put(chat_user_url, [], format='json'), 200)

    def test_resource_permission_does_not_cross_workspace(self):
        read_permission = self.application_permission(PermissionConstants.APPLICATION_READ)
        self.authenticate(read_permission)
        url = f'/admin/api/workspace/another-workspace/application/{self.application.id}/setting'
        self.assert_app_code(self.client.get(url), 404)
