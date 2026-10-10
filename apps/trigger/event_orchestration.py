from collections import deque
from datetime import timedelta

import uuid_utils.compat as uuid
from django.db import IntegrityError, transaction
from django.db.models import Count, Max, Q
from django.utils import timezone
from rest_framework import serializers

from .models import (
    DispatchResourcePool,
    DispatchTask,
    DispatchTaskStatus,
    EventFlowNodeRun,
    EventFlowNodeAttempt,
    EventFlowRun,
    EventFlowRunEvent,
    EventFlowVersion,
    EventSourceType,
    FlowNodeRunStatus,
    FlowNodeType,
    FlowRunEventType,
    FlowRunStatus,
    FlowVersionStatus,
    StandardEvent,
    NodeActivationMode,
    NodeAttemptStatus,
    NodeDependencyMode,
    NodeFailureStrategy,
)
from .resource_coordination import ResourceCoordinationService


class FlowNodeDefinitionSerializer(serializers.Serializer):
    code = serializers.RegexField(r"^[A-Z][A-Z0-9_-]{1,63}$")
    name = serializers.CharField(max_length=160)
    node_type = serializers.ChoiceField(choices=FlowNodeType.choices)
    dependencies = serializers.ListField(
        child=serializers.RegexField(r"^[A-Z][A-Z0-9_-]{1,63}$"), required=False, default=list
    )
    resource_pool_id = serializers.UUIDField(required=False, allow_null=True, default=None)
    priority = serializers.IntegerField(min_value=1, max_value=100, required=False, default=50)
    required_units = serializers.IntegerField(min_value=1, max_value=10000, required=False, default=1)
    mutex_keys = serializers.ListField(
        child=serializers.RegexField(r"^[a-zA-Z0-9:_-]{1,80}$"), required=False, default=list
    )
    dependency_mode = serializers.ChoiceField(
        choices=NodeDependencyMode.choices, required=False, default=NodeDependencyMode.ALL_SUCCESS
    )
    activation_mode = serializers.ChoiceField(
        choices=NodeActivationMode.choices, required=False, default=NodeActivationMode.NORMAL
    )
    condition = serializers.DictField(required=False, default=dict)
    max_retries = serializers.IntegerField(min_value=0, max_value=5, required=False, default=0)
    timeout_seconds = serializers.IntegerField(
        min_value=30, max_value=86400, required=False, default=300
    )
    failure_strategy = serializers.ChoiceField(
        choices=NodeFailureStrategy.choices, required=False, default=NodeFailureStrategy.FAIL_RUN
    )
    fallback_node_code = serializers.RegexField(
        r"^[A-Z][A-Z0-9_-]{1,63}$", required=False, allow_blank=True, default=""
    )
    recovery_action = serializers.RegexField(
        r"^[A-Z][A-Z0-9_-]{1,63}$", required=False, allow_blank=True, default=""
    )

    def validate_dependencies(self, value):
        return list(dict.fromkeys(value))

    def validate_mutex_keys(self, value):
        if len(value) > 20:
            raise serializers.ValidationError("互斥资源最多配置 20 项")
        return list(dict.fromkeys(value))

    def validate_condition(self, value):
        if not value:
            return {}
        allowed_keys = {"source", "path", "operator", "value"}
        unknown = set(value) - allowed_keys
        if unknown:
            raise serializers.ValidationError(f"条件包含未知字段：{', '.join(sorted(unknown))}")
        source = value.get("source", "EVENT_PAYLOAD")
        operator = value.get("operator", "EQ")
        path = value.get("path", "")
        if source not in {"EVENT_PAYLOAD", "NODE_OUTPUT"}:
            raise serializers.ValidationError("条件来源仅支持 EVENT_PAYLOAD 或 NODE_OUTPUT")
        if operator not in {"EQ", "NE", "IN", "GTE", "LTE", "EXISTS"}:
            raise serializers.ValidationError("条件操作符不受支持")
        import re

        if not isinstance(path, str) or not re.fullmatch(r"[a-zA-Z0-9_-]+(?:\.[a-zA-Z0-9_-]+)*", path):
            raise serializers.ValidationError("条件路径格式不正确")
        return {"source": source, "path": path, "operator": operator, "value": value.get("value")}


class EventFlowCreateSerializer(serializers.Serializer):
    code = serializers.RegexField(r"^[A-Z][A-Z0-9_-]{2,63}$")
    name = serializers.CharField(max_length=160)
    description = serializers.CharField(max_length=512, allow_blank=True, required=False, default="")
    event_type = serializers.RegexField(r"^[a-zA-Z][a-zA-Z0-9._:-]{2,127}$")
    source_types = serializers.ListField(
        child=serializers.ChoiceField(choices=EventSourceType.choices), min_length=1
    )
    event_schema = serializers.DictField(required=False, default=dict)
    nodes = FlowNodeDefinitionSerializer(many=True, min_length=1, max_length=50)
    publish = serializers.BooleanField(required=False, default=False)

    def validate_source_types(self, value):
        return list(dict.fromkeys(value))

    def validate_nodes(self, nodes):
        codes = [node["code"] for node in nodes]
        if len(codes) != len(set(codes)):
            raise serializers.ValidationError("节点编号不能重复")
        code_set = set(codes)
        graph = {node["code"]: set(node["dependencies"]) for node in nodes}
        for code, dependencies in graph.items():
            unknown = dependencies - code_set
            if unknown:
                raise serializers.ValidationError(f"节点 {code} 引用了不存在的依赖：{', '.join(sorted(unknown))}")
            if code in dependencies:
                raise serializers.ValidationError(f"节点 {code} 不能依赖自身")

        by_code = {node["code"]: node for node in nodes}
        for node in nodes:
            fallback_code = node.get("fallback_node_code", "")
            if node["failure_strategy"] == NodeFailureStrategy.FALLBACK:
                if not fallback_code:
                    raise serializers.ValidationError(f"节点 {node['code']} 必须配置备用节点")
                if fallback_code == node["code"]:
                    raise serializers.ValidationError(f"节点 {node['code']} 不能将自身设为备用节点")
                fallback = by_code.get(fallback_code)
                if not fallback:
                    raise serializers.ValidationError(
                        f"节点 {node['code']} 引用了不存在的备用节点 {fallback_code}"
                    )
                if fallback["activation_mode"] != NodeActivationMode.FALLBACK_ONLY:
                    raise serializers.ValidationError(f"备用节点 {fallback_code} 必须设为仅降级激活")
                if node["code"] not in fallback["dependencies"]:
                    raise serializers.ValidationError(f"备用节点 {fallback_code} 必须依赖 {node['code']}")
            elif fallback_code:
                raise serializers.ValidationError(f"节点 {node['code']} 未使用降级策略，不能配置备用节点")
            if node["activation_mode"] == NodeActivationMode.FALLBACK_ONLY and not node["dependencies"]:
                raise serializers.ValidationError(f"备用节点 {node['code']} 必须配置上游依赖")

        indegree = {code: len(dependencies) for code, dependencies in graph.items()}
        children = {code: [] for code in codes}
        for code, dependencies in graph.items():
            for dependency in dependencies:
                children[dependency].append(code)
        queue = deque(code for code, degree in indegree.items() if degree == 0)
        visited = 0
        while queue:
            current = queue.popleft()
            visited += 1
            for child in children[current]:
                indegree[child] -= 1
                if indegree[child] == 0:
                    queue.append(child)
        if visited != len(nodes):
            raise serializers.ValidationError("DAG 存在循环依赖")
        return nodes


class StandardEventCreateSerializer(serializers.Serializer):
    event_id = serializers.CharField(max_length=128)
    idempotency_key = serializers.CharField(max_length=128)
    source_type = serializers.ChoiceField(choices=EventSourceType.choices)
    event_type = serializers.RegexField(r"^[a-zA-Z][a-zA-Z0-9._:-]{2,127}$")
    subject = serializers.CharField(max_length=160, allow_blank=True, required=False, default="")
    payload = serializers.DictField(required=False, default=dict)
    metadata = serializers.DictField(required=False, default=dict)
    occurred_at = serializers.DateTimeField(required=False, default=timezone.now)


class FlowNodeOperateSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=["SUCCEED", "FAIL", "APPROVE", "REJECT"])
    note = serializers.CharField(max_length=512, allow_blank=True, required=False, default="")
    output = serializers.DictField(required=False, default=dict)


class EventFlowReplaySerializer(serializers.Serializer):
    idempotency_key = serializers.CharField(max_length=128)


class EventOrchestrationService:
    def __init__(self, workspace_id, user):
        self.workspace_id = workspace_id
        self.user = user

    def _flow_queryset(self):
        return EventFlowVersion.objects.filter(workspace_id=self.workspace_id)

    def _run_queryset(self):
        return EventFlowRun.objects.filter(workspace_id=self.workspace_id).select_related(
            "flow_version", "standard_event"
        )

    @staticmethod
    def _run_event(run, event_type, detail, operator, node_run=None):
        sequence_no = (run.events.aggregate(maximum=Max("sequence_no"))["maximum"] or 0) + 1
        return EventFlowRunEvent.objects.create(
            workspace_id=run.workspace_id,
            run=run,
            node_run=node_run,
            sequence_no=sequence_no,
            event_type=event_type,
            detail=detail,
            operator=operator,
        )

    def create_flow(self, data):
        serializer = EventFlowCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        pool_ids = {
            str(node["resource_pool_id"])
            for node in values["nodes"]
            if node["resource_pool_id"] is not None
        }
        pools = {
            str(pool.id): pool
            for pool in DispatchResourcePool.objects.filter(
                workspace_id=self.workspace_id, id__in=pool_ids
            )
        }
        if len(pools) != len(pool_ids):
            raise serializers.ValidationError("存在不属于当前工作空间的资源池")
        for node in values["nodes"]:
            if node["node_type"] == FlowNodeType.MANUAL:
                node["resource_pool_id"] = None
                continue
            pool_id = str(node["resource_pool_id"] or "")
            if not pool_id:
                raise serializers.ValidationError(f"节点 {node['code']} 必须选择资源池")
            if node["required_units"] > pools[pool_id].max_units_per_task:
                raise serializers.ValidationError(
                    f"节点 {node['code']} 的申请配额超过资源池单任务上限"
                )

        with transaction.atomic():
            existing_versions = list(
                self._flow_queryset()
                .select_for_update()
                .filter(code=values["code"])
                .values_list("version_no", flat=True)
            )
            latest = max(existing_versions, default=0)
            flow = EventFlowVersion.objects.create(
                workspace_id=self.workspace_id,
                code=values["code"],
                name=values["name"],
                description=values["description"],
                version_no=latest + 1,
                event_type=values["event_type"],
                source_types=values["source_types"],
                event_schema=values["event_schema"],
                nodes_snapshot=[
                    {
                        **node,
                        "resource_pool_id": (
                            str(node["resource_pool_id"]) if node["resource_pool_id"] else None
                        ),
                    }
                    for node in values["nodes"]
                ],
                created_by=self.user,
            )
        if values["publish"]:
            return self.publish_flow(flow.id)
        return self.flow_detail(flow.id)

    def publish_flow(self, flow_id):
        with transaction.atomic():
            flow = self._flow_queryset().select_for_update().get(id=flow_id)
            self._flow_queryset().select_for_update().filter(
                code=flow.code, status=FlowVersionStatus.PUBLISHED
            ).exclude(id=flow.id).update(status=FlowVersionStatus.ARCHIVED)
            flow.status = FlowVersionStatus.PUBLISHED
            flow.published_at = timezone.now()
            flow.save(update_fields=["status", "published_at", "update_time"])
        return self.flow_detail(flow.id)

    @staticmethod
    def _validate_payload(flow, payload):
        required = flow.event_schema.get("required", []) if isinstance(flow.event_schema, dict) else []
        missing = [field for field in required if field not in payload]
        if missing:
            raise serializers.ValidationError(f"事件缺少必填字段：{', '.join(missing)}")

    def receive_event(self, data):
        serializer = StandardEventCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        existing = StandardEvent.objects.filter(workspace_id=self.workspace_id).filter(
            Q(event_id=values["event_id"]) | Q(idempotency_key=values["idempotency_key"])
        ).first()
        if existing:
            return self._event_result(existing, created=False)

        matching = [
            flow
            for flow in self._flow_queryset().filter(
                status=FlowVersionStatus.PUBLISHED,
                event_type=values["event_type"],
            )
            if values["source_type"] in flow.source_types
        ]
        for flow in matching:
            self._validate_payload(flow, values["payload"])

        now = timezone.now()
        try:
            with transaction.atomic():
                event = StandardEvent.objects.create(
                    workspace_id=self.workspace_id,
                    event_id=values["event_id"],
                    idempotency_key=values["idempotency_key"],
                    source_type=values["source_type"],
                    event_type=values["event_type"],
                    subject=values["subject"],
                    payload_snapshot=values["payload"],
                    metadata_snapshot=values["metadata"],
                    occurred_at=values["occurred_at"],
                    received_at=now,
                    created_by=self.user,
                )
        except IntegrityError:
            existing = StandardEvent.objects.filter(workspace_id=self.workspace_id).filter(
                Q(event_id=values["event_id"])
                | Q(idempotency_key=values["idempotency_key"])
            ).first()
            if existing:
                return self._event_result(existing, created=False)
            raise

        for flow in matching:
            self._create_run(flow, event)
        return self._event_result(event, created=True)

    def _create_run(self, flow, event, replay_of=None):
        now = timezone.now()
        with transaction.atomic():
            run, created = EventFlowRun.objects.get_or_create(
                workspace_id=self.workspace_id,
                flow_version=flow,
                standard_event=event,
                defaults={
                    "code": f"RUN-{timezone.localtime(now):%Y%m%d}-{str(uuid.uuid7()).replace('-', '')[-8:].upper()}",
                    "context_snapshot": {
                        "event_id": event.event_id,
                        "event_type": event.event_type,
                        "subject": event.subject,
                        "payload": event.payload_snapshot,
                    },
                    "trace_id": uuid.uuid7().hex,
                    "replay_of": replay_of,
                    "replay_sequence": (replay_of.replays.count() + 1) if replay_of else 0,
                    "started_at": now,
                },
            )
            if not created:
                return run
            for sequence_no, node in enumerate(flow.nodes_snapshot, start=1):
                EventFlowNodeRun.objects.create(
                    workspace_id=self.workspace_id,
                    run=run,
                    node_code=node["code"],
                    node_name=node["name"],
                    node_type=node["node_type"],
                    sequence_no=sequence_no,
                    dependencies=node.get("dependencies", []),
                    dependency_mode=node.get("dependency_mode", NodeDependencyMode.ALL_SUCCESS),
                    activation_mode=node.get("activation_mode", NodeActivationMode.NORMAL),
                    condition_snapshot=node.get("condition", {}),
                    max_retries=node.get("max_retries", 0),
                    timeout_seconds=node.get("timeout_seconds", 300),
                    failure_strategy=node.get("failure_strategy", NodeFailureStrategy.FAIL_RUN),
                    fallback_node_code=node.get("fallback_node_code", ""),
                    recovery_action=node.get("recovery_action", ""),
                    span_id=uuid.uuid7().hex,
                    resource_pool_id=node.get("resource_pool_id"),
                    priority=node.get("priority", 50),
                    required_units=node.get("required_units", 1),
                    mutex_keys=node.get("mutex_keys", []),
                    input_snapshot=run.context_snapshot,
                )
            self._run_event(
                run,
                FlowRunEventType.RUN_CREATED,
                {"flow_code": flow.code, "flow_version": flow.version_no},
                self.user,
            )
            if replay_of:
                self._run_event(
                    run,
                    FlowRunEventType.RUN_REPLAYED,
                    {"replay_of": replay_of.code, "replay_sequence": run.replay_sequence},
                    self.user,
                )
        self.advance_run(run.id)
        return run

    @staticmethod
    def _terminal_node_statuses():
        return {
            FlowNodeRunStatus.SUCCEEDED,
            FlowNodeRunStatus.FAILED,
            FlowNodeRunStatus.SKIPPED,
            FlowNodeRunStatus.CANCELLED,
        }

    @staticmethod
    def _resolve_path(value, path):
        current = value
        for part in path.split("."):
            if not isinstance(current, dict) or part not in current:
                return False, None
            current = current[part]
        return True, current

    def _condition_matches(self, run, node, nodes_by_code):
        condition = node.condition_snapshot or {}
        if not condition:
            return True
        source = condition.get("source", "EVENT_PAYLOAD")
        path = condition.get("path", "")
        if source == "EVENT_PAYLOAD":
            exists, actual = self._resolve_path(run.standard_event.payload_snapshot, path)
        else:
            node_code, _, output_path = path.partition(".")
            source_node = nodes_by_code.get(node_code)
            exists, actual = self._resolve_path(
                source_node.output_snapshot if source_node else {}, output_path
            )
        operator = condition.get("operator", "EQ")
        expected = condition.get("value")
        if operator == "EXISTS":
            return exists is bool(expected if expected is not None else True)
        if not exists:
            return False
        if operator == "EQ":
            return actual == expected
        if operator == "NE":
            return actual != expected
        if operator == "IN":
            return actual in expected if isinstance(expected, (list, tuple, str)) else False
        try:
            if operator == "GTE":
                return actual >= expected
            if operator == "LTE":
                return actual <= expected
        except TypeError:
            return False
        return False

    def _dependencies_state(self, node, status_by_code):
        if not node.dependencies:
            return True, True
        statuses = [status_by_code.get(code) for code in node.dependencies]
        all_terminal = all(status in self._terminal_node_statuses() for status in statuses)
        if node.dependency_mode == NodeDependencyMode.ALL_SUCCESS:
            return all(status == FlowNodeRunStatus.SUCCEEDED for status in statuses), all_terminal
        if node.dependency_mode == NodeDependencyMode.ANY_SUCCESS:
            return all_terminal and any(
                status == FlowNodeRunStatus.SUCCEEDED for status in statuses
            ), all_terminal
        return all_terminal, all_terminal

    def _complete_attempt(self, node, status, now, output=None, error=None):
        attempt = node.attempts.filter(attempt_no=node.active_attempt_no).first()
        if not attempt:
            return
        attempt.status = status
        attempt.output_snapshot = output or {}
        attempt.error_snapshot = error or {}
        attempt.finished_at = now
        attempt.save(
            update_fields=[
                "status",
                "output_snapshot",
                "error_snapshot",
                "finished_at",
                "update_time",
            ]
        )

    def _skip_node_locked(self, run, node, reason, now):
        node.status = FlowNodeRunStatus.SKIPPED
        node.finished_at = now
        node.output_snapshot = {"reason": reason}
        node.save(update_fields=["status", "finished_at", "output_snapshot", "update_time"])
        self._run_event(run, FlowRunEventType.NODE_SKIPPED, {"reason": reason}, self.user, node)

    def _handle_node_failure_locked(self, run, node, nodes_by_code, now, reason, timed_out=False):
        attempt_status = NodeAttemptStatus.TIMED_OUT if timed_out else NodeAttemptStatus.FAILED
        self._complete_attempt(node, attempt_status, now, error={"reason": reason})
        event_type = FlowRunEventType.NODE_TIMED_OUT if timed_out else FlowRunEventType.NODE_FAILED
        self._run_event(
            run,
            event_type,
            {"reason": reason, "attempt_no": node.active_attempt_no},
            self.user,
            node,
        )
        if node.active_attempt_no <= node.max_retries:
            node.status = FlowNodeRunStatus.READY
            node.dispatch_task = None
            node.started_at = None
            node.finished_at = None
            node.output_snapshot = {"last_error": reason}
            node.save(
                update_fields=[
                    "status",
                    "dispatch_task",
                    "started_at",
                    "finished_at",
                    "output_snapshot",
                    "update_time",
                ]
            )
            self._run_event(
                run,
                FlowRunEventType.NODE_RETRYING,
                {"next_attempt_no": node.active_attempt_no + 1, "reason": reason},
                self.user,
                node,
            )
            if node.recovery_action:
                self._run_event(
                    run,
                    FlowRunEventType.NODE_RECOVERED,
                    {"action": node.recovery_action, "result": "READY_TO_RETRY"},
                    self.user,
                    node,
                )
            return

        node.status = FlowNodeRunStatus.FAILED
        node.finished_at = now
        node.output_snapshot = {"reason": reason, "attempts": node.active_attempt_no}
        if node.failure_strategy == NodeFailureStrategy.FALLBACK:
            fallback = nodes_by_code.get(node.fallback_node_code)
            if not fallback:
                raise serializers.ValidationError("备用节点不存在，无法继续执行")
            node.failure_handled = True
            fallback.fallback_activated = True
            fallback.save(update_fields=["fallback_activated", "update_time"])
            self._run_event(
                run,
                FlowRunEventType.NODE_FALLBACK,
                {"fallback_node_code": fallback.node_code, "reason": reason},
                self.user,
                node,
            )
            if node.recovery_action:
                self._run_event(
                    run,
                    FlowRunEventType.NODE_RECOVERED,
                    {"action": node.recovery_action, "result": "FALLBACK_ACTIVATED"},
                    self.user,
                    node,
                )
        elif node.failure_strategy == NodeFailureStrategy.CONTINUE:
            node.failure_handled = True
        node.save(
            update_fields=[
                "status",
                "finished_at",
                "output_snapshot",
                "failure_handled",
                "update_time",
            ]
        )

    def _sync_resource_nodes_locked(self, run, nodes, now, coordinator):
        nodes_by_code = {node.node_code: node for node in nodes}
        for node in nodes:
            if node.status not in {
                FlowNodeRunStatus.WAITING_RESOURCE,
                FlowNodeRunStatus.RUNNING,
            } or not node.dispatch_task_id:
                continue
            dispatch = DispatchTask.objects.get(id=node.dispatch_task_id)
            if dispatch.status == DispatchTaskStatus.RUNNING and node.status != FlowNodeRunStatus.RUNNING:
                node.status = FlowNodeRunStatus.RUNNING
                node.started_at = dispatch.started_at or now
                node.save(update_fields=["status", "started_at", "update_time"])
                attempt = node.attempts.filter(attempt_no=node.active_attempt_no).first()
                if attempt and not attempt.started_at:
                    attempt.started_at = node.started_at
                    attempt.save(update_fields=["started_at", "update_time"])
                self._run_event(
                    run,
                    FlowRunEventType.NODE_STARTED,
                    {"dispatch_task_id": str(dispatch.id), "attempt_no": node.active_attempt_no},
                    self.user,
                    node,
                )
            elif dispatch.status in {DispatchTaskStatus.FAILED, DispatchTaskStatus.CANCELLED}:
                self._handle_node_failure_locked(
                    run,
                    node,
                    nodes_by_code,
                    dispatch.finished_at or now,
                    f"资源任务状态：{dispatch.status}",
                )

        for node in nodes:
            if (
                node.status == FlowNodeRunStatus.RUNNING
                and node.started_at
                and node.started_at + timedelta(seconds=node.timeout_seconds) <= now
            ):
                if node.dispatch_task_id:
                    dispatch = DispatchTask.objects.get(id=node.dispatch_task_id)
                    if dispatch.status == DispatchTaskStatus.RUNNING:
                        coordinator.operate_task(
                            dispatch.id,
                            {
                                "action": "FAIL",
                                "note": "执行路径超时，资源已释放",
                                "result_summary": {"reason": "NODE_TIMEOUT"},
                            },
                        )
                self._handle_node_failure_locked(
                    run, node, nodes_by_code, now, "NODE_TIMEOUT", timed_out=True
                )

    def advance_run(self, run_id):
        coordinator = ResourceCoordinationService(self.workspace_id, self.user)
        with transaction.atomic():
            run = EventFlowRun.objects.select_for_update().get(
                id=run_id, workspace_id=self.workspace_id
            )
            if run.status in {
                FlowRunStatus.SUCCEEDED,
                FlowRunStatus.FAILED,
                FlowRunStatus.CANCELLED,
            }:
                return self.run_detail(run.id)
            now = timezone.now()
            nodes = list(EventFlowNodeRun.objects.select_for_update().filter(run=run))
            self._sync_resource_nodes_locked(run, nodes, now, coordinator)
            status_by_code = {node.node_code: node.status for node in nodes}
            if any(
                node.status == FlowNodeRunStatus.FAILED and not node.failure_handled
                for node in nodes
            ):
                self._finish_run_locked(run, FlowRunStatus.FAILED, now)
                return self.run_detail(run.id)

            nodes_by_code = {node.node_code: node for node in nodes}
            for node in nodes:
                if node.status != FlowNodeRunStatus.PENDING:
                    continue
                dependencies_met, dependencies_terminal = self._dependencies_state(
                    node, status_by_code
                )
                if (
                    node.activation_mode == NodeActivationMode.FALLBACK_ONLY
                    and node.fallback_activated
                    and dependencies_terminal
                ):
                    dependencies_met = True
                if not dependencies_met and dependencies_terminal:
                    self._skip_node_locked(run, node, "DEPENDENCY_NOT_SATISFIED", now)
                    status_by_code[node.node_code] = node.status
                    continue
                if dependencies_met:
                    if (
                        node.activation_mode == NodeActivationMode.FALLBACK_ONLY
                        and not node.fallback_activated
                    ):
                        self._skip_node_locked(run, node, "FALLBACK_NOT_ACTIVATED", now)
                        status_by_code[node.node_code] = node.status
                        continue
                    if not self._condition_matches(run, node, nodes_by_code):
                        self._skip_node_locked(run, node, "CONDITION_NOT_MATCHED", now)
                        status_by_code[node.node_code] = node.status
                        continue
                    if node.node_type == FlowNodeType.MANUAL:
                        node.status = FlowNodeRunStatus.WAITING_MANUAL
                        event_type = FlowRunEventType.MANUAL_WAITING
                    else:
                        node.status = FlowNodeRunStatus.READY
                        event_type = FlowRunEventType.NODE_READY
                    node.save(update_fields=["status", "update_time"])
                    status_by_code[node.node_code] = node.status
                    self._run_event(run, event_type, {}, self.user, node)

            for node in nodes:
                if node.status != FlowNodeRunStatus.READY:
                    continue
                attempt_no = node.active_attempt_no + 1
                request_key = f"flow:{run.id}:node:{node.node_code}:attempt:{attempt_no}"
                dispatched = coordinator.submit_task(
                    node.resource_pool_id,
                    {
                        "request_id": request_key,
                        "idempotency_key": request_key,
                        "name": f"{run.flow_version.name} / {node.node_name}",
                        "source": run.standard_event.source_type,
                        "source_reference": run.standard_event.event_id,
                        "priority": node.priority,
                        "required_units": node.required_units,
                        "mutex_keys": node.mutex_keys,
                        "payload": node.input_snapshot,
                    },
                )["task"]
                attempt = EventFlowNodeAttempt.objects.create(
                    workspace_id=self.workspace_id,
                    run=run,
                    node_run=node,
                    attempt_no=attempt_no,
                    status=NodeAttemptStatus.RUNNING,
                    dispatch_task_id=dispatched["id"],
                    trace_id=run.trace_id,
                    span_id=uuid.uuid7().hex,
                    timeout_seconds=node.timeout_seconds,
                    input_snapshot=node.input_snapshot,
                    recovery_action=node.recovery_action,
                    started_at=now if dispatched["status"] == DispatchTaskStatus.RUNNING else None,
                )
                node.active_attempt_no = attempt_no
                node.span_id = attempt.span_id
                node.dispatch_task_id = dispatched["id"]
                if dispatched["status"] == DispatchTaskStatus.RUNNING:
                    node.status = FlowNodeRunStatus.RUNNING
                    node.started_at = now
                    event_type = FlowRunEventType.NODE_STARTED
                else:
                    node.status = FlowNodeRunStatus.WAITING_RESOURCE
                    event_type = FlowRunEventType.NODE_QUEUED
                node.save(
                    update_fields=[
                        "active_attempt_no",
                        "span_id",
                        "dispatch_task",
                        "status",
                        "started_at",
                        "update_time",
                    ]
                )
                self._run_event(
                    run,
                    event_type,
                    {
                        "dispatch_task_id": dispatched["id"],
                        "queue_reason": dispatched["queue_reason"],
                        "attempt_no": attempt_no,
                    },
                    self.user,
                    node,
                )

            self._refresh_run_status_locked(run, now)
        return self.run_detail(run.id)

    def operate_node(self, run_id, node_id, data):
        serializer = FlowNodeOperateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        coordinator = ResourceCoordinationService(self.workspace_id, self.user)
        with transaction.atomic():
            run = EventFlowRun.objects.select_for_update().get(
                id=run_id, workspace_id=self.workspace_id
            )
            nodes = list(EventFlowNodeRun.objects.select_for_update().filter(run=run))
            node = next((item for item in nodes if str(item.id) == str(node_id)), None)
            if not node:
                raise EventFlowNodeRun.DoesNotExist
            nodes_by_code = {item.node_code: item for item in nodes}
            now = timezone.now()
            action = values["action"]
            if node.node_type == FlowNodeType.MANUAL:
                if node.status != FlowNodeRunStatus.WAITING_MANUAL or action not in {
                    "APPROVE",
                    "REJECT",
                }:
                    raise serializers.ValidationError("人工节点只允许通过或拒绝")
                success = action == "APPROVE"
                event_type = (
                    FlowRunEventType.MANUAL_APPROVED
                    if success
                    else FlowRunEventType.MANUAL_REJECTED
                )
            else:
                if node.status != FlowNodeRunStatus.RUNNING or action not in {"SUCCEED", "FAIL"}:
                    raise serializers.ValidationError("执行节点只允许成功或失败收口")
                success = action == "SUCCEED"
                event_type = (
                    FlowRunEventType.NODE_SUCCEEDED
                    if success
                    else FlowRunEventType.NODE_FAILED
                )
                coordinator.operate_task(
                    node.dispatch_task_id,
                    {
                        "action": "SUCCEED" if success else "FAIL",
                        "note": values["note"],
                        "result_summary": values["output"],
                    },
                )
            if success:
                node.status = FlowNodeRunStatus.SUCCEEDED
                node.output_snapshot = values["output"] | {"note": values["note"]}
                node.finished_at = now
                node.save(
                    update_fields=["status", "output_snapshot", "finished_at", "update_time"]
                )
                if node.node_type != FlowNodeType.MANUAL:
                    self._complete_attempt(
                        node, NodeAttemptStatus.SUCCEEDED, now, output=node.output_snapshot
                    )
                self._run_event(
                    run,
                    event_type,
                    {"note": values["note"], "output": values["output"]},
                    self.user,
                    node,
                )
            elif node.node_type == FlowNodeType.MANUAL:
                node.status = FlowNodeRunStatus.FAILED
                node.output_snapshot = values["output"] | {"note": values["note"]}
                node.finished_at = now
                node.save(
                    update_fields=["status", "output_snapshot", "finished_at", "update_time"]
                )
                self._run_event(
                    run,
                    event_type,
                    {"note": values["note"], "output": values["output"]},
                    self.user,
                    node,
                )
            else:
                self._handle_node_failure_locked(
                    run, node, nodes_by_code, now, values["note"] or "NODE_EXECUTION_FAILED"
                )
        return self.advance_run(run.id)

    def _finish_run_locked(self, run, status, now):
        if run.status == status:
            return
        run.status = status
        run.finished_at = now
        run.result_summary = {"status": status}
        run.save(update_fields=["status", "finished_at", "result_summary", "update_time"])
        self._run_event(
            run,
            FlowRunEventType.RUN_SUCCEEDED
            if status == FlowRunStatus.SUCCEEDED
            else FlowRunEventType.RUN_FAILED,
            run.result_summary,
            self.user,
        )

    def _refresh_run_status_locked(self, run, now):
        statuses = list(run.node_runs.values_list("status", flat=True))
        nodes = list(run.node_runs.all())
        if nodes and all(
            node.status in {FlowNodeRunStatus.SUCCEEDED, FlowNodeRunStatus.SKIPPED}
            or (node.status == FlowNodeRunStatus.FAILED and node.failure_handled)
            for node in nodes
        ):
            self._finish_run_locked(run, FlowRunStatus.SUCCEEDED, now)
            return
        if any(
            node.status == FlowNodeRunStatus.FAILED and not node.failure_handled
            for node in nodes
        ):
            self._finish_run_locked(run, FlowRunStatus.FAILED, now)
            return
        if any(status == FlowNodeRunStatus.RUNNING for status in statuses):
            status = FlowRunStatus.RUNNING
        elif any(
            status in {FlowNodeRunStatus.WAITING_RESOURCE, FlowNodeRunStatus.WAITING_MANUAL}
            for status in statuses
        ):
            status = FlowRunStatus.WAITING
        else:
            status = FlowRunStatus.PENDING
        if run.status != status:
            run.status = status
            run.save(update_fields=["status", "update_time"])

    def flows(self):
        return [
            self._serialize_flow(flow)
            for flow in self._flow_queryset().order_by("code", "-version_no")
        ]

    def replay_run(self, run_id, data):
        serializer = EventFlowReplaySerializer(data=data)
        serializer.is_valid(raise_exception=True)
        original = self._run_queryset().get(id=run_id)
        if original.status not in {
            FlowRunStatus.SUCCEEDED,
            FlowRunStatus.FAILED,
            FlowRunStatus.CANCELLED,
        }:
            raise serializers.ValidationError("只有已结束的运行可以重放")
        idempotency_key = serializer.validated_data["idempotency_key"]
        existing = StandardEvent.objects.filter(
            workspace_id=self.workspace_id, idempotency_key=idempotency_key
        ).first()
        if existing:
            return self._event_result(existing, created=False)
        now = timezone.now()
        event = StandardEvent.objects.create(
            workspace_id=self.workspace_id,
            event_id=f"REPLAY-{original.standard_event.event_id}-{uuid.uuid7().hex[-8:].upper()}",
            idempotency_key=idempotency_key,
            source_type=original.standard_event.source_type,
            event_type=original.standard_event.event_type,
            subject=f"{original.standard_event.subject}（重放）",
            payload_snapshot=original.standard_event.payload_snapshot,
            metadata_snapshot={
                **original.standard_event.metadata_snapshot,
                "replay_of_run_id": str(original.id),
                "replay_of_run_code": original.code,
            },
            occurred_at=now,
            received_at=now,
            created_by=self.user,
        )
        self._create_run(original.flow_version, event, replay_of=original)
        return self._event_result(event, created=True)

    def flow_detail(self, flow_id):
        return self._serialize_flow(self._flow_queryset().get(id=flow_id), detail=True)

    def runs(self):
        return [
            self._serialize_run(run)
            for run in self._run_queryset().order_by("-create_time")[:100]
        ]

    def run_detail(self, run_id):
        run = self._run_queryset().get(id=run_id)
        data = self._serialize_run(run)
        data["context_snapshot"] = run.context_snapshot
        data["result_summary"] = run.result_summary
        data["nodes"] = [self._serialize_node(node) for node in run.node_runs.all()]
        data["attempts"] = [
            {
                "id": str(attempt.id),
                "node_code": attempt.node_run.node_code,
                "attempt_no": attempt.attempt_no,
                "status": attempt.status,
                "status_label": attempt.get_status_display(),
                "dispatch_task_id": (
                    str(attempt.dispatch_task_id) if attempt.dispatch_task_id else None
                ),
                "trace_id": attempt.trace_id,
                "span_id": attempt.span_id,
                "timeout_seconds": attempt.timeout_seconds,
                "output_snapshot": attempt.output_snapshot,
                "error_snapshot": attempt.error_snapshot,
                "recovery_action": attempt.recovery_action,
                "started_at": attempt.started_at.isoformat() if attempt.started_at else None,
                "finished_at": attempt.finished_at.isoformat() if attempt.finished_at else None,
            }
            for attempt in run.attempts.select_related("node_run").all()
        ]
        data["events"] = [
            {
                "id": str(event.id),
                "sequence_no": event.sequence_no,
                "event_type": event.event_type,
                "event_type_label": event.get_event_type_display(),
                "node_code": event.node_run.node_code if event.node_run else "",
                "detail": event.detail,
                "operator_name": event.operator.nick_name if event.operator else "系统",
                "create_time": event.create_time.isoformat(),
            }
            for event in run.events.select_related("node_run", "operator").all()
        ]
        return data

    def dashboard(self):
        run_counts = {
            item["status"]: item["count"]
            for item in EventFlowRun.objects.filter(workspace_id=self.workspace_id)
            .values("status")
            .annotate(count=Count("id"))
        }
        node_counts = {
            item["status"]: item["count"]
            for item in EventFlowNodeRun.objects.filter(workspace_id=self.workspace_id)
            .values("status")
            .annotate(count=Count("id"))
        }
        return {
            "summary": {
                "published_flow_count": self._flow_queryset()
                .filter(status=FlowVersionStatus.PUBLISHED)
                .count(),
                "event_count": StandardEvent.objects.filter(
                    workspace_id=self.workspace_id
                ).count(),
                "running_count": run_counts.get(FlowRunStatus.RUNNING, 0),
                "waiting_count": run_counts.get(FlowRunStatus.WAITING, 0),
                "succeeded_count": run_counts.get(FlowRunStatus.SUCCEEDED, 0),
                "failed_count": run_counts.get(FlowRunStatus.FAILED, 0),
                "manual_waiting_count": node_counts.get(FlowNodeRunStatus.WAITING_MANUAL, 0),
                "resource_waiting_count": node_counts.get(FlowNodeRunStatus.WAITING_RESOURCE, 0),
                "retried_node_count": EventFlowNodeRun.objects.filter(
                    workspace_id=self.workspace_id, active_attempt_no__gt=1
                ).count(),
                "fallback_count": EventFlowNodeRun.objects.filter(
                    workspace_id=self.workspace_id, fallback_activated=True
                ).count(),
                "skipped_node_count": node_counts.get(FlowNodeRunStatus.SKIPPED, 0),
            },
            "flows": self.flows(),
            "runs": self.runs(),
        }

    def _event_result(self, event, created):
        return {
            "created": created,
            "event": {
                "id": str(event.id),
                "event_id": event.event_id,
                "source_type": event.source_type,
                "source_type_label": event.get_source_type_display(),
                "event_type": event.event_type,
                "subject": event.subject,
                "occurred_at": event.occurred_at.isoformat(),
                "received_at": event.received_at.isoformat(),
            },
            "runs": [self._serialize_run(run) for run in event.runs.select_related("flow_version")],
        }

    @staticmethod
    def _serialize_flow(flow, detail=False):
        data = {
            "id": str(flow.id),
            "code": flow.code,
            "name": flow.name,
            "description": flow.description,
            "version_no": flow.version_no,
            "status": flow.status,
            "status_label": flow.get_status_display(),
            "event_type": flow.event_type,
            "source_types": flow.source_types,
            "node_count": len(flow.nodes_snapshot),
            "published_at": flow.published_at.isoformat() if flow.published_at else None,
            "create_time": flow.create_time.isoformat(),
        }
        if detail:
            data["event_schema"] = flow.event_schema
            data["nodes"] = flow.nodes_snapshot
        return data

    @staticmethod
    def _serialize_run(run):
        return {
            "id": str(run.id),
            "code": run.code,
            "flow_id": str(run.flow_version_id),
            "flow_code": run.flow_version.code,
            "flow_name": run.flow_version.name,
            "flow_version": run.flow_version.version_no,
            "event_id": run.standard_event.event_id,
            "event_type": run.standard_event.event_type,
            "subject": run.standard_event.subject,
            "source_type": run.standard_event.source_type,
            "status": run.status,
            "status_label": run.get_status_display(),
            "trace_id": run.trace_id,
            "replay_of_id": str(run.replay_of_id) if run.replay_of_id else None,
            "replay_sequence": run.replay_sequence,
            "node_count": run.node_runs.count(),
            "completed_node_count": run.node_runs.filter(
                Q(
                    status__in=[
                        FlowNodeRunStatus.SUCCEEDED,
                        FlowNodeRunStatus.SKIPPED,
                        FlowNodeRunStatus.CANCELLED,
                    ]
                )
                | Q(status=FlowNodeRunStatus.FAILED, failure_handled=True)
            ).count(),
            "succeeded_node_count": run.node_runs.filter(
                status=FlowNodeRunStatus.SUCCEEDED
            ).count(),
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "finished_at": run.finished_at.isoformat() if run.finished_at else None,
            "create_time": run.create_time.isoformat(),
        }

    @staticmethod
    def _serialize_node(node):
        dispatch = None
        if node.dispatch_task_id:
            task = DispatchTask.objects.get(id=node.dispatch_task_id)
            dispatch = {
                "id": str(task.id),
                "code": task.code,
                "status": task.status,
                "status_label": task.get_status_display(),
                "queue_reason": task.queue_reason,
            }
        return {
            "id": str(node.id),
            "node_code": node.node_code,
            "node_name": node.node_name,
            "node_type": node.node_type,
            "node_type_label": node.get_node_type_display(),
            "sequence_no": node.sequence_no,
            "dependencies": node.dependencies,
            "dependency_mode": node.dependency_mode,
            "activation_mode": node.activation_mode,
            "condition": node.condition_snapshot,
            "max_retries": node.max_retries,
            "timeout_seconds": node.timeout_seconds,
            "failure_strategy": node.failure_strategy,
            "fallback_node_code": node.fallback_node_code,
            "recovery_action": node.recovery_action,
            "active_attempt_no": node.active_attempt_no,
            "failure_handled": node.failure_handled,
            "fallback_activated": node.fallback_activated,
            "span_id": node.span_id,
            "resource_pool_id": str(node.resource_pool_id) if node.resource_pool_id else None,
            "priority": node.priority,
            "required_units": node.required_units,
            "mutex_keys": node.mutex_keys,
            "status": node.status,
            "status_label": node.get_status_display(),
            "dispatch_task": dispatch,
            "input_snapshot": node.input_snapshot,
            "output_snapshot": node.output_snapshot,
            "started_at": node.started_at.isoformat() if node.started_at else None,
            "finished_at": node.finished_at.isoformat() if node.finished_at else None,
        }
