import json
from types import SimpleNamespace

from django.test import TestCase
from rest_framework.test import APIClient

from users.models import User

from .api_orchestration import ApiOrchestrationService
from .models import (
    ApiCircuitState,
    ApiGovernanceEvent,
    ApiInvocationAudit,
    ApiInvocationStatus,
    ApiVersionStatus,
)


class ApiOrchestrationFixture(TestCase):
    def setUp(self):
        self.workspace_id = "api-orchestration-test"
        self.user = User.objects.create(
            username="api_orchestration_admin",
            nick_name="接口编排管理员",
            password="x",
            role="WORKSPACE_MANAGE",
        )
        self.service = ApiOrchestrationService(self.workspace_id, self.user)

    @staticmethod
    def asset_payload(mock_name="5G 畅享套餐"):
        return {
            "asset_key": "recommend_customer_product",
            "name": "客户产品推荐",
            "description": "晓搭 Mock 推荐接口",
            "auth_scheme": "API_KEY",
            "auth_reference": "system-api-key:test-reference",
            "ip_allowlist": ["127.0.0.1"],
            "environment": "TEST",
            "method": "POST",
            "endpoint_path": "/xiaoda/v1/recommend",
            "input_schema": {
                "type": "object",
                "required": ["customer_id"],
                "additionalProperties": False,
                "properties": {"customer_id": {"type": "string"}},
            },
            "output_schema": {
                "type": "object",
                "required": ["recommendations"],
                "properties": {"recommendations": {"type": "array"}},
            },
            "request_mapping": {"customerId": "customer_id"},
            "response_mapping": {"items": "recommendations"},
            "mock_response": {"recommendations": [{"name": mock_name}]},
        }


class ApiOrchestrationServiceTests(ApiOrchestrationFixture):
    def test_register_publish_mock_failures_and_audit(self):
        created = self.service.save_asset(self.asset_payload())
        asset_id = created["id"]
        self.service.publish(asset_id, created["draft_version"]["id"])

        success = self.service.mock_invoke(
            asset_id,
            {
                "request_id": "REQ-SUCCESS",
                "payload": {"customer_id": "C-001"},
                "auth_context": {"validated": True, "scheme": "API_KEY"},
            },
        )
        auth_failed = self.service.mock_invoke(
            asset_id,
            {
                "request_id": "REQ-AUTH-FAILED",
                "payload": {"customer_id": "C-002"},
                "auth_context": {"validated": False},
            },
        )
        schema_failed = self.service.mock_invoke(
            asset_id,
            {
                "request_id": "REQ-SCHEMA-FAILED",
                "payload": {},
                "auth_context": {"validated": True, "scheme": "API_KEY"},
            },
        )

        self.assertEqual(success["status"], ApiInvocationStatus.SUCCESS)
        self.assertEqual(auth_failed["status"], ApiInvocationStatus.AUTH_FAILED)
        self.assertEqual(schema_failed["status"], ApiInvocationStatus.SCHEMA_FAILED)
        self.assertNotIn("auth_context", success["request_snapshot"])
        self.assertEqual(ApiInvocationAudit.objects.filter(workspace_id=self.workspace_id).count(), 3)

    def test_new_version_and_rollback_keep_immutable_history(self):
        first = self.service.save_asset(self.asset_payload("V1 套餐"))
        asset_id = first["id"]
        self.service.publish(asset_id, first["draft_version"]["id"])
        second = self.service.save_asset(self.asset_payload("V2 套餐"), asset_id)
        self.service.publish(asset_id, second["draft_version"]["id"])

        rolled_back = self.service.rollback(asset_id, first["draft_version"]["id"])
        versions = rolled_back["versions"]

        self.assertEqual(rolled_back["published_version_no"], 3)
        self.assertEqual(versions[0]["version_no"], 3)
        self.assertEqual(versions[0]["mock_response"]["recommendations"][0]["name"], "V1 套餐")
        self.assertEqual(sum(item["status"] == ApiVersionStatus.PUBLISHED for item in versions), 1)

    def test_parameter_sources_dependencies_and_sensitive_context_are_controlled(self):
        payload = self.asset_payload()
        payload["input_schema"] = {
            "type": "object",
            "required": ["customer_id", "tenant_id", "channel"],
            "additionalProperties": False,
            "properties": {
                "customer_id": {"type": "string"},
                "tenant_id": {"type": "string"},
                "channel": {"type": "string"},
            },
        }
        payload["parameter_bindings"] = [
            {
                "target": "customer_id",
                "source_type": "REQUEST",
                "source_path": "customer.id",
                "required": True,
                "depends_on": [],
            },
            {
                "target": "tenant_id",
                "source_type": "CONTEXT",
                "source_path": "tenant.id",
                "required": True,
                "depends_on": ["customer_id"],
            },
            {
                "target": "channel",
                "source_type": "CONSTANT",
                "source_value": "assistant",
                "required": True,
                "depends_on": ["tenant_id"],
            },
        ]
        created = self.service.save_asset(payload)
        self.service.publish(created["id"], created["draft_version"]["id"])

        audit = self.service.mock_invoke(
            created["id"],
            {
                "request_id": "REQ-BINDINGS",
                "payload": {"customer": {"id": "C-100"}},
                "source_context": {"tenant": {"id": "T-01"}, "secret": "never-store"},
                "auth_context": {"validated": True, "scheme": "API_KEY"},
            },
        )

        self.assertEqual(audit["status"], ApiInvocationStatus.SUCCESS)
        self.assertEqual(
            audit["request_snapshot"]["params"],
            {"customer_id": "C-100", "tenant_id": "T-01", "channel": "assistant"},
        )
        self.assertNotIn("source_context", audit["request_snapshot"])
        self.assertNotIn("never-store", json.dumps(audit["request_snapshot"]))

    def test_parameter_dependency_cycle_is_rejected(self):
        payload = self.asset_payload()
        payload["parameter_bindings"] = [
            {
                "target": "customer_id",
                "source_type": "REQUEST",
                "source_path": "customer_id",
                "depends_on": ["customer_id"],
            }
        ]
        with self.assertRaises(Exception) as context:
            self.service.save_asset(payload)
        self.assertIn("不得依赖自身", str(context.exception))

    def test_environment_gates_production_auth_and_enable_switch(self):
        production_first = self.asset_payload()
        production_first["environment"] = "PRODUCTION"
        production_first["openapi_snapshot"] = {"openapi": "3.0.3", "paths": {}}
        blocked = self.service.save_asset(production_first)
        with self.assertRaises(Exception) as context:
            self.service.publish(blocked["id"], blocked["draft_version"]["id"])
        self.assertIn("灰度版本", str(context.exception))

        test_payload = self.asset_payload()
        test_payload["asset_key"] = "governed_recommendation"
        test_version = self.service.save_asset(test_payload)
        asset_id = test_version["id"]
        self.service.publish(asset_id, test_version["draft_version"]["id"])
        gray_payload = {**test_payload, "environment": "GRAY"}
        gray_version = self.service.save_asset(gray_payload, asset_id)
        self.service.publish(asset_id, gray_version["draft_version"]["id"])
        production_payload = {
            **test_payload,
            "environment": "PRODUCTION",
            "openapi_snapshot": {"openapi": "3.0.3", "paths": {}},
        }
        production_version = self.service.save_asset(production_payload, asset_id)
        published = self.service.publish(
            asset_id,
            production_version["draft_version"]["id"],
        )
        self.assertEqual(published["published_version_no"], 3)

        rejected = self.service.mock_invoke(
            asset_id,
            {
                "request_id": "REQ-PROD-AUTH-REJECTED",
                "payload": {"customer_id": "C-01"},
                "auth_context": {"validated": True, "scheme": "API_KEY"},
            },
        )
        accepted = self.service.mock_invoke(
            asset_id,
            {
                "request_id": "REQ-PROD-AUTH-ACCEPTED",
                "payload": {"customer_id": "C-01"},
                "auth_context": {
                    "validated": True,
                    "scheme": "API_KEY",
                    "source_ip": "127.0.0.1",
                    "credential_reference": "system-api-key:test-reference",
                },
            },
        )
        self.assertEqual(rejected["status"], ApiInvocationStatus.AUTH_FAILED)
        self.assertEqual(accepted["status"], ApiInvocationStatus.SUCCESS)
        disabled = self.service.set_enabled(asset_id, {"enabled": False, "reason": "验收停用"})
        self.assertFalse(disabled["enabled"])
        self.assertTrue(
            ApiGovernanceEvent.objects.filter(
                workspace_id=self.workspace_id,
                asset_id=asset_id,
                event_type="ASSET_DISABLED",
            ).exists()
        )

    def test_retry_exhaustion_opens_circuit_and_rejects_next_call(self):
        payload = self.asset_payload()
        payload.update(
            {
                "max_retries": 1,
                "circuit_failure_threshold": 2,
                "circuit_recovery_seconds": 60,
            }
        )
        created = self.service.save_asset(payload)
        asset_id = created["id"]
        self.service.publish(asset_id, created["draft_version"]["id"])
        auth = {"validated": True, "scheme": "API_KEY"}
        first = self.service.mock_invoke(
            asset_id,
            {
                "request_id": "REQ-RETRY-1",
                "payload": {"customer_id": "C-01"},
                "auth_context": auth,
                "simulated_failures": 2,
            },
        )
        second = self.service.mock_invoke(
            asset_id,
            {
                "request_id": "REQ-RETRY-2",
                "payload": {"customer_id": "C-01"},
                "auth_context": auth,
                "simulated_failures": 2,
            },
        )
        rejected = self.service.mock_invoke(
            asset_id,
            {
                "request_id": "REQ-CIRCUIT-OPEN",
                "payload": {"customer_id": "C-01"},
                "auth_context": auth,
            },
        )
        self.assertEqual(first["status"], ApiInvocationStatus.RETRY_EXHAUSTED)
        self.assertEqual(second["status"], ApiInvocationStatus.RETRY_EXHAUSTED)
        self.assertEqual(rejected["status"], ApiInvocationStatus.CIRCUIT_OPEN)
        self.assertEqual(
            self.service._asset(asset_id).circuit_state,
            ApiCircuitState.OPEN,
        )


class ApiOrchestrationApiTests(ApiOrchestrationFixture):
    def setUp(self):
        super().setUp()
        self.client = APIClient()
        self.client.force_authenticate(
            user=self.user,
            token=SimpleNamespace(
                role_list=[f"WORKSPACE_MANAGE:/WORKSPACE/{self.workspace_id}"],
                permission_list=[],
            ),
        )

    def test_bootstrap_and_dashboard_api(self):
        bootstrap = self.client.post(
            f"/admin/api/workspace/{self.workspace_id}/api-orchestration/bootstrap",
            data={},
            format="json",
        )
        dashboard = self.client.get(
            f"/admin/api/workspace/{self.workspace_id}/api-orchestration/dashboard"
        )
        bootstrap_data = json.loads(bootstrap.content)["data"]
        dashboard_data = json.loads(dashboard.content)["data"]

        self.assertEqual(bootstrap.status_code, 200)
        self.assertEqual(bootstrap_data["summary"]["asset_count"], 1)
        self.assertEqual(bootstrap_data["summary"]["success_count"], 1)
        self.assertEqual(bootstrap_data["summary"]["failure_count"], 2)
        self.assertEqual(dashboard_data["assets"][0]["published_version_no"], 1)

    def test_openapi_import_and_breaking_version_compare_api(self):
        document = {
            "openapi": "3.0.3",
            "info": {"title": "Customer API", "version": "1.2.0"},
            "paths": {
                "/customers/{customer_id}/recommendations": {
                    "post": {
                        "operationId": "recommendCustomerProduct",
                        "parameters": [
                            {
                                "name": "customer_id",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "string"},
                            }
                        ],
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/RecommendRequest"}
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "content": {
                                    "application/json": {
                                        "schema": {"$ref": "#/components/schemas/RecommendResponse"}
                                    }
                                }
                            }
                        },
                    }
                }
            },
            "components": {
                "schemas": {
                    "RecommendRequest": {
                        "type": "object",
                        "required": ["channel"],
                        "properties": {"channel": {"type": "string"}},
                    },
                    "RecommendResponse": {
                        "type": "object",
                        "required": ["items"],
                        "properties": {"items": {"type": "array"}},
                    },
                }
            },
        }
        imported = self.client.post(
            f"/admin/api/workspace/{self.workspace_id}/api-orchestration/openapi/import",
            data={"document": document},
            format="json",
        )
        imported_data = json.loads(imported.content)["data"]
        self.assertEqual(imported.status_code, 200)
        self.assertEqual(imported_data["method"], "POST")
        self.assertEqual(
            imported_data["input_schema"]["required"], ["customer_id", "channel"]
        )
        self.assertEqual(len(imported_data["parameter_bindings"]), 2)

        first = self.service.save_asset(self.asset_payload())
        changed = self.asset_payload()
        changed["input_schema"]["properties"]["channel"] = {"type": "string"}
        changed["input_schema"]["required"].append("channel")
        changed["output_schema"]["properties"] = {"items": {"type": "array"}}
        changed["output_schema"]["required"] = ["items"]
        second = self.service.save_asset(changed, first["id"])
        comparison = self.client.get(
            f"/admin/api/workspace/{self.workspace_id}/api-orchestration/asset/"
            f"{first['id']}/version/{first['draft_version']['id']}/compare",
            {"target_version_id": second["draft_version"]["id"]},
        )
        comparison_data = json.loads(comparison.content)["data"]
        self.assertEqual(comparison.status_code, 200)
        self.assertFalse(comparison_data["compatible"])
        self.assertIn("channel", comparison_data["input_schema_diff"]["required_added"])
        self.assertIn("recommendations", comparison_data["output_schema_diff"]["removed"])
