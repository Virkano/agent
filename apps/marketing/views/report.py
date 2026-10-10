# coding=utf-8
from urllib.parse import quote

from django.http import HttpResponse
from rest_framework.request import Request
from rest_framework.views import APIView

from common import result
from common.auth import TokenAuth
from common.auth.authentication import has_permissions
from common.auth.workspace_permissions import workspace_menu_permissions
from common.constants.permission_constants import PermissionConstants
from common.log.log import log
from common.utils.common import query_params_to_single_dict
from marketing.models import MarketingAnalysisReport, MarketingReportStatus
from marketing.report_exports import EXPORT_CONTENT_TYPES, build_report_export, safe_report_filename
from marketing.serializers import MarketingAnalysisReportService, MarketingReportSubscriptionService


report_permissions = workspace_menu_permissions(PermissionConstants.ANALYSIS_REPORT_READ)


class MarketingAnalysisReportView(APIView):
    authentication_classes = [TokenAuth]

    class Metadata(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*report_permissions)
        def get(self, request: Request, workspace_id: str):
            return result.success(MarketingAnalysisReportService(workspace_id, request.user).metadata())

    class Page(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*report_permissions)
        def get(self, request: Request, workspace_id: str, current_page: int, page_size: int):
            return result.success(
                MarketingAnalysisReportService(workspace_id, request.user).page(
                    current_page,
                    page_size,
                    query_params_to_single_dict(request.query_params),
                )
            )

    class Detail(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*report_permissions)
        def get(self, request: Request, workspace_id: str, report_id: str):
            return result.success(MarketingAnalysisReportService(workspace_id, request.user).get(report_id))

    class Generate(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*report_permissions)
        @log(menu="AI 分析报告", operate="生成分析报告")
        def post(self, request: Request, workspace_id: str):
            return result.success(MarketingAnalysisReportService(workspace_id, request.user).generate(request.data))

    class Retry(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*report_permissions)
        @log(menu="AI 分析报告", operate="重试生成分析报告")
        def post(self, request: Request, workspace_id: str, report_id: str):
            return result.success(MarketingAnalysisReportService(workspace_id, request.user).retry(report_id))

    class Download(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*report_permissions)
        @log(menu="AI 分析报告", operate="下载分析报告")
        def get(self, request: Request, workspace_id: str, report_id: str, export_format: str):
            report = MarketingAnalysisReport.objects.filter(workspace_id=workspace_id, id=report_id).first()
            if report is None:
                return result.error("分析报告不存在")
            if report.status != MarketingReportStatus.SUCCESS:
                return result.error("只有生成成功的报告可以下载")
            if export_format not in EXPORT_CONTENT_TYPES:
                return result.error("不支持的报告格式")
            content = build_report_export(report, export_format)
            filename = safe_report_filename(report, export_format)
            response = HttpResponse(content, content_type=EXPORT_CONTENT_TYPES[export_format])
            response["Content-Disposition"] = f"attachment; filename*=UTF-8''{quote(filename)}"
            return response

    class Template(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*report_permissions)
        def get(self, request: Request, workspace_id: str):
            return result.success(MarketingAnalysisReportService(workspace_id, request.user).list_templates())

        @has_permissions(*report_permissions)
        @log(menu="AI 分析报告", operate="新增报告模板")
        def post(self, request: Request, workspace_id: str):
            return result.success(MarketingAnalysisReportService(workspace_id, request.user).create_template(request.data))

    class TemplateOperate(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*report_permissions)
        @log(menu="AI 分析报告", operate="编辑报告模板")
        def put(self, request: Request, workspace_id: str, template_id: str):
            return result.success(
                MarketingAnalysisReportService(workspace_id, request.user).update_template(template_id, request.data)
            )

        @has_permissions(*report_permissions)
        @log(menu="AI 分析报告", operate="删除报告模板")
        def delete(self, request: Request, workspace_id: str, template_id: str):
            return result.success(
                MarketingAnalysisReportService(workspace_id, request.user).delete_template(template_id)
            )

    class Subscription(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*report_permissions)
        def get(self, request: Request, workspace_id: str):
            return result.success(MarketingReportSubscriptionService(workspace_id, request.user).list())

        @has_permissions(*report_permissions)
        @log(menu="AI 分析报告", operate="新增报告订阅")
        def post(self, request: Request, workspace_id: str):
            return result.success(MarketingReportSubscriptionService(workspace_id, request.user).save(request.data))

    class SubscriptionOperate(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*report_permissions)
        @log(menu="AI 分析报告", operate="编辑报告订阅")
        def put(self, request: Request, workspace_id: str, subscription_id: str):
            return result.success(
                MarketingReportSubscriptionService(workspace_id, request.user).save(request.data, subscription_id)
            )

        @has_permissions(*report_permissions)
        @log(menu="AI 分析报告", operate="删除报告订阅")
        def delete(self, request: Request, workspace_id: str, subscription_id: str):
            return result.success(
                MarketingReportSubscriptionService(workspace_id, request.user).delete(subscription_id)
            )

    class SubscriptionRun(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*report_permissions)
        @log(menu="AI 分析报告", operate="立即执行报告订阅")
        def post(self, request: Request, workspace_id: str, subscription_id: str):
            return result.success(
                MarketingReportSubscriptionService(workspace_id, request.user).run_now(subscription_id)
            )
