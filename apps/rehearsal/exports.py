import csv
from io import StringIO

from django.utils import timezone

from .serializers import IMPORT_FIELDS


def _safe_csv_value(value):
    text = "" if value is None else str(value)
    if text.startswith(("=", "+", "-", "@")):
        return f"'{text}"
    return text


def _csv_bytes(rows):
    output = StringIO()
    writer = csv.writer(output)
    for row in rows:
        writer.writerow([_safe_csv_value(value) for value in row])
    return output.getvalue().encode("utf-8-sig")


def build_import_template_csv():
    return _csv_bytes(
        [
            IMPORT_FIELDS,
            (
                "2026-09-14T09:00:00+08:00",
                "PUBLIC",
                "PUB-IMPORT-001",
                "模拟公众客户001",
                "138****8001",
                "融合套餐",
                "东区",
                "10000号",
                "宽带中断",
                "HIGH",
                "宽带中断模拟申告",
                "模拟客户反馈宽带中断，请尽快核查。",
            ),
            (
                "2026-09-14T09:05:00+08:00",
                "ENTERPRISE",
                "ENT-IMPORT-001",
                "模拟政企客户001",
                "010-****0001",
                "政企专线",
                "南区",
                "客户经理",
                "专线质量",
                "CRITICAL",
                "专线质量模拟申告",
                "模拟政企客户反馈专线质量异常，请启动协同处置。",
            ),
        ]
    )


def build_complaint_csv(queryset):
    rows = [
        (
            "发生时间",
            "实例编号",
            "客户类型",
            "客户标识",
            "客户名称",
            "脱敏联系方式",
            "客户分群",
            "区域",
            "渠道",
            "申告分类",
            "等级",
            "状态",
            "标题",
            "内容",
            "数据来源",
            "校验状态",
            "校验错误",
        )
    ]
    for row in queryset:
        occurred_at = timezone.localtime(row.occurred_at).isoformat() if row.occurred_at else ""
        rows.append(
            (
                occurred_at,
                row.instance.code,
                row.get_customer_type_display(),
                row.customer_ref,
                row.customer_name,
                row.contact_masked,
                row.customer_segment,
                row.region,
                row.channel,
                row.category,
                row.get_severity_display(),
                row.get_status_display(),
                row.title,
                row.content,
                row.batch.get_source_display(),
                row.get_validation_status_display(),
                "；".join(row.validation_errors),
            )
        )
    return _csv_bytes(rows)


def build_batch_validation_csv(batch):
    rows = [
        (
            "序号",
            *IMPORT_FIELDS,
            "校验状态",
            "校验错误",
        )
    ]
    for row in batch.complaints.order_by("sequence_no"):
        raw = row.raw_data or {}
        rows.append(
            (
                row.sequence_no,
                *(raw.get(field, "") for field in IMPORT_FIELDS),
                row.get_validation_status_display(),
                "；".join(row.validation_errors),
            )
        )
    return _csv_bytes(rows)


def build_process_run_csv(queryset):
    rows = [
        (
            "流程编号",
            "流程名称",
            "预演实例",
            "流程模板",
            "状态",
            "推进方式",
            "当前步骤",
            "已完成步骤",
            "总步骤",
            "进度",
            "阻塞原因",
            "启动时间",
            "完成时间",
            "更新时间",
        )
    ]
    for row in queryset:
        snapshot_steps = (row.template_snapshot or {}).get("steps", [])
        current_step_name = next(
            (
                item.get("name", row.current_step_code)
                for item in snapshot_steps
                if item.get("code") == row.current_step_code
            ),
            row.current_step_code,
        )
        if row.status == "COMPLETED":
            current_step_name = "已全部完成"
        rows.append(
            (
                row.code,
                row.name,
                f"{row.instance.name}（{row.instance.code}）",
                f"{row.template.name} V{row.template.version}",
                row.get_status_display(),
                "自动" if row.auto_advance else "人工",
                current_step_name,
                row.completed_steps,
                row.total_steps,
                f"{row.progress_percent}%",
                row.blocked_reason,
                timezone.localtime(row.started_at).isoformat() if row.started_at else "",
                timezone.localtime(row.completed_at).isoformat() if row.completed_at else "",
                timezone.localtime(row.update_time).isoformat(),
            )
        )
    return _csv_bytes(rows)


def build_data_simulation_csv(queryset):
    rows = [
        (
            "数据批次编号",
            "数据批次名称",
            "预演实例",
            "数据类型",
            "批次版本",
            "发生时间",
            "时序序号",
            "字段编号",
            "字段名称",
            "数值",
            "单位",
            "分布类型",
            "标签",
            "说明",
        )
    ]
    for batch in queryset:
        rules = {item["code"]: item for item in batch.rules_snapshot}
        for point in batch.points.all():
            occurred_at = timezone.localtime(point.occurred_at).isoformat()
            for code, value in point.values.items():
                rule = rules.get(code, {})
                rows.append(
                    (
                        batch.code,
                        batch.name,
                        f"{batch.instance.name}（{batch.instance.code}）",
                        batch.get_kind_display(),
                        batch.version,
                        occurred_at,
                        point.sequence_no,
                        code,
                        rule.get("name", code),
                        value,
                        rule.get("unit", ""),
                        dict(
                            LINEAR="线性趋势",
                            WAVE="周期波动",
                            RANDOM="随机分布",
                            STEP="阶跃变化",
                        ).get(rule.get("distribution"), rule.get("distribution", "")),
                        "、".join(point.tags),
                        point.narrative,
                    )
                )
    return _csv_bytes(rows)


def build_traceback_csv(queryset):
    rows = [
        (
            "回溯编号",
            "回溯名称",
            "预演实例",
            "范围",
            "状态",
            "事件类型",
            "发生时间",
            "标题",
            "摘要",
            "当前状态",
            "引用ID",
            "详情",
        )
    ]
    for traceback in queryset:
        for item in (traceback.snapshot or {}).get("items", []):
            rows.append(
                (
                    traceback.code,
                    traceback.name,
                    f"{traceback.instance.name}（{traceback.instance.code}）",
                    traceback.get_scope_display(),
                    traceback.get_status_display(),
                    item.get("kind_label") or item.get("kind"),
                    item.get("occurred_at", ""),
                    item.get("title", ""),
                    item.get("subtitle", ""),
                    item.get("status", ""),
                    item.get("reference_id", ""),
                    item.get("detail", {}),
                )
            )
    return _csv_bytes(rows)


def build_simulation_record_csv(records):
    rows = [
        (
            "记录类型",
            "执行序次",
            "记录编号",
            "记录名称",
            "预演实例",
            "原始状态",
            "统一结果",
            "进度",
            "结果摘要",
            "明细数量",
            "开始时间",
            "完成时间",
            "耗时秒数",
            "最后更新时间",
        )
    ]
    for record in records:
        rows.append(
            (
                record.get("kind_label", ""),
                record.get("occurrence_no", 0),
                record.get("code", ""),
                record.get("name", ""),
                f"{record.get('instance_name', '')}（{record.get('instance_code', '')}）",
                record.get("status_label", ""),
                record.get("state_label", ""),
                f"{record.get('progress_percent', 0)}%",
                record.get("result_summary", ""),
                record.get("event_count", 0),
                record.get("started_at", ""),
                record.get("completed_at", ""),
                record.get("duration_seconds", 0),
                record.get("update_time", ""),
            )
        )
    return _csv_bytes(rows)
