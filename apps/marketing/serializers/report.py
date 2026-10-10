from collections import defaultdict
from datetime import datetime, time, timedelta
from decimal import Decimal, ROUND_HALF_UP
from html import escape
import json

from django.db import IntegrityError, transaction
from django.db.models import Count, Q, Sum
from django.utils import timezone
from langchain_core.messages import HumanMessage
from rest_framework import serializers

from common.exception.app_exception import AppApiException
from common.result import Page
from marketing.models import (
    MarketingAnalysisReport,
    MarketingAttributionMethod,
    MarketingConversionOutcome,
    MarketingConversionRecord,
    MarketingCustomer,
    MarketingReportAttributionDetail,
    MarketingReportDelivery,
    MarketingReportDeliveryChannel,
    MarketingReportDeliveryStatus,
    MarketingReportGenerationRun,
    MarketingReportStatus,
    MarketingReportTemplate,
    MarketingTask,
    MarketingTouchBatch,
    MarketingTouchExecution,
    MarketingTouchExecutionResult,
    RecommendationRankingRun,
)
from models_provider.base_model_provider import ModelTypeConst
from models_provider.models import Model, Status as ModelStatus
from models_provider.tools import get_model_instance_by_model_workspace_id


DEFAULT_TEMPLATE_NAME = "经营成效分析模板"


class MarketingReportTemplateWriteSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=128)
    description = serializers.CharField(required=False, allow_blank=True)
    title_template = serializers.CharField(required=False, max_length=256)
    narrative_prompt = serializers.CharField(required=False, allow_blank=False)
    active = serializers.BooleanField(required=False)
    config = serializers.DictField(required=False)


class MarketingReportGenerateSerializer(serializers.Serializer):
    template_id = serializers.UUIDField(required=False, allow_null=True)
    task_id = serializers.UUIDField(required=False, allow_null=True)
    model_id = serializers.UUIDField(required=False, allow_null=True)
    title = serializers.CharField(required=False, allow_blank=True, max_length=256)
    period_start = serializers.DateField()
    period_end = serializers.DateField()
    attribution_method = serializers.ChoiceField(
        required=False,
        default=MarketingAttributionMethod.LAST_TOUCH,
        choices=MarketingAttributionMethod.choices,
    )
    attributed_revenue = serializers.DecimalField(
        required=False, default=Decimal("0"), max_digits=16, decimal_places=2, min_value=Decimal("0")
    )
    marketing_cost = serializers.DecimalField(
        required=False, default=Decimal("0"), max_digits=16, decimal_places=2, min_value=Decimal("0")
    )
    variable_cost = serializers.DecimalField(
        required=False, default=Decimal("0"), max_digits=16, decimal_places=2, min_value=Decimal("0")
    )
    use_llm = serializers.BooleanField(required=False, default=False)

    def validate(self, attrs):
        if attrs["period_start"] > attrs["period_end"]:
            raise serializers.ValidationError({"period_end": "结束日期不能早于开始日期"})
        if attrs["use_llm"] and not attrs.get("model_id"):
            raise serializers.ValidationError({"model_id": "启用智能解读时必须选择模型"})
        return attrs


class MarketingReportQuerySerializer(serializers.Serializer):
    keyword = serializers.CharField(required=False, allow_blank=True)
    status = serializers.ChoiceField(required=False, allow_blank=True, choices=MarketingReportStatus.choices)
    task_id = serializers.UUIDField(required=False, allow_null=True)


def _money(value):
    return round(float(value or 0), 2)


def _percent(numerator, denominator):
    return round(float(numerator) / float(denominator) * 100, 1) if denominator else 0.0


def _serialize_template(template: MarketingReportTemplate):
    return {
        "id": str(template.id),
        "name": template.name,
        "description": template.description,
        "title_template": template.title_template,
        "narrative_prompt": template.narrative_prompt,
        "config": template.config or {},
        "active": template.active,
        "version": template.version,
        "create_time": template.create_time,
        "update_time": template.update_time,
    }


def _serialize_run(run: MarketingReportGenerationRun):
    return {
        "id": str(run.id),
        "attempt": run.attempt,
        "status": run.status,
        "error_message": run.error_message,
        "started_at": run.started_at,
        "finished_at": run.finished_at,
    }


def _serialize_report(report: MarketingAnalysisReport, include_content=False):
    data = {
        "id": str(report.id),
        "title": report.title,
        "period_start": report.period_start,
        "period_end": report.period_end,
        "attribution_method": report.attribution_method,
        "attribution_method_label": report.get_attribution_method_display(),
        "status": report.status,
        "template_id": str(report.template_id) if report.template_id else None,
        "template_name": report.template.name if report.template else "",
        "task_id": str(report.task_id) if report.task_id else None,
        "task_name": report.task.name if report.task else "全部营销任务",
        "model_id": str(report.model_id) if report.model_id else None,
        "model_name": report.model.name if report.model else "规则分析",
        "metrics": report.metrics or {},
        "narrative": report.narrative,
        "error_message": report.error_message,
        "retry_count": report.retry_count,
        "generated_at": report.generated_at,
        "create_user": report.user.nick_name if report.user else "",
        "create_time": report.create_time,
        "update_time": report.update_time,
    }
    if include_content:
        data["html_content"] = report.html_content
        data["input_snapshot"] = report.input_snapshot or {}
        data["runs"] = [_serialize_run(item) for item in report.runs.all()]
        data["attribution_details"] = [
            {
                "id": str(item.id),
                "conversion_id": str(item.conversion_id),
                "customer_name": item.customer.name,
                "batch_id": str(item.batch_id) if item.batch_id else None,
                "batch_name": item.batch.name if item.batch else "未匹配触达批次",
                "channel": item.channel or "未配置",
                "method": item.method,
                "weight": float(item.weight),
                "attributed_revenue": float(item.attributed_revenue),
                "touch_time": item.touch_time,
            }
            for item in report.attribution_details.all()
        ]
        data["deliveries"] = [
            {
                "id": str(item.id),
                "channel": item.channel,
                "status": item.status,
                "recipient": item.recipient,
                "error_message": item.error_message,
                "sent_at": item.sent_at,
            }
            for item in report.deliveries.all()
        ]
    return data


class MarketingAnalysisReportService:
    def __init__(self, workspace_id: str, user=None):
        self.workspace_id = workspace_id
        self.user = user

    def _report_queryset(self):
        return (
            MarketingAnalysisReport.objects.filter(workspace_id=self.workspace_id)
            .select_related("template", "task", "model", "user")
            .prefetch_related("runs", "attribution_details__customer", "attribution_details__batch", "deliveries")
            .order_by("-create_time")
        )

    def _template_queryset(self):
        return MarketingReportTemplate.objects.filter(workspace_id=self.workspace_id).order_by("-active", "name")

    def _ensure_default_template(self):
        defaults = {
            "user": self.user,
            "description": "汇总曝光、触达、转化、边际贡献和投入产出，并生成经营建议。",
        }
        try:
            template, _ = MarketingReportTemplate.objects.get_or_create(
                workspace_id=self.workspace_id,
                name=DEFAULT_TEMPLATE_NAME,
                defaults=defaults,
            )
        except IntegrityError:
            template = MarketingReportTemplate.objects.get(
                workspace_id=self.workspace_id,
                name=DEFAULT_TEMPLATE_NAME,
            )
        return template

    def metadata(self):
        self._ensure_default_template()
        tasks = MarketingTask.objects.filter(workspace_id=self.workspace_id).order_by("-update_time")
        models = Model.objects.filter(
            workspace_id=self.workspace_id,
            model_type=ModelTypeConst.LLM.name,
            status=ModelStatus.SUCCESS,
        ).order_by("name")
        return {
            "templates": [_serialize_template(row) for row in self._template_queryset()],
            "tasks": [
                {"id": str(row.id), "name": row.name, "channel": row.channel, "status": row.status}
                for row in tasks
            ],
            "models": [
                {"id": str(row.id), "name": row.name, "provider": row.provider, "model_name": row.model_name}
                for row in models
            ],
        }

    def list_templates(self):
        self._ensure_default_template()
        return [_serialize_template(row) for row in self._template_queryset()]

    def create_template(self, data):
        serializer = MarketingReportTemplateWriteSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        try:
            template = MarketingReportTemplate.objects.create(
                workspace_id=self.workspace_id,
                user=self.user,
                **serializer.validated_data,
            )
        except IntegrityError as exc:
            raise AppApiException(400, "当前工作空间已存在同名报告模板") from exc
        return _serialize_template(template)

    def update_template(self, template_id, data):
        template = self._template_queryset().filter(id=template_id).first()
        if template is None:
            raise AppApiException(404, "报告模板不存在")
        serializer = MarketingReportTemplateWriteSerializer(data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            for key, value in serializer.validated_data.items():
                setattr(template, key, value)
            template.version += 1
            template.save()
        except IntegrityError as exc:
            raise AppApiException(400, "当前工作空间已存在同名报告模板") from exc
        return _serialize_template(template)

    def delete_template(self, template_id):
        template = self._template_queryset().filter(id=template_id).first()
        if template is None:
            raise AppApiException(404, "报告模板不存在")
        if template.name == DEFAULT_TEMPLATE_NAME:
            raise AppApiException(400, "默认报告模板不能删除")
        template.delete()
        return True

    def page(self, current_page, page_size, params):
        serializer = MarketingReportQuerySerializer(data=params)
        serializer.is_valid(raise_exception=True)
        queryset = self._report_queryset()
        values = serializer.validated_data
        if values.get("keyword"):
            queryset = queryset.filter(
                Q(title__icontains=values["keyword"])
                | Q(task__name__icontains=values["keyword"])
                | Q(template__name__icontains=values["keyword"])
            )
        if values.get("status"):
            queryset = queryset.filter(status=values["status"])
        if values.get("task_id"):
            queryset = queryset.filter(task_id=values["task_id"])
        total = queryset.count()
        start = (current_page - 1) * page_size
        records = [_serialize_report(row) for row in queryset[start : start + page_size]]
        return Page(total, records, current_page, page_size)

    def get(self, report_id):
        report = self._report_queryset().filter(id=report_id).first()
        if report is None:
            raise AppApiException(404, "分析报告不存在")
        return _serialize_report(report, include_content=True)

    def _resolve_related(self, values):
        template_id = values.get("template_id")
        template = (
            self._template_queryset().filter(id=template_id, active=True).first()
            if template_id
            else self._ensure_default_template()
        )
        if template is None:
            raise AppApiException(400, "报告模板不存在或已停用")

        task = None
        if values.get("task_id"):
            task = MarketingTask.objects.filter(id=values["task_id"], workspace_id=self.workspace_id).first()
            if task is None:
                raise AppApiException(400, "营销任务不存在")

        model = None
        if values.get("model_id"):
            model = Model.objects.filter(
                id=values["model_id"],
                workspace_id=self.workspace_id,
                model_type=ModelTypeConst.LLM.name,
                status=ModelStatus.SUCCESS,
            ).first()
            if model is None:
                raise AppApiException(400, "智能解读模型不存在或不可用")
        return template, task, model

    def generate(self, data):
        serializer = MarketingReportGenerateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        template, task, model = self._resolve_related(values)
        snapshot = self._snapshot(values)
        snapshot["source_lineage"] = self._source_lineage(values, task)
        title = values.get("title", "").strip() or self._title(template, values, task)
        report = MarketingAnalysisReport.objects.create(
            workspace_id=self.workspace_id,
            template=template,
            task=task,
            model=model,
            user=self.user,
            title=title,
            period_start=values["period_start"],
            period_end=values["period_end"],
            attribution_method=values["attribution_method"],
            status=MarketingReportStatus.RUNNING,
            input_snapshot=snapshot,
        )
        return self._execute(report, values, template, task, model)

    def retry(self, report_id):
        report = self._report_queryset().filter(id=report_id).first()
        if report is None:
            raise AppApiException(404, "分析报告不存在")
        if report.status != MarketingReportStatus.FAILED:
            raise AppApiException(400, "只有生成失败的报告可以重试")
        serializer = MarketingReportGenerateSerializer(data=report.input_snapshot)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        template, task, model = self._resolve_related(values)
        report.template = template
        report.task = task
        report.model = model
        report.attribution_method = values["attribution_method"]
        report.status = MarketingReportStatus.RUNNING
        report.error_message = ""
        report.retry_count += 1
        report.save()
        return self._execute(report, values, template, task, model)

    @staticmethod
    def _snapshot(values):
        return {
            "template_id": str(values["template_id"]) if values.get("template_id") else None,
            "task_id": str(values["task_id"]) if values.get("task_id") else None,
            "model_id": str(values["model_id"]) if values.get("model_id") else None,
            "title": values.get("title", ""),
            "period_start": values["period_start"].isoformat(),
            "period_end": values["period_end"].isoformat(),
            "attribution_method": values["attribution_method"],
            "attributed_revenue": str(values["attributed_revenue"]),
            "marketing_cost": str(values["marketing_cost"]),
            "variable_cost": str(values["variable_cost"]),
            "use_llm": values["use_llm"],
        }

    def _source_lineage(self, values, task):
        """Freeze bounded, workspace-scoped related fact IDs without asserting causality."""
        if task is None:
            return {"scope": "ALL_TASKS_NOT_ENUMERATED"}
        from platform_monitoring.models import MetricDispatchOrder
        from trigger.models import EventFlowRun

        start, end = self._period_bounds(values)
        scoped = {"workspace_id": self.workspace_id, "create_time__gte": start, "create_time__lt": end}

        def references(rows):
            total = rows.count()
            return {
                "total_count": total,
                "ids": [str(pk) for pk in rows.order_by("id").values_list("id", flat=True)[:100]],
                "truncated": total > 100,
            }

        return {
            "scope": "TASK_PERIOD_ASSOCIATION",
            "task_id": str(task.id),
            "touch_executions": references(MarketingTouchExecution.objects.filter(
                **scoped, batch__task_id=task.id,
            )),
            "recommendation_rankings": references(RecommendationRankingRun.objects.filter(
                **scoped, customer__task_id=task.id,
            )),
            "metric_dispatch_orders": references(MetricDispatchOrder.objects.filter(
                **scoped, incident__observation__dimensions__task_id=str(task.id),
            )),
            "event_flow_runs": references(EventFlowRun.objects.filter(
                **scoped, standard_event__payload_snapshot__task_id=str(task.id),
            )),
        }

    @staticmethod
    def _title(template, values, task):
        replacements = {
            "start_date": values["period_start"].isoformat(),
            "end_date": values["period_end"].isoformat(),
            "task_name": task.name if task else "全量营销任务",
        }
        title = template.title_template
        for key, value in replacements.items():
            title = title.replace("{" + key + "}", value)
        return title[:256]

    def _period_bounds(self, values):
        zone = timezone.get_current_timezone()
        start = timezone.make_aware(datetime.combine(values["period_start"], time.min), zone)
        end = timezone.make_aware(datetime.combine(values["period_end"] + timedelta(days=1), time.min), zone)
        return start, end

    def _calculate_attribution(self, conversions, executions, values):
        method = values["attribution_method"]
        conversion_rows = list(conversions.select_related("customer", "batch", "task"))
        revenue_total = Decimal(values["attributed_revenue"] or 0).quantize(Decimal("0.01"))
        revenue_per_conversion = (
            revenue_total / len(conversion_rows) if conversion_rows else Decimal("0")
        )
        detail_rows = []
        channel_revenue = defaultdict(lambda: Decimal("0"))
        channel_weight = defaultdict(lambda: Decimal("0"))

        for conversion_index, conversion in enumerate(conversion_rows):
            candidates = list(
                executions.filter(
                    customer_id=conversion.customer_id,
                    create_time__lte=conversion.create_time,
                )
                .select_related("batch", "batch__task")
                .order_by("-create_time")
            )
            unique_candidates = []
            seen_batches = set()
            for execution in candidates:
                if execution.batch_id not in seen_batches:
                    unique_candidates.append(execution)
                    seen_batches.add(execution.batch_id)
            if conversion.batch_id and conversion.batch_id not in seen_batches:
                unique_candidates.append(None)
            if method == MarketingAttributionMethod.LAST_TOUCH:
                unique_candidates = unique_candidates[:1]
            if not unique_candidates:
                unique_candidates = [None]

            row_revenue = revenue_per_conversion
            if conversion_index == len(conversion_rows) - 1:
                row_revenue = revenue_total - (revenue_per_conversion * (len(conversion_rows) - 1))
            weight = (Decimal("1") / len(unique_candidates)).quantize(Decimal("0.000001"))
            allocated = Decimal("0")
            for touch_index, execution in enumerate(unique_candidates):
                batch = execution.batch if execution else conversion.batch
                touch_time = execution.create_time if execution else None
                channel = batch.task.channel if batch and batch.task else conversion.task.channel
                touch_revenue = (row_revenue * weight).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                if touch_index == len(unique_candidates) - 1:
                    touch_revenue = row_revenue - allocated
                allocated += touch_revenue
                detail_rows.append(
                    MarketingReportAttributionDetail(
                        workspace_id=self.workspace_id,
                        conversion=conversion,
                        customer=conversion.customer,
                        batch=batch,
                        method=method,
                        channel=channel or "未配置",
                        weight=weight,
                        attributed_revenue=touch_revenue,
                        touch_time=touch_time,
                    )
                )
                channel_revenue[channel or "未配置"] += touch_revenue
                channel_weight[channel or "未配置"] += weight

        distribution = [
            {
                "channel": channel,
                "weight": float(channel_weight[channel]),
                "attributed_revenue": float(amount),
                "revenue_share": _percent(amount, revenue_total),
            }
            for channel, amount in sorted(channel_revenue.items(), key=lambda item: item[1], reverse=True)
        ]
        return detail_rows, distribution

    def _calculate_metrics(self, values, task):
        start, end = self._period_bounds(values)
        tasks = MarketingTask.objects.filter(workspace_id=self.workspace_id)
        if task:
            tasks = tasks.filter(id=task.id)
        task_ids = list(tasks.values_list("id", flat=True))
        customers = MarketingCustomer.objects.filter(workspace_id=self.workspace_id, task_id__in=task_ids)
        batches = MarketingTouchBatch.objects.filter(
            workspace_id=self.workspace_id,
            task_id__in=task_ids,
            create_time__gte=start,
            create_time__lt=end,
        )
        executions = MarketingTouchExecution.objects.filter(
            workspace_id=self.workspace_id,
            batch__task_id__in=task_ids,
            create_time__gte=start,
            create_time__lt=end,
        )
        conversions = MarketingConversionRecord.objects.filter(
            workspace_id=self.workspace_id,
            task_id__in=task_ids,
            outcome=MarketingConversionOutcome.CONVERTED,
            create_time__gte=start,
            create_time__lt=end,
        )

        exposure_count = batches.aggregate(total=Sum("selected_count"))["total"] or 0
        touch_count = executions.count()
        reached_customer_count = (
            executions.exclude(result=MarketingTouchExecutionResult.NO_ANSWER)
            .values("customer_id")
            .distinct()
            .count()
        )
        converted_customer_count = conversions.values("customer_id").distinct().count()
        revenue = _money(values["attributed_revenue"])
        marketing_cost = _money(values["marketing_cost"])
        variable_cost = _money(values["variable_cost"])
        marginal_contribution = round(revenue - variable_cost, 2)
        roi = round((revenue - marketing_cost) / marketing_cost * 100, 1) if marketing_cost else 0.0
        channel_rows = tasks.values("channel").annotate(task_count=Count("id"), target_count=Sum("target_count"))
        attribution_rows, attribution_distribution = self._calculate_attribution(conversions, executions, values)
        return {
            "task_count": len(task_ids),
            "customer_count": customers.count(),
            "batch_count": batches.count(),
            "exposure_count": exposure_count,
            "touch_count": touch_count,
            "reached_customer_count": reached_customer_count,
            "touch_rate": _percent(reached_customer_count, exposure_count),
            "conversion_count": conversions.count(),
            "converted_customer_count": converted_customer_count,
            "conversion_rate": _percent(converted_customer_count, reached_customer_count),
            "attributed_revenue": revenue,
            "marketing_cost": marketing_cost,
            "variable_cost": variable_cost,
            "marginal_contribution": marginal_contribution,
            "roi": roi,
            "attribution_method": values["attribution_method"],
            "attribution_method_label": MarketingAttributionMethod(values["attribution_method"]).label,
            "attribution_touch_count": len(attribution_rows),
            "attribution_distribution": attribution_distribution,
            "channel_distribution": [
                {
                    "channel": row["channel"] or "未配置",
                    "task_count": row["task_count"],
                    "target_count": row["target_count"] or 0,
                }
                for row in channel_rows
            ],
        }, attribution_rows

    @staticmethod
    def _rule_narrative(metrics):
        performance = (
            f"统计周期内共覆盖 {metrics['exposure_count']} 人，实际触达 {metrics['reached_customer_count']} 人，"
            f"触达率 {metrics['touch_rate']}%；确认转化 {metrics['converted_customer_count']} 人，"
            f"触达后转化率 {metrics['conversion_rate']}%。"
        )
        finance = (
            f"归因收入 {metrics['attributed_revenue']:.2f} 元，营销投入 {metrics['marketing_cost']:.2f} 元，"
            f"边际贡献 {metrics['marginal_contribution']:.2f} 元，ROI {metrics['roi']}%。"
        )
        if not metrics["exposure_count"]:
            advice = "当前周期尚无触达批次数据，建议先完成客户筛选和批次执行，再评估经营成效。"
        elif metrics["touch_rate"] < 60:
            advice = "触达率偏低，建议优先检查客户数据有效性、触达时段和渠道策略。"
        elif metrics["conversion_rate"] < 10:
            advice = "触达已形成规模但转化仍低，建议复盘客群匹配、产品卖点和转人工承接链路。"
        else:
            advice = "当前转化表现相对稳定，建议保留高效客群与渠道组合，并继续做小范围增量验证。"
        return performance + finance + advice

    @staticmethod
    def _llm_narrative(model_id, workspace_id, template, metrics):
        prompt = (
            f"{template.narrative_prompt}\n\n"
            "以下是系统计算的指标，所有结论必须以这些数据为准：\n"
            f"{json.dumps(metrics, ensure_ascii=False)}"
        )
        model = get_model_instance_by_model_workspace_id(model_id, workspace_id)
        response = model.invoke([HumanMessage(content=prompt)])
        content = response.content if hasattr(response, "content") else str(response)
        if isinstance(content, list):
            content = "".join(str(item.get("text", item)) if isinstance(item, dict) else str(item) for item in content)
        content = str(content).strip()
        if not content:
            raise ValueError("模型未返回分析内容")
        return prompt, content

    @staticmethod
    def _render_html(report, metrics, narrative):
        metric_rows = [
            ("曝光人数", metrics["exposure_count"]),
            ("实际触达人数", metrics["reached_customer_count"]),
            ("触达率", f"{metrics['touch_rate']}%"),
            ("确认转化人数", metrics["converted_customer_count"]),
            ("触达后转化率", f"{metrics['conversion_rate']}%"),
            ("归因收入", f"¥{metrics['attributed_revenue']:.2f}"),
            ("营销投入", f"¥{metrics['marketing_cost']:.2f}"),
            ("边际贡献", f"¥{metrics['marginal_contribution']:.2f}"),
            ("ROI", f"{metrics['roi']}%"),
        ]
        rows = "".join(
            f"<tr><th>{escape(str(label))}</th><td>{escape(str(value))}</td></tr>" for label, value in metric_rows
        )
        channels = "".join(
            "<li>"
            f"{escape(str(item['channel']))}：{item['task_count']} 个任务，目标 {item['target_count']} 人"
            "</li>"
            for item in metrics["channel_distribution"]
        ) or "<li>暂无渠道数据</li>"
        attribution = "".join(
            '<div class="attribution-bar"><div><strong>'
            f"{escape(str(item['channel']))}</strong><span>¥{item['attributed_revenue']:.2f} · "
            f"{item['revenue_share']}%</span></div><i style=\"width:{min(item['revenue_share'], 100)}%\"></i></div>"
            for item in metrics.get("attribution_distribution", [])
        ) or "<p>当前周期暂无可归因转化记录。</p>"
        return (
            '<article class="analysis-report-document">'
            f"<header><p>AI ANALYSIS REPORT</p><h1>{escape(report.title)}</h1>"
            f"<span>{report.period_start.isoformat()} — {report.period_end.isoformat()}</span></header>"
            '<section><h2>核心经营指标</h2><table><tbody>' + rows + "</tbody></table></section>"
            f"<section><h2>经营解读</h2><p>{escape(narrative)}</p></section>"
            f"<section><h2>{escape(metrics['attribution_method_label'])}分布</h2>{attribution}</section>"
            f"<section><h2>渠道覆盖</h2><ul>{channels}</ul></section>"
            "</article>"
        )

    def _execute(self, report, values, template, task, model):
        attempt = report.retry_count + 1
        run = MarketingReportGenerationRun.objects.create(
            workspace_id=self.workspace_id,
            report=report,
            user=self.user,
            attempt=attempt,
            status=MarketingReportStatus.RUNNING,
            input_snapshot=report.input_snapshot,
            started_at=timezone.now(),
        )
        try:
            metrics, attribution_rows = self._calculate_metrics(values, task)
            prompt = ""
            if values["use_llm"]:
                prompt, narrative = self._llm_narrative(str(model.id), self.workspace_id, template, metrics)
            else:
                narrative = self._rule_narrative(metrics)
            html_content = self._render_html(report, metrics, narrative)
            now = timezone.now()
            with transaction.atomic():
                MarketingReportAttributionDetail.objects.filter(report=report).delete()
                for row in attribution_rows:
                    row.report = report
                MarketingReportAttributionDetail.objects.bulk_create(attribution_rows)
                MarketingAnalysisReport.objects.filter(id=report.id).update(
                    status=MarketingReportStatus.SUCCESS,
                    metrics=metrics,
                    narrative=narrative,
                    html_content=html_content,
                    error_message="",
                    generated_at=now,
                )
                MarketingReportGenerationRun.objects.filter(id=run.id).update(
                    status=MarketingReportStatus.SUCCESS,
                    metrics_snapshot=metrics,
                    prompt=prompt,
                    raw_output=narrative if values["use_llm"] else "",
                    finished_at=now,
                )
        except Exception:  # Generation errors are persisted so the user can retry without leaking provider details.
            message = (
                "智能解读模型调用失败，请检查模型服务和配置后重试。"
                if values["use_llm"]
                else "报告生成失败，请检查统计数据后重试。"
            )
            now = timezone.now()
            with transaction.atomic():
                MarketingAnalysisReport.objects.filter(id=report.id).update(
                    status=MarketingReportStatus.FAILED,
                    error_message=message,
                )
                MarketingReportGenerationRun.objects.filter(id=run.id).update(
                    status=MarketingReportStatus.FAILED,
                    error_message=message,
                    finished_at=now,
                )
        refreshed = self._report_queryset().get(id=report.id)
        from marketing.serializers.notifications import MarketingNotificationService

        notice_created = MarketingNotificationService(self.workspace_id, self.user).dispatch_report(refreshed)
        if notice_created:
            MarketingReportDelivery.objects.get_or_create(
                workspace_id=self.workspace_id,
                report=refreshed,
                user=self.user or refreshed.user,
                channel=MarketingReportDeliveryChannel.IN_APP,
                recipient=str((self.user or refreshed.user).id),
                defaults={
                    "status": MarketingReportDeliveryStatus.SUCCESS,
                    "sent_at": timezone.now(),
                },
            )
        return _serialize_report(refreshed, include_content=True)
