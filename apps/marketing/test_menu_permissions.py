import json
from types import SimpleNamespace

from django.test import SimpleTestCase, TestCase
from rest_framework.test import APIClient

from common.constants.permission_constants import PermissionConstants, RoleConstants
from users.models import User
from xpack_lite.views.rbac import _role_permission_tree


class WorkspaceMenuPermissionTreeTests(SimpleTestCase):
    def test_new_navigation_items_are_assignable_in_role_permissions(self):
        tree = _role_permission_tree(template_role_type=RoleConstants.USER.name)
        permission_ids = {
            permission["id"]
            for module in tree
            for feature in module["children"]
            for permission in feature["permission"]
        }
        expected = {
            str(PermissionConstants.MARKETING_SCENARIO_READ.value),
            str(PermissionConstants.MARKETING_CAMPAIGN_READ.value),
            str(PermissionConstants.MARKETING_TASK_READ.value),
            str(PermissionConstants.RECOMMENDATION_ENGINE_READ.value),
            str(PermissionConstants.MARKETING_OPERATIONS_READ.value),
            str(PermissionConstants.MARKETING_QUALITY_READ.value),
            str(PermissionConstants.ANALYSIS_REPORT_READ.value),
            str(PermissionConstants.METRIC_OPERATIONS_READ.value),
            str(PermissionConstants.PLATFORM_MONITORING_READ.value),
            str(PermissionConstants.API_ORCHESTRATION_READ.value),
            str(PermissionConstants.EVENT_ORCHESTRATION_READ.value),
            str(PermissionConstants.RESOURCE_COORDINATION_READ.value),
            str(PermissionConstants.IVR_SIMULATOR_READ.value),
            str(PermissionConstants.REHEARSAL_READ.value),
        }
        self.assertTrue(expected.issubset(permission_ids))


class MarketingScenarioMenuPermissionApiTests(TestCase):
    def setUp(self):
        self.workspace_id = "menu-permission-workspace"
        self.user = User.objects.create(
            username="menu_permission_user",
            nick_name="菜单权限用户",
            password="x",
            role="USER",
        )
        self.client = APIClient()
        self.url = f"/admin/api/workspace/{self.workspace_id}/marketing/scenario"

    def authenticate(self, permissions):
        self.client.force_authenticate(
            user=self.user,
            token=SimpleNamespace(role_list=[], permission_list=permissions),
        )

    def test_unassigned_menu_is_rejected(self):
        self.authenticate([])
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_unassigned_menu_rejects_write(self):
        self.authenticate([])
        response = self.client.post(self.url, {"name": "无权限场景"}, format="json")
        self.assertEqual(response.status_code, 403)

    def test_assigned_menu_can_be_opened_only_in_its_workspace(self):
        permission = (
            f"{PermissionConstants.MARKETING_SCENARIO_READ.value}"
            f":/WORKSPACE/{self.workspace_id}"
        )
        self.authenticate([permission])

        allowed = self.client.get(self.url)
        denied = self.client.get("/admin/api/workspace/another-workspace/marketing/scenario")

        self.assertEqual(allowed.status_code, 200)
        self.assertEqual(json.loads(allowed.content)["code"], 200)
        self.assertEqual(denied.status_code, 403)

    def test_page_read_permission_allows_page_write_operations(self):
        permission = (
            f"{PermissionConstants.MARKETING_SCENARIO_READ.value}"
            f":/WORKSPACE/{self.workspace_id}"
        )
        self.authenticate([permission])

        response = self.client.post(self.url, {"name": "一页一权场景"}, format="json")

        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.content)
        self.assertEqual(payload["code"], 200)
        self.assertEqual(payload["data"]["name"], "一页一权场景")
