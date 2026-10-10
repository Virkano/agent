# coding=utf-8
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from common.exception.app_exception import AppApiException
from common.utils.logger import telecom_ai_logger
from marketing.models import (
    IvrEvent,
    IvrEventDirection,
    IvrEventType,
    IvrSession,
    IvrSessionStatus,
    IvrTransport,
)


IVR_TERMINAL_STATUSES = {IvrSessionStatus.ENDED, IvrSessionStatus.FAILED}
IVR_EXTERNAL_EVENT_TYPES = (
    IvrEventType.BROADCAST_STARTED,
    IvrEventType.BROADCAST_ENDED,
    IvrEventType.TRANSFERRED,
    IvrEventType.SESSION_ENDED,
    IvrEventType.FAILED,
)
IVR_STATUS_BY_EVENT = {
    IvrEventType.BROADCAST_STARTED: IvrSessionStatus.BROADCASTING,
    IvrEventType.BROADCAST_ENDED: IvrSessionStatus.ACTIVE,
    IvrEventType.TRANSFERRED: IvrSessionStatus.TRANSFERRED,
    IvrEventType.SESSION_ENDED: IvrSessionStatus.ENDED,
    IvrEventType.FAILED: IvrSessionStatus.FAILED,
}


class IvrSessionCreateSerializer(serializers.Serializer):
    external_session_id = serializers.CharField(required=False, allow_blank=True, max_length=128)
    transport = serializers.ChoiceField(choices=IvrTransport.choices, default=IvrTransport.HTTP)
    caller_number = serializers.CharField(required=False, allow_blank=True, max_length=64, write_only=True)
    caller_label = serializers.CharField(required=False, allow_blank=True, max_length=128)
    language = serializers.CharField(required=False, default="zh-CN", max_length=16)
    metadata = serializers.DictField(required=False, default=dict)


class IvrAudioChunkSerializer(serializers.Serializer):
    request_id = serializers.CharField(max_length=160)
    chunk_index = serializers.IntegerField(min_value=0)
    audio_reference = serializers.CharField(required=False, allow_blank=True, max_length=256)
    duration_ms = serializers.IntegerField(required=False, min_value=0, max_value=600000, default=0)
    transcript_hint = serializers.CharField(required=False, allow_blank=True, max_length=4000)
    is_final = serializers.BooleanField(required=False, default=False)
    occurred_at = serializers.DateTimeField(required=False, default=timezone.now)


class IvrExternalEventSerializer(serializers.Serializer):
    request_id = serializers.CharField(max_length=160)
    event_type = serializers.ChoiceField(
        choices=[(value, label) for value, label in IvrEventType.choices if value in IVR_EXTERNAL_EVENT_TYPES]
    )
    payload = serializers.DictField(required=False, default=dict)
    occurred_at = serializers.DateTimeField(required=False, default=timezone.now)


def mask_caller_number(value):
    normalized = "".join(character for character in str(value or "") if character.isdigit())
    if not normalized:
        return ""
    if len(normalized) <= 7:
        return f"{normalized[:2]}***{normalized[-2:]}"
    return f"{normalized[:3]}****{normalized[-4:]}"


def serialize_ivr_event(row):
    return {
        "id": str(row.id),
        "sequence": row.sequence,
        "event_type": row.event_type,
        "event_type_label": row.get_event_type_display(),
        "direction": row.direction,
        "direction_label": row.get_direction_display(),
        "request_id": row.request_id,
        "payload": row.payload or {},
        "occurred_at": row.occurred_at,
        "create_time": row.create_time,
    }


def serialize_ivr_session(row, *, include_events=False, redis_state=None):
    data = {
        "id": str(row.id),
        "external_session_id": row.external_session_id,
        "transport": row.transport,
        "transport_label": row.get_transport_display(),
        "caller_masked": row.caller_masked,
        "caller_label": row.caller_label,
        "language": row.language,
        "status": row.status,
        "status_label": row.get_status_display(),
        "current_sequence": row.current_sequence,
        "latest_transcript": row.latest_transcript,
        "latest_response": row.latest_response,
        "metadata": row.metadata or {},
        "started_at": row.started_at,
        "ended_at": row.ended_at,
        "create_time": row.create_time,
        "update_time": row.update_time,
        "redis_state": redis_state,
    }
    if include_events:
        data["events"] = [serialize_ivr_event(event) for event in row.events.all()]
    return data


class IvrProtocolSimulatorService:
    CACHE_TIMEOUT_SECONDS = 2 * 60 * 60

    def __init__(self, workspace_id, user=None):
        self.workspace_id = workspace_id
        self.user = user

    def _session_queryset(self):
        return IvrSession.objects.filter(workspace_id=self.workspace_id).select_related("user")

    def _get_session(self, session_id, *, lock=False):
        queryset = IvrSession.objects.filter(workspace_id=self.workspace_id)
        if lock:
            queryset = queryset.select_for_update()
        session = queryset.filter(id=session_id).first()
        if session is None:
            raise AppApiException(404, "IVR 会话不存在")
        return session

    def _cache_key(self, session_id):
        return f"marketing:ivr:{self.workspace_id}:{session_id}"

    def _state_payload(self, session):
        return {
            "session_id": str(session.id),
            "external_session_id": session.external_session_id,
            "status": session.status,
            "sequence": session.current_sequence,
            "latest_transcript": session.latest_transcript,
            "latest_response": session.latest_response,
            "updated_at": timezone.now().isoformat(),
        }

    def _sync_cache(self, session):
        try:
            cache.set(
                self._cache_key(session.id),
                self._state_payload(session),
                timeout=self.CACHE_TIMEOUT_SECONDS,
            )
            return True
        except Exception as exc:
            telecom_ai_logger.warning("IVR session cache update failed for %s: %s", session.id, exc)
            return False

    def _read_cache(self, session):
        try:
            return cache.get(self._cache_key(session.id))
        except Exception as exc:
            telecom_ai_logger.warning("IVR session cache read failed for %s: %s", session.id, exc)
            return None

    def _create_event(self, session, event_type, direction, payload, occurred_at, request_id=""):
        session.current_sequence += 1
        event = IvrEvent.objects.create(
            workspace_id=self.workspace_id,
            session=session,
            sequence=session.current_sequence,
            event_type=event_type,
            direction=direction,
            request_id=request_id,
            payload=payload,
            occurred_at=occurred_at,
            user=self.user,
        )
        return event

    def protocol(self):
        return {
            "version": "ivr-simulator-v1",
            "mode": "LOCAL_PROTOCOL_REPLAY",
            "external_integration_status": "PENDING",
            "http": {
                "create_session": "POST /marketing/ivr/session",
                "audio_chunk": "POST /marketing/ivr/session/{session_id}/audio",
                "state_event": "POST /marketing/ivr/session/{session_id}/event",
            },
            "websocket": {
                "status": "CONTRACT_REPLAY",
                "future_endpoint": "/ws/workspace/{workspace_id}/marketing/ivr/{session_id}",
                "note": "当前通过相同 JSON 消息契约进行回放；生产长连接待 IVR 网关联调。",
            },
            "message_types": [{"type": value, "label": label} for value, label in IvrEventType.choices],
            "response_commands": ["PLAY_TEXT", "TRANSFER_TO_AGENT", "END_SESSION"],
        }

    @transaction.atomic
    def create_session(self, data):
        serializer = IvrSessionCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        external_session_id = values.get("external_session_id") or f"SIM-{timezone.now():%Y%m%d%H%M%S%f}"
        existing = self._session_queryset().filter(external_session_id=external_session_id).first()
        if existing:
            return {
                "created": False,
                "session": serialize_ivr_session(existing, redis_state=self._read_cache(existing)),
                "protocol": self.protocol(),
            }
        now = timezone.now()
        session = IvrSession.objects.create(
            workspace_id=self.workspace_id,
            external_session_id=external_session_id,
            transport=values["transport"],
            caller_masked=mask_caller_number(values.get("caller_number")),
            caller_label=values.get("caller_label", ""),
            language=values["language"],
            status=IvrSessionStatus.ACTIVE,
            metadata=values.get("metadata", {}),
            started_at=now,
            user=self.user,
        )
        self._create_event(
            session,
            IvrEventType.SESSION_STARTED,
            IvrEventDirection.SYSTEM,
            {"transport": session.transport, "language": session.language},
            now,
        )
        session.save(update_fields=["current_sequence", "update_time"])
        cache_synced = self._sync_cache(session)
        return {
            "created": True,
            "cache_synced": cache_synced,
            "session": serialize_ivr_session(session, redis_state=self._read_cache(session)),
            "protocol": self.protocol(),
        }

    def _duplicate_response(self, session, existing):
        session = self._get_session(session.id)
        return {
            "created": False,
            "duplicate_event_id": str(existing.id),
            "session": self.get(session.id),
            "instruction": (existing.payload or {}).get("instruction"),
        }

    @staticmethod
    def _build_instruction(transcript, is_final):
        transfer_requested = any(keyword in transcript for keyword in ("转人工", "人工客服", "人工坐席"))
        if transfer_requested:
            return {
                "command": "TRANSFER_TO_AGENT",
                "tts_text": "正在为您转接人工坐席，请稍候。",
                "reason": "识别文本包含转人工意图",
                "final": bool(is_final),
            }
        return {
            "command": "PLAY_TEXT",
            "tts_text": f"已收到：{transcript}。当前为 IVR 协议模拟响应。",
            "reason": "本地协议模拟规则",
            "final": bool(is_final),
        }

    @transaction.atomic
    def process_audio(self, session_id, data):
        serializer = IvrAudioChunkSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        session = self._get_session(session_id, lock=True)
        existing = IvrEvent.objects.filter(
            workspace_id=self.workspace_id,
            request_id=values["request_id"],
        ).first()
        if existing:
            return self._duplicate_response(session, existing)
        if session.status in IVR_TERMINAL_STATUSES:
            raise AppApiException(400, "已结束的 IVR 会话不能继续接收音频")

        occurred_at = values["occurred_at"]
        audio_event = self._create_event(
            session,
            IvrEventType.AUDIO_CHUNK_RECEIVED,
            IvrEventDirection.INBOUND,
            {
                "chunk_index": values["chunk_index"],
                "audio_reference": values.get("audio_reference", ""),
                "duration_ms": values["duration_ms"],
                "is_final": values["is_final"],
            },
            occurred_at,
        )
        transcript = values.get("transcript_hint", "").strip()
        if not transcript:
            transcript = f"[模拟识别] 已接收第 {values['chunk_index']} 个音频分片"
        stt_event = self._create_event(
            session,
            IvrEventType.STT_COMPLETED,
            IvrEventDirection.SYSTEM,
            {"text": transcript, "provider": "LOCAL_PROTOCOL_SIMULATOR", "mode": "SIMULATED"},
            occurred_at,
        )
        instruction = self._build_instruction(transcript, values["is_final"])
        response_event = self._create_event(
            session,
            IvrEventType.RESPONSE_CREATED,
            IvrEventDirection.OUTBOUND,
            {"instruction": instruction},
            occurred_at,
            request_id=values["request_id"],
        )
        session.status = IvrSessionStatus.ACTIVE
        session.latest_transcript = transcript
        session.latest_response = instruction["tts_text"]
        session.save(
            update_fields=[
                "status",
                "current_sequence",
                "latest_transcript",
                "latest_response",
                "update_time",
            ]
        )
        cache_synced = self._sync_cache(session)
        return {
            "created": True,
            "cache_synced": cache_synced,
            "session": serialize_ivr_session(session, redis_state=self._read_cache(session)),
            "events": [serialize_ivr_event(row) for row in (audio_event, stt_event, response_event)],
            "instruction": instruction,
        }

    @transaction.atomic
    def record_event(self, session_id, data):
        serializer = IvrExternalEventSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        session = self._get_session(session_id, lock=True)
        existing = IvrEvent.objects.filter(
            workspace_id=self.workspace_id,
            request_id=values["request_id"],
        ).first()
        if existing:
            return self._duplicate_response(session, existing)
        if session.status in IVR_TERMINAL_STATUSES:
            raise AppApiException(400, "已结束的 IVR 会话不能继续写入状态事件")

        event_type = values["event_type"]
        new_status = IVR_STATUS_BY_EVENT[event_type]
        event = self._create_event(
            session,
            event_type,
            IvrEventDirection.INBOUND,
            values.get("payload", {}),
            values["occurred_at"],
            request_id=values["request_id"],
        )
        session.status = new_status
        if new_status in IVR_TERMINAL_STATUSES:
            session.ended_at = values["occurred_at"]
        session.save(update_fields=["status", "current_sequence", "ended_at", "update_time"])
        cache_synced = self._sync_cache(session)
        return {
            "created": True,
            "cache_synced": cache_synced,
            "session": serialize_ivr_session(session, redis_state=self._read_cache(session)),
            "event": serialize_ivr_event(event),
        }

    def get(self, session_id):
        session = self._session_queryset().prefetch_related("events").filter(id=session_id).first()
        if session is None:
            raise AppApiException(404, "IVR 会话不存在")
        return serialize_ivr_session(
            session,
            include_events=True,
            redis_state=self._read_cache(session),
        )

    def dashboard(self):
        sessions = list(self._session_queryset().order_by("-update_time")[:30])
        status_counts = {value: 0 for value in IvrSessionStatus.values}
        for session in sessions:
            status_counts[session.status] += 1
        active_statuses = {IvrSessionStatus.ACTIVE, IvrSessionStatus.BROADCASTING}
        return {
            "summary": {
                "session_count": self._session_queryset().count(),
                "active_session_count": self._session_queryset().filter(status__in=active_statuses).count(),
                "event_count": IvrEvent.objects.filter(workspace_id=self.workspace_id).count(),
                "websocket_replay_count": self._session_queryset()
                .filter(transport=IvrTransport.WEBSOCKET_REPLAY)
                .count(),
            },
            "status_counts": status_counts,
            "protocol": self.protocol(),
            "sessions": [serialize_ivr_session(session, redis_state=self._read_cache(session)) for session in sessions],
        }
