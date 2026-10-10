import hashlib
import json
from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase
from rest_framework.exceptions import PermissionDenied
from rest_framework.test import APIClient

from common.log.log import log
from common.log.master_data import master_data_read_audit
from system_manage.models import Log, MasterDataAccessEvent


class MasterDataAuditTests(TestCase):
    @staticmethod
    def request():
        return SimpleNamespace(
            user=SimpleNamespace(
                id="actor-1", email="person@example.invalid", phone="13800000000",
                nick_name="Person", username="person", role="ADMIN",
            ),
            query_params={"phone": "13800000000", "api_key": "sensitive-query-value"},
            data={"password": "sensitive-body-value", "nested": {"token": "sensitive-token"}},
            resolver_match=SimpleNamespace(route="admin/api/workspace/<str:workspace_id>/customer"),
            META={"REMOTE_ADDR": "127.0.0.1"},
        )

    def test_successful_master_read_persists_value_free_fact(self):
        request = self.request()
        audited = master_data_read_audit("marketing.MarketingCustomer")(
            lambda view, req, **kwargs: {"ok": True}
        )
        self.assertEqual(audited(object(), request, workspace_id="demo", task_id="task-1"), {"ok": True})
        event = MasterDataAccessEvent.objects.get()
        self.assertEqual(event.resource_model, "marketing.MarketingCustomer")
        self.assertEqual(event.outcome, "SUCCESS")
        self.assertEqual(event.workspace_id, "demo")
        self.assertEqual(event.scope_hash, hashlib.sha256(b"task-1").hexdigest())
        self.assertEqual(event.query_keys, ["api_key", "phone"])
        persisted = {field.name: getattr(event, field.name) for field in event._meta.concrete_fields}
        self.assertNotIn("13800000000", json.dumps(persisted, default=str))

    def test_denied_master_read_is_recorded_without_returning_data(self):
        def reject(view, request, **kwargs):
            raise PermissionDenied()

        audited = master_data_read_audit("users.User")(reject)
        with self.assertRaises(PermissionDenied):
            audited(object(), self.request(), user_id="target-user")
        event = MasterDataAccessEvent.objects.get()
        self.assertEqual(event.outcome, "DENIED")
        self.assertEqual(event.action, "DETAIL")
        self.assertEqual(event.scope_hash, hashlib.sha256(b"target-user").hexdigest())

    def test_generic_operation_log_never_persists_body_query_or_contact_values(self):
        request = self.request()

        @log(menu="test", operate="read", get_operation_object=lambda req, kwargs: {"email": "person@example.invalid"})
        def handler(view, req):
            return "ok"

        self.assertEqual(handler(object(), request), "ok")
        entry = Log.objects.get()
        self.assertEqual(entry.details["body_fields"], ["nested", "password"])
        self.assertEqual(entry.details["query_fields"], ["api_key", "phone"])
        self.assertEqual(entry.operation_object, {"field_names": ["email"]})
        self.assertEqual(entry.menu, "测试")
        self.assertEqual(entry.operate, "读取")
        serialized = json.dumps({"user": entry.user, "details": entry.details, "object": entry.operation_object})
        for secret in ("sensitive-body-value", "sensitive-query-value", "sensitive-token", "13800000000", "person@example.invalid"):
            self.assertNotIn(secret, serialized)

    def test_customer_and_user_read_routes_create_access_events(self):
        client = APIClient()
        client.force_authenticate(
            user=self.request().user,
            token=SimpleNamespace(role_list=["ADMIN"], permission_list=[]),
        )
        with patch("marketing.views.task.MarketingCustomerService.list", return_value=[]):
            response = client.get(
                "/admin/api/workspace/demo/marketing/task/task-1/customer",
                {"phone": "13800000000"},
            )
        self.assertEqual(response.status_code, 200)
        with patch("users.views.user.UserProfileSerializer.profile", return_value={}):
            response = client.get("/admin/api/user/profile")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            set(MasterDataAccessEvent.objects.values_list("resource_model", flat=True)),
            {"marketing.MarketingCustomer", "users.User"},
        )
