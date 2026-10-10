# coding=utf-8
import uuid_utils.compat as uuid
from django.db import models

from common.mixins.app_model_mixin import AppModelMixin
from users.models import User


class IvrTransport(models.TextChoices):
    HTTP = "HTTP", "HTTP 回调"
    WEBSOCKET_REPLAY = "WEBSOCKET_REPLAY", "WebSocket 消息回放"


class IvrSessionStatus(models.TextChoices):
    CREATED = "CREATED", "已创建"
    ACTIVE = "ACTIVE", "通话中"
    BROADCASTING = "BROADCASTING", "播报中"
    TRANSFERRED = "TRANSFERRED", "已转人工"
    ENDED = "ENDED", "已结束"
    FAILED = "FAILED", "异常结束"


class IvrEventDirection(models.TextChoices):
    INBOUND = "INBOUND", "平台上行"
    OUTBOUND = "OUTBOUND", "智能体下行"
    SYSTEM = "SYSTEM", "系统事件"


class IvrEventType(models.TextChoices):
    SESSION_STARTED = "SESSION_STARTED", "会话开始"
    AUDIO_CHUNK_RECEIVED = "AUDIO_CHUNK_RECEIVED", "收到音频分片"
    STT_COMPLETED = "STT_COMPLETED", "语音识别完成"
    RESPONSE_CREATED = "RESPONSE_CREATED", "响应指令已生成"
    BROADCAST_STARTED = "BROADCAST_STARTED", "播报开始"
    BROADCAST_ENDED = "BROADCAST_ENDED", "播报结束"
    TRANSFERRED = "TRANSFERRED", "转人工"
    SESSION_ENDED = "SESSION_ENDED", "会话结束"
    FAILED = "FAILED", "处理失败"


class IvrSession(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False, verbose_name="主键id")
    workspace_id = models.CharField(max_length=64, default="default", db_index=True, verbose_name="工作空间id")
    external_session_id = models.CharField(max_length=128, verbose_name="外部会话id")
    transport = models.CharField(max_length=24, choices=IvrTransport.choices, default=IvrTransport.HTTP)
    caller_masked = models.CharField(max_length=64, default="", blank=True, verbose_name="脱敏主叫号码")
    caller_label = models.CharField(max_length=128, default="", blank=True, verbose_name="来电标识")
    language = models.CharField(max_length=16, default="zh-CN", verbose_name="语言")
    status = models.CharField(
        max_length=24,
        choices=IvrSessionStatus.choices,
        default=IvrSessionStatus.CREATED,
        db_index=True,
    )
    current_sequence = models.PositiveIntegerField(default=0, verbose_name="当前事件序号")
    latest_transcript = models.TextField(default="", blank=True, verbose_name="最近识别文本")
    latest_response = models.TextField(default="", blank=True, verbose_name="最近响应文本")
    metadata = models.JSONField(default=dict, blank=True, verbose_name="会话扩展信息")
    started_at = models.DateTimeField(blank=True, null=True, verbose_name="开始时间")
    ended_at = models.DateTimeField(blank=True, null=True, verbose_name="结束时间")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, blank=True, null=True)

    class Meta:
        db_table = "ivr_session"
        ordering = ["-create_time"]
        constraints = [
            models.UniqueConstraint(
                fields=["workspace_id", "external_session_id"],
                name="ivr_session_ws_external",
            )
        ]
        indexes = [models.Index(fields=["workspace_id", "status", "update_time"], name="ivr_session_ws_status")]


class IvrEvent(AppModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False, verbose_name="主键id")
    workspace_id = models.CharField(max_length=64, default="default", db_index=True, verbose_name="工作空间id")
    session = models.ForeignKey(IvrSession, on_delete=models.CASCADE, related_name="events")
    sequence = models.PositiveIntegerField(verbose_name="事件序号")
    event_type = models.CharField(max_length=32, choices=IvrEventType.choices, db_index=True)
    direction = models.CharField(max_length=16, choices=IvrEventDirection.choices, default=IvrEventDirection.SYSTEM)
    request_id = models.CharField(max_length=160, default="", blank=True, db_index=True, verbose_name="请求幂等键")
    payload = models.JSONField(default=dict, blank=True, verbose_name="脱敏事件载荷")
    occurred_at = models.DateTimeField(verbose_name="发生时间")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, db_constraint=False, blank=True, null=True)

    class Meta:
        db_table = "ivr_event"
        ordering = ["sequence"]
        constraints = [
            models.UniqueConstraint(fields=["session", "sequence"], name="ivr_event_session_seq"),
            models.UniqueConstraint(
                fields=["workspace_id", "request_id"],
                condition=~models.Q(request_id=""),
                name="ivr_event_ws_request",
            ),
        ]
        indexes = [models.Index(fields=["workspace_id", "occurred_at"], name="ivr_event_ws_time")]
