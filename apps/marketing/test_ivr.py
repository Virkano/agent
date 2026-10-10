import json
from types import SimpleNamespace

from django.core.cache import cache
from django.test import TestCase
from rest_framework.test import APIClient

from common.exception.app_exception import AppApiException
from marketing.models import IvrEvent, IvrEventType, IvrSession, IvrSessionStatus, IvrTransport
from marketing.serializers.ivr import IvrProtocolSimulatorService, mask_caller_number
from users.models import User


class IvrProtocolSimulatorFixture(TestCase):
    def setUp(self):
        self.workspace_id = "ivr-simulator-test"
        self.user = User.objects.create(
            username="ivr_simulator_user",
            nick_name="IVR模拟管理员",
            password="x",
            role="ADMIN",
        )
        self.service = IvrProtocolSimulatorService(self.workspace_id, self.user)

    def create_session(self, **overrides):
        data = {
            "external_session_id": "IVR-TEST-001",
            "transport": IvrTransport.HTTP,
            "caller_number": "13800138000",
            "caller_label": "北京测试来电",
        }
        data.update(overrides)
        return self.service.create_session(data)


class IvrProtocolSimulatorServiceTests(IvrProtocolSimulatorFixture):
    def tearDown(self):
        for session in IvrSession.objects.filter(workspace_id=self.workspace_id):
            cache.delete(self.service._cache_key(session.id))

    def test_create_session_masks_caller_and_synchronizes_state(self):
        result = self.create_session()

        self.assertTrue(result["created"])
        self.assertEqual(result["session"]["caller_masked"], "138****8000")
        self.assertEqual(result["session"]["status"], IvrSessionStatus.ACTIVE)
        self.assertEqual(result["session"]["redis_state"]["sequence"], 1)
        self.assertEqual(IvrEvent.objects.get().event_type, IvrEventType.SESSION_STARTED)
        self.assertEqual(mask_caller_number("1234567"), "12***67")

    def test_audio_chunk_generates_stt_and_response_instruction(self):
        session_id = self.create_session()["session"]["id"]

        result = self.service.process_audio(
            session_id,
            {
                "request_id": "audio:test:001",
                "chunk_index": 0,
                "duration_ms": 1600,
                "transcript_hint": "请帮我查询当前变更操作进度",
                "is_final": True,
            },
        )

        self.assertTrue(result["created"])
        self.assertEqual(result["instruction"]["command"], "PLAY_TEXT")
        self.assertEqual(
            [row["event_type"] for row in result["events"]],
            [
                IvrEventType.AUDIO_CHUNK_RECEIVED,
                IvrEventType.STT_COMPLETED,
                IvrEventType.RESPONSE_CREATED,
            ],
        )
        self.assertEqual(IvrSession.objects.get(id=session_id).current_sequence, 4)

    def test_audio_request_is_idempotent_and_transfer_intent_is_detected(self):
        session_id = self.create_session()["session"]["id"]
        payload = {
            "request_id": "audio:test:transfer",
            "chunk_index": 1,
            "transcript_hint": "我要转人工客服",
        }

        first = self.service.process_audio(session_id, payload)
        second = self.service.process_audio(session_id, payload)

        self.assertEqual(first["instruction"]["command"], "TRANSFER_TO_AGENT")
        self.assertFalse(second["created"])
        self.assertEqual(IvrEvent.objects.filter(session_id=session_id).count(), 4)

    def test_state_events_follow_transition_and_terminal_rules(self):
        session_id = self.create_session(transport=IvrTransport.WEBSOCKET_REPLAY)["session"]["id"]
        broadcasting = self.service.record_event(
            session_id,
            {"request_id": "event:test:start", "event_type": IvrEventType.BROADCAST_STARTED},
        )
        ended = self.service.record_event(
            session_id,
            {"request_id": "event:test:end", "event_type": IvrEventType.SESSION_ENDED},
        )

        self.assertEqual(broadcasting["session"]["status"], IvrSessionStatus.BROADCASTING)
        self.assertEqual(ended["session"]["status"], IvrSessionStatus.ENDED)
        with self.assertRaisesMessage(AppApiException, "已结束的 IVR 会话不能继续写入状态事件"):
            self.service.record_event(
                session_id,
                {"request_id": "event:test:late", "event_type": IvrEventType.BROADCAST_ENDED},
            )


class IvrProtocolSimulatorApiTests(IvrProtocolSimulatorFixture):
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

    def tearDown(self):
        for session in IvrSession.objects.filter(workspace_id=self.workspace_id):
            cache.delete(self.service._cache_key(session.id))

    def test_http_protocol_full_chain(self):
        prefix = f"/admin/api/workspace/{self.workspace_id}/marketing/ivr"
        created_response = self.client.post(
            f"{prefix}/session",
            {
                "external_session_id": "IVR-API-001",
                "transport": IvrTransport.WEBSOCKET_REPLAY,
                "caller_number": "13900139000",
            },
            format="json",
        )
        created = json.loads(created_response.content)["data"]
        session_id = created["session"]["id"]
        audio_response = self.client.post(
            f"{prefix}/session/{session_id}/audio",
            {
                "request_id": "api:audio:001",
                "chunk_index": 0,
                "transcript_hint": "变更操作已经开始",
            },
            format="json",
        )
        event_response = self.client.post(
            f"{prefix}/session/{session_id}/event",
            {"request_id": "api:event:001", "event_type": IvrEventType.BROADCAST_STARTED},
            format="json",
        )
        detail_response = self.client.get(f"{prefix}/session/{session_id}")
        dashboard_response = self.client.get(f"{prefix}/dashboard")
        protocol_response = self.client.get(f"{prefix}/protocol")

        self.assertEqual(created_response.status_code, 200)
        self.assertEqual(audio_response.status_code, 200)
        self.assertEqual(event_response.status_code, 200)
        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(dashboard_response.status_code, 200)
        self.assertEqual(protocol_response.status_code, 200)
        detail = json.loads(detail_response.content)["data"]
        dashboard = json.loads(dashboard_response.content)["data"]
        protocol = json.loads(protocol_response.content)["data"]
        self.assertEqual(detail["status"], IvrSessionStatus.BROADCASTING)
        self.assertEqual(len(detail["events"]), 5)
        self.assertEqual(dashboard["summary"]["websocket_replay_count"], 1)
        self.assertEqual(protocol["websocket"]["status"], "CONTRACT_REPLAY")
