# coding=utf-8
from django.db import IntegrityError
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from application.models import Application
from common.exception.app_exception import AppApiException
from common.result import Page
from knowledge.models import Knowledge
from marketing.models import MarketingScenario, MarketingScenarioStatus
from marketing.recommendation import select_recommendation, validate_recommendation_policy


class MarketingScenarioWriteSerializer(serializers.Serializer):
    name = serializers.CharField(required=True, max_length=128, label=_("Marketing scenario name"))
    target_audience = serializers.CharField(
        required=False, allow_blank=True, max_length=256, label=_("Target audience")
    )
    objective = serializers.CharField(required=False, allow_blank=True, max_length=256, label=_("Marketing objective"))
    channel = serializers.CharField(required=False, allow_blank=True, max_length=64, label=_("Channel"))
    status = serializers.ChoiceField(required=False, choices=MarketingScenarioStatus.choices, label=_("Status"))
    application_id = serializers.UUIDField(required=False, allow_null=True, label=_("Application ID"))
    knowledge_id = serializers.UUIDField(required=False, allow_null=True, label=_("Knowledge ID"))
    config = serializers.DictField(required=False, label=_("Config"))
    description = serializers.CharField(required=False, allow_blank=True, label=_("Description"))


class MarketingRecommendationSimulateSerializer(serializers.Serializer):
    current_plan = serializers.CharField(required=False, allow_blank=True, max_length=128)
    province = serializers.CharField(required=False, allow_blank=True, max_length=64)
    monthly_data_usage = serializers.CharField(required=False, allow_blank=True, max_length=64)
    monthly_call_usage = serializers.CharField(required=False, allow_blank=True, max_length=64)


class MarketingScenarioListQuerySerializer(serializers.Serializer):
    name = serializers.CharField(required=False, allow_blank=True)
    status = serializers.CharField(required=False, allow_blank=True)


def _serialize_scenario(row: MarketingScenario):
    return {
        "id": str(row.id),
        "workspace_id": row.workspace_id,
        "name": row.name,
        "target_audience": row.target_audience,
        "objective": row.objective,
        "channel": row.channel,
        "status": row.status,
        "application_id": str(row.application_id) if row.application_id else None,
        "application_name": row.application.name if row.application else "",
        "knowledge_id": str(row.knowledge_id) if row.knowledge_id else None,
        "knowledge_name": row.knowledge.name if row.knowledge else "",
        "config": row.config or {},
        "description": row.description,
        "task_count": row.tasks.count(),
        "create_user": row.user.nick_name if row.user else "",
        "create_time": row.create_time,
        "update_time": row.update_time,
    }


class MarketingScenarioService:
    def __init__(self, workspace_id: str, user=None):
        self.workspace_id = workspace_id
        self.user = user

    def _queryset(self):
        return (
            MarketingScenario.objects.filter(workspace_id=self.workspace_id)
            .select_related("application", "knowledge", "user")
            .order_by("-update_time")
        )

    def list(self, params: dict):
        serializer = MarketingScenarioListQuerySerializer(data=params)
        serializer.is_valid(raise_exception=True)
        query_set = self._queryset()
        name = serializer.validated_data.get("name")
        status = serializer.validated_data.get("status")
        if name:
            query_set = query_set.filter(
                Q(name__icontains=name)
                | Q(target_audience__icontains=name)
                | Q(objective__icontains=name)
                | Q(description__icontains=name)
            )
        if status:
            query_set = query_set.filter(status=status)
        return [_serialize_scenario(row) for row in query_set]

    def page(self, current_page: int, page_size: int, params: dict):
        records = self.list(params)
        start = (current_page - 1) * page_size
        return Page(len(records), records[start : start + page_size], current_page, page_size)

    def get(self, scenario_id: str):
        scenario = self._queryset().filter(id=scenario_id).first()
        if scenario is None:
            raise AppApiException(404, _("Marketing scenario does not exist"))
        return _serialize_scenario(scenario)

    def _validate_related(self, data: dict):
        application_id = data.get("application_id")
        knowledge_id = data.get("knowledge_id")
        application = None
        knowledge = None
        if application_id:
            application = Application.objects.filter(id=application_id, workspace_id=self.workspace_id).first()
            if application is None:
                raise AppApiException(400, _("Application does not exist in current workspace"))
        if knowledge_id:
            knowledge = Knowledge.objects.filter(id=knowledge_id, workspace_id=self.workspace_id).first()
            if knowledge is None:
                raise AppApiException(400, _("Knowledge does not exist in current workspace"))
        return application, knowledge

    def create(self, data: dict):
        serializer = MarketingScenarioWriteSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = dict(serializer.validated_data)
        validate_recommendation_policy(values.get("config"))
        application, knowledge = self._validate_related(values)
        try:
            scenario = MarketingScenario.objects.create(
                workspace_id=self.workspace_id,
                user=self.user,
                application=application,
                knowledge=knowledge,
                name=values["name"],
                target_audience=values.get("target_audience", ""),
                objective=values.get("objective", ""),
                channel=values.get("channel", "ONLINE") or "ONLINE",
                status=values.get("status", MarketingScenarioStatus.DRAFT),
                config=values.get("config", {}),
                description=values.get("description", ""),
            )
        except IntegrityError:
            raise AppApiException(400, _("Marketing scenario name already exists"))
        return _serialize_scenario(scenario)

    def update(self, scenario_id: str, data: dict):
        scenario = MarketingScenario.objects.filter(id=scenario_id, workspace_id=self.workspace_id).first()
        if scenario is None:
            raise AppApiException(404, _("Marketing scenario does not exist"))
        serializer = MarketingScenarioWriteSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = dict(serializer.validated_data)
        validate_recommendation_policy(values.get("config"))
        application, knowledge = self._validate_related(values)
        for field in ["name", "target_audience", "objective", "channel", "status", "config", "description"]:
            if field in values:
                setattr(scenario, field, values[field])
        scenario.application = application
        scenario.knowledge = knowledge
        try:
            scenario.save()
        except IntegrityError:
            raise AppApiException(400, _("Marketing scenario name already exists"))
        return _serialize_scenario(scenario)

    def simulate_recommendation(self, scenario_id: str, data: dict):
        scenario = MarketingScenario.objects.filter(id=scenario_id, workspace_id=self.workspace_id).first()
        if scenario is None:
            raise AppApiException(404, _("Marketing scenario does not exist"))
        serializer = MarketingRecommendationSimulateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        policy = scenario.config.get("recommendation_policy", {}) if isinstance(scenario.config, dict) else {}
        recommendation = select_recommendation(
            policy,
            {
                "plan": values.get("current_plan"),
                "province": values.get("province"),
                "data_usage": values.get("monthly_data_usage"),
                "call_usage": values.get("monthly_call_usage"),
            },
        )
        return {"recommendation": recommendation, "policy": validate_recommendation_policy(policy)}

    def delete(self, scenario_id: str):
        deleted, _ = MarketingScenario.objects.filter(id=scenario_id, workspace_id=self.workspace_id).delete()
        if deleted == 0:
            raise AppApiException(404, _("Marketing scenario does not exist"))
        return True
