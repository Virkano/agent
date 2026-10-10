from datetime import timedelta

import uuid_utils.compat as uuid
from django.db import IntegrityError, transaction
from django.db.models import Count, Max, Q, Sum
from django.utils import timezone
from rest_framework import serializers

from .models import (
    DispatchEventType,
    DispatchResourceLease,
    DispatchResourcePool,
    DispatchTask,
    DispatchTaskEvent,
    DispatchTaskSource,
    DispatchTaskStatus,
    ResourceLeaseStatus,
    ResourcePoolType,
)


class ResourcePoolCreateSerializer(serializers.Serializer):
    code = serializers.RegexField(r"^[A-Z][A-Z0-9_-]{2,63}$")
    name = serializers.CharField(max_length=128)
    resource_type = serializers.ChoiceField(choices=ResourcePoolType.choices)
    capacity = serializers.IntegerField(min_value=1, max_value=10000)
    max_units_per_task = serializers.IntegerField(min_value=1, max_value=10000)
    lease_timeout_seconds = serializers.IntegerField(min_value=30, max_value=86400)
    description = serializers.CharField(max_length=512, allow_blank=True, required=False, default="")
    metadata = serializers.DictField(required=False, default=dict)

    def validate(self, attrs):
        if attrs["max_units_per_task"] > attrs["capacity"]:
            raise serializers.ValidationError("单任务最大配额不能超过资源池总配额")
        return attrs


class DispatchTaskCreateSerializer(serializers.Serializer):
    request_id = serializers.CharField(max_length=128)
    idempotency_key = serializers.CharField(max_length=128)
    name = serializers.CharField(max_length=160)
    source = serializers.ChoiceField(choices=DispatchTaskSource.choices)
    source_reference = serializers.CharField(max_length=160, allow_blank=True, required=False, default="")
    priority = serializers.IntegerField(min_value=1, max_value=100)
    required_units = serializers.IntegerField(min_value=1, max_value=10000)
    mutex_keys = serializers.ListField(
        child=serializers.RegexField(r"^[a-zA-Z0-9:_-]{1,80}$"), required=False, default=list
    )
    payload = serializers.DictField(required=False, default=dict)

    def validate_mutex_keys(self, value):
        if len(value) > 20:
            raise serializers.ValidationError("互斥资源最多配置 20 项")
        return list(dict.fromkeys(value))


class DispatchTaskOperateSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=["SUCCEED", "FAIL", "CANCEL"])
    note = serializers.CharField(max_length=512, allow_blank=True, required=False, default="")
    result_summary = serializers.DictField(required=False, default=dict)


class ResourceCoordinationService:
    def __init__(self, workspace_id, user):
        self.workspace_id = workspace_id
        self.user = user

    def _pool_queryset(self):
        return DispatchResourcePool.objects.filter(workspace_id=self.workspace_id)

    def _task_queryset(self):
        return DispatchTask.objects.filter(workspace_id=self.workspace_id).select_related("pool")

    @staticmethod
    def _event(task, event_type, previous_status, current_status, detail, operator):
        sequence_no = (task.events.aggregate(maximum=Max("sequence_no"))["maximum"] or 0) + 1
        return DispatchTaskEvent.objects.create(
            workspace_id=task.workspace_id,
            task=task,
            sequence_no=sequence_no,
            event_type=event_type,
            previous_status=previous_status,
            current_status=current_status,
            detail=detail,
            operator=operator,
        )

    @staticmethod
    def _active_leases(pool):
        return list(
            DispatchResourceLease.objects.filter(pool=pool, status=ResourceLeaseStatus.ACTIVE)
            .select_related("task")
            .order_by("acquired_at")
        )

    def _try_allocate_locked(self, task, pool, now):
        active_leases = self._active_leases(pool)
        used_units = sum(item.units for item in active_leases)
        requested_mutex = set(task.mutex_keys or [])
        occupied_mutex = {key for lease in active_leases for key in (lease.mutex_keys or [])}
        conflict_keys = sorted(requested_mutex & occupied_mutex)

        reason = ""
        if not pool.enabled:
            reason = "资源池已停用"
        elif task.required_units > pool.max_units_per_task:
            reason = f"请求 {task.required_units} 单位，超过单任务上限 {pool.max_units_per_task}"
        elif used_units + task.required_units > pool.capacity:
            reason = f"剩余配额 {pool.capacity - used_units}，需要 {task.required_units}"
        elif conflict_keys:
            reason = f"互斥资源冲突：{', '.join(conflict_keys)}"

        if reason:
            previous_reason = task.queue_reason
            task.status = DispatchTaskStatus.QUEUED
            task.queue_reason = reason
            task.save(update_fields=["status", "queue_reason", "update_time"])
            if previous_reason != reason:
                self._event(
                    task,
                    DispatchEventType.QUEUED,
                    DispatchTaskStatus.QUEUED,
                    DispatchTaskStatus.QUEUED,
                    {"reason": reason},
                    self.user,
                )
            return False

        previous_status = task.status
        expires_at = now + timedelta(seconds=pool.lease_timeout_seconds)
        DispatchResourceLease.objects.create(
            workspace_id=self.workspace_id,
            pool=pool,
            task=task,
            units=task.required_units,
            mutex_keys=task.mutex_keys,
            acquired_at=now,
            expires_at=expires_at,
        )
        task.status = DispatchTaskStatus.RUNNING
        task.queue_reason = ""
        task.started_at = now
        task.save(update_fields=["status", "queue_reason", "started_at", "update_time"])
        self._event(
            task,
            DispatchEventType.ALLOCATED,
            previous_status,
            DispatchTaskStatus.RUNNING,
            {
                "pool_code": pool.code,
                "units": task.required_units,
                "mutex_keys": task.mutex_keys,
                "expires_at": expires_at.isoformat(),
            },
            self.user,
        )
        return True

    def _dispatch_waiting_locked(self, pool, now):
        allocated = []
        queued = list(
            DispatchTask.objects.select_for_update()
            .filter(pool=pool, status=DispatchTaskStatus.QUEUED)
            .order_by("-priority", "queued_at", "create_time")
        )
        for task in queued:
            if self._try_allocate_locked(task, pool, now):
                allocated.append(str(task.id))
        return allocated

    def _reclaim_expired_locked(self, pool, now):
        leases = list(
            DispatchResourceLease.objects.select_for_update()
            .select_related("task")
            .filter(pool=pool, status=ResourceLeaseStatus.ACTIVE, expires_at__lte=now)
        )
        for lease in leases:
            lease.status = ResourceLeaseStatus.EXPIRED
            lease.released_at = now
            lease.release_reason = "租约超时自动回收"
            lease.save(update_fields=["status", "released_at", "release_reason", "update_time"])
            task = lease.task
            previous_status = task.status
            task.status = DispatchTaskStatus.FAILED
            task.finished_at = now
            task.result_summary = {"reason": "RESOURCE_LEASE_EXPIRED"}
            task.save(update_fields=["status", "finished_at", "result_summary", "update_time"])
            self._event(
                task,
                DispatchEventType.LEASE_EXPIRED,
                previous_status,
                DispatchTaskStatus.FAILED,
                {"lease_id": str(lease.id), "expired_at": lease.expires_at.isoformat()},
                self.user,
            )
        return [str(item.id) for item in leases]

    def create_pool(self, data):
        serializer = ResourcePoolCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        pool, created = DispatchResourcePool.objects.get_or_create(
            workspace_id=self.workspace_id,
            code=serializer.validated_data["code"],
            defaults={**serializer.validated_data, "created_by": self.user},
        )
        if not created:
            raise serializers.ValidationError("资源池编号已存在")
        return self.pool_detail(pool.id)

    def submit_task(self, pool_id, data):
        serializer = DispatchTaskCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data

        with transaction.atomic():
            pool = self._pool_queryset().select_for_update().get(id=pool_id)
            existing = DispatchTask.objects.filter(workspace_id=self.workspace_id).filter(
                Q(idempotency_key=values["idempotency_key"]) | Q(request_id=values["request_id"])
            ).first()
            if existing:
                return {"created": False, "task": self.task_detail(existing.id)}
            if values["required_units"] > pool.max_units_per_task:
                raise serializers.ValidationError(
                    f"请求配额不能超过单任务上限 {pool.max_units_per_task}"
                )
            now = timezone.now()
            try:
                with transaction.atomic():
                    task = DispatchTask.objects.create(
                        workspace_id=self.workspace_id,
                        pool=pool,
                        request_id=values["request_id"],
                        idempotency_key=values["idempotency_key"],
                        code=f"DSP-{timezone.localtime(now):%Y%m%d}-{str(uuid.uuid7()).replace('-', '')[-8:].upper()}",
                        name=values["name"],
                        source=values["source"],
                        source_reference=values["source_reference"],
                        priority=values["priority"],
                        required_units=values["required_units"],
                        mutex_keys=values["mutex_keys"],
                        payload_snapshot=values["payload"],
                        queued_at=now,
                        created_by=self.user,
                    )
            except IntegrityError:
                existing = DispatchTask.objects.filter(workspace_id=self.workspace_id).filter(
                    Q(idempotency_key=values["idempotency_key"])
                    | Q(request_id=values["request_id"])
                ).first()
                if existing:
                    return {"created": False, "task": self.task_detail(existing.id)}
                raise
            self._event(
                task,
                DispatchEventType.SUBMITTED,
                "",
                DispatchTaskStatus.QUEUED,
                {"priority": task.priority, "required_units": task.required_units},
                self.user,
            )
            self._reclaim_expired_locked(pool, now)
            self._dispatch_waiting_locked(pool, now)
        return {"created": True, "task": self.task_detail(task.id)}

    def operate_task(self, task_id, data):
        serializer = DispatchTaskOperateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        with transaction.atomic():
            task = self._task_queryset().select_for_update().get(id=task_id)
            pool = self._pool_queryset().select_for_update().get(id=task.pool_id)
            action = values["action"]
            if action in {"SUCCEED", "FAIL"} and task.status != DispatchTaskStatus.RUNNING:
                raise serializers.ValidationError("只有执行中的任务可以成功或失败收口")
            if action == "CANCEL" and task.status not in {
                DispatchTaskStatus.QUEUED,
                DispatchTaskStatus.RUNNING,
            }:
                raise serializers.ValidationError("只有等待中或执行中的任务可以取消")

            now = timezone.now()
            previous_status = task.status
            status_map = {
                "SUCCEED": DispatchTaskStatus.SUCCEEDED,
                "FAIL": DispatchTaskStatus.FAILED,
                "CANCEL": DispatchTaskStatus.CANCELLED,
            }
            event_map = {
                "SUCCEED": DispatchEventType.SUCCEEDED,
                "FAIL": DispatchEventType.FAILED,
                "CANCEL": DispatchEventType.CANCELLED,
            }
            task.status = status_map[action]
            task.finished_at = now
            task.result_summary = values["result_summary"] | {"note": values["note"]}
            task.queue_reason = ""
            task.save(
                update_fields=["status", "finished_at", "result_summary", "queue_reason", "update_time"]
            )
            lease = DispatchResourceLease.objects.select_for_update().filter(task=task).first()
            if lease and lease.status == ResourceLeaseStatus.ACTIVE:
                lease.status = ResourceLeaseStatus.RELEASED
                lease.released_at = now
                lease.release_reason = values["note"] or task.get_status_display()
                lease.save(update_fields=["status", "released_at", "release_reason", "update_time"])
            self._event(
                task,
                event_map[action],
                previous_status,
                task.status,
                {"note": values["note"], "result_summary": values["result_summary"]},
                self.user,
            )
            allocated = self._dispatch_waiting_locked(pool, now)
        return {"task": self.task_detail(task.id), "allocated_task_ids": allocated}

    def reclaim_pool(self, pool_id):
        with transaction.atomic():
            pool = self._pool_queryset().select_for_update().get(id=pool_id)
            now = timezone.now()
            expired = self._reclaim_expired_locked(pool, now)
            allocated = self._dispatch_waiting_locked(pool, now)
        return {"expired_lease_ids": expired, "allocated_task_ids": allocated}

    def pools(self):
        return [self._serialize_pool(pool) for pool in self._pool_queryset().order_by("code")]

    def pool_detail(self, pool_id):
        return self._serialize_pool(self._pool_queryset().get(id=pool_id))

    def tasks(self, params=None):
        params = params or {}
        queryset = self._task_queryset()
        if params.get("status"):
            queryset = queryset.filter(status=params["status"])
        if params.get("pool_id"):
            queryset = queryset.filter(pool_id=params["pool_id"])
        if params.get("source"):
            queryset = queryset.filter(source=params["source"])
        if params.get("keyword"):
            keyword = params["keyword"]
            queryset = queryset.filter(Q(name__icontains=keyword) | Q(code__icontains=keyword))
        return [self._serialize_task(task) for task in queryset.order_by("-priority", "-create_time")]

    def task_detail(self, task_id):
        task = self._task_queryset().get(id=task_id)
        data = self._serialize_task(task)
        data["payload_snapshot"] = task.payload_snapshot
        data["result_summary"] = task.result_summary
        data["events"] = [
            {
                "id": str(event.id),
                "sequence_no": event.sequence_no,
                "event_type": event.event_type,
                "event_type_label": event.get_event_type_display(),
                "previous_status": event.previous_status,
                "current_status": event.current_status,
                "current_status_label": event.get_current_status_display(),
                "detail": event.detail,
                "operator_name": event.operator.nick_name if event.operator else "系统",
                "create_time": event.create_time.isoformat(),
            }
            for event in task.events.select_related("operator").all()
        ]
        return data

    def dashboard(self):
        task_counts = {
            item["status"]: item["count"]
            for item in DispatchTask.objects.filter(workspace_id=self.workspace_id)
            .values("status")
            .annotate(count=Count("id"))
        }
        active_leases = DispatchResourceLease.objects.filter(
            workspace_id=self.workspace_id, status=ResourceLeaseStatus.ACTIVE
        )
        return {
            "summary": {
                "pool_count": self._pool_queryset().count(),
                "enabled_pool_count": self._pool_queryset().filter(enabled=True).count(),
                "queued_task_count": task_counts.get(DispatchTaskStatus.QUEUED, 0),
                "running_task_count": task_counts.get(DispatchTaskStatus.RUNNING, 0),
                "succeeded_task_count": task_counts.get(DispatchTaskStatus.SUCCEEDED, 0),
                "failed_task_count": task_counts.get(DispatchTaskStatus.FAILED, 0),
                "active_lease_count": active_leases.count(),
                "allocated_units": active_leases.aggregate(total=Sum("units"))["total"] or 0,
                "mutex_conflict_count": DispatchTask.objects.filter(
                    workspace_id=self.workspace_id,
                    status=DispatchTaskStatus.QUEUED,
                    queue_reason__startswith="互斥资源冲突",
                ).count(),
            },
            "pools": self.pools(),
            "tasks": self.tasks()[:50],
        }

    def _serialize_pool(self, pool):
        active_leases = DispatchResourceLease.objects.filter(
            pool=pool, status=ResourceLeaseStatus.ACTIVE
        )
        used_units = active_leases.aggregate(total=Sum("units"))["total"] or 0
        return {
            "id": str(pool.id),
            "code": pool.code,
            "name": pool.name,
            "resource_type": pool.resource_type,
            "resource_type_label": pool.get_resource_type_display(),
            "capacity": pool.capacity,
            "used_units": used_units,
            "available_units": max(pool.capacity - used_units, 0),
            "utilization_percent": round(used_units / pool.capacity * 100, 2),
            "max_units_per_task": pool.max_units_per_task,
            "lease_timeout_seconds": pool.lease_timeout_seconds,
            "enabled": pool.enabled,
            "description": pool.description,
            "metadata": pool.metadata,
            "active_lease_count": active_leases.count(),
            "queued_task_count": DispatchTask.objects.filter(
                pool=pool, status=DispatchTaskStatus.QUEUED
            ).count(),
            "create_time": pool.create_time.isoformat(),
        }

    @staticmethod
    def _serialize_task(task):
        try:
            lease = task.lease
        except DispatchResourceLease.DoesNotExist:
            lease = None
        return {
            "id": str(task.id),
            "pool_id": str(task.pool_id),
            "pool_code": task.pool.code,
            "pool_name": task.pool.name,
            "code": task.code,
            "name": task.name,
            "source": task.source,
            "source_label": task.get_source_display(),
            "source_reference": task.source_reference,
            "priority": task.priority,
            "required_units": task.required_units,
            "mutex_keys": task.mutex_keys,
            "status": task.status,
            "status_label": task.get_status_display(),
            "queue_reason": task.queue_reason,
            "queued_at": task.queued_at.isoformat(),
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "finished_at": task.finished_at.isoformat() if task.finished_at else None,
            "lease": {
                "id": str(lease.id),
                "status": lease.status,
                "status_label": lease.get_status_display(),
                "units": lease.units,
                "expires_at": lease.expires_at.isoformat(),
                "released_at": lease.released_at.isoformat() if lease.released_at else None,
                "release_reason": lease.release_reason,
            }
            if lease
            else None,
            "create_time": task.create_time.isoformat(),
        }
