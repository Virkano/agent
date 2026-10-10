# coding=utf-8
import csv
from io import BytesIO, StringIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from django.utils import timezone

from marketing.report_exports import REPORT_FONT_NAME, REPORT_FONT_PATH


CHANGE_QUALITY_EXPORT_CONTENT_TYPES = {
    "csv": "text/csv; charset=utf-8",
    "pdf": "application/pdf",
}

METRIC_LABELS = (
    ("operation_count", "变更操作数"),
    ("evaluated_count", "已评估数"),
    ("green_count", "绿灯数"),
    ("yellow_count", "黄灯数"),
    ("red_count", "红灯数"),
    ("approved_count", "风险放行数"),
    ("rejected_count", "风险驳回数"),
    ("pending_confirmation_count", "待人工确认数"),
    ("in_progress_count", "执行中数"),
    ("completed_count", "已完成数"),
    ("aborted_count", "已终止数"),
    ("communication_count", "提醒与告知数"),
    ("sent_communication_count", "已发送通信数"),
    ("acknowledged_communication_count", "已确认通信数"),
    ("failed_communication_count", "失败通信数"),
    ("communication_coverage_rate", "通信覆盖率(%)"),
    ("control_completion_rate", "执行完成率(%)"),
    ("average_confirmation_seconds", "平均人工确认耗时(秒)"),
)


def safe_change_quality_filename(report, extension):
    safe_title = "".join(char if char.isalnum() or char in "-_" else "_" for char in report.title).strip("_")
    return f"{safe_title[:80] or 'change-quality-report'}.{extension}"


def build_change_quality_csv(report):
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow([report.title])
    writer.writerow(["统计周期", report.period_start.isoformat(), report.period_end.isoformat()])
    writer.writerow([])
    writer.writerow(["指标", "结果"])
    for key, label in METRIC_LABELS:
        writer.writerow([label, (report.metrics or {}).get(key, 0)])
    writer.writerow([])
    writer.writerow(["日期", "变更数", "红灯数", "提醒告知数", "完成数"])
    for item in report.daily_trend or []:
        writer.writerow(
            [
                item["date"],
                item["operation_count"],
                item["red_count"],
                item["communication_count"],
                item["completed_count"],
            ]
        )
    writer.writerow([])
    writer.writerow(["日期", "变更编号", "变更名称", "风险", "风险分", "风险状态", "管控状态", "提醒告知数"])
    for item in report.operation_snapshot or []:
        writer.writerow(
            [
                item["date"],
                item["code"],
                item["name"],
                item["risk_level_label"],
                item["risk_score"],
                item["status_label"],
                item["control_status_label"],
                item["communication_count"],
            ]
        )
    return output.getvalue().encode("utf-8-sig")


def _table_style():
    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DDEDEC")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#123638")),
            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CAD5D4")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F6F9F8")]),
        ]
    )


def build_change_quality_pdf(report):
    if REPORT_FONT_NAME not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(REPORT_FONT_NAME, REPORT_FONT_PATH))
    output = BytesIO()
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ChangeQualityTitle",
        parent=styles["Title"],
        fontName=REPORT_FONT_NAME,
        fontSize=20,
        leading=28,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#13202D"),
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "ChangeQualityBody",
        parent=styles["BodyText"],
        fontName=REPORT_FONT_NAME,
        fontSize=9,
        leading=14,
        textColor=colors.HexColor("#34434A"),
    )
    heading_style = ParagraphStyle(
        "ChangeQualityHeading",
        parent=body_style,
        fontSize=13,
        leading=20,
        spaceBefore=10,
        spaceAfter=6,
        textColor=colors.HexColor("#0D6D70"),
    )

    def paragraph(value):
        return Paragraph(str(value), body_style)

    def draw_page(canvas, document):
        canvas.saveState()
        canvas.setFont(REPORT_FONT_NAME, 8)
        canvas.setFillColor(colors.HexColor("#6B777B"))
        canvas.drawString(22 * mm, 12 * mm, "变更操作质量周期报告")
        canvas.drawRightString(A4[0] - 22 * mm, 12 * mm, f"第 {document.page} 页")
        canvas.restoreState()

    doc = SimpleDocTemplate(
        output,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=20 * mm,
        title=report.title,
        author="电信智能体变更操作中心",
    )
    generated_at = timezone.localtime(report.generated_at)
    story = [
        Paragraph(report.title, title_style),
        Paragraph(
            f"统计周期：{report.period_start.isoformat()} 至 {report.period_end.isoformat()}　生成时间：{generated_at:%Y-%m-%d %H:%M}",
            body_style,
        ),
        Spacer(1, 6 * mm),
        Paragraph("核心质量指标", heading_style),
    ]
    metric_data = [[paragraph("指标"), paragraph("结果")]]
    metric_data.extend(
        [[paragraph(label), paragraph((report.metrics or {}).get(key, 0))] for key, label in METRIC_LABELS]
    )
    metric_table = Table(metric_data, colWidths=[105 * mm, 45 * mm], repeatRows=1)
    metric_table.setStyle(_table_style())
    story.append(metric_table)

    active_days = [
        item
        for item in report.daily_trend or []
        if item["operation_count"] or item["communication_count"] or item["completed_count"]
    ]
    story.append(Paragraph("时间趋势与下钻索引", heading_style))
    if active_days:
        trend_data = [[paragraph(value) for value in ("日期", "变更", "红灯", "提醒告知", "完成")]]
        trend_data.extend(
            [
                paragraph(item["date"]),
                paragraph(item["operation_count"]),
                paragraph(item["red_count"]),
                paragraph(item["communication_count"]),
                paragraph(item["completed_count"]),
            ]
            for item in active_days
        )
        trend_table = Table(trend_data, colWidths=[42 * mm, 27 * mm, 27 * mm, 32 * mm, 27 * mm], repeatRows=1)
        trend_table.setStyle(_table_style())
        story.append(trend_table)
    else:
        story.append(Paragraph("本周期暂无变更或通信活动。", body_style))

    story.append(Paragraph("变更操作明细", heading_style))
    if report.operation_snapshot:
        operation_data = [
            [paragraph(value) for value in ("日期", "编号 / 名称", "风险", "业务状态", "管控状态", "提醒")]
        ]
        operation_data.extend(
            [
                paragraph(item["date"]),
                paragraph(f"{item['code']}<br/>{item['name']}"),
                paragraph(f"{item['risk_level_label']} / {item['risk_score']}"),
                paragraph(item["status_label"]),
                paragraph(item["control_status_label"]),
                paragraph(item["communication_count"]),
            ]
            for item in report.operation_snapshot
        )
        operation_table = Table(
            operation_data,
            colWidths=[28 * mm, 52 * mm, 24 * mm, 28 * mm, 27 * mm, 14 * mm],
            repeatRows=1,
        )
        operation_table.setStyle(_table_style())
        story.append(operation_table)
    else:
        story.append(Paragraph("本周期暂无变更操作。", body_style))
    doc.build(story, onFirstPage=draw_page, onLaterPages=draw_page)
    return output.getvalue()


def build_change_quality_export(report, export_format):
    if export_format == "csv":
        return build_change_quality_csv(report)
    if export_format == "pdf":
        return build_change_quality_pdf(report)
    raise ValueError("不支持的变更质量报告格式")
