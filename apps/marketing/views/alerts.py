import csv
from io import StringIO
import urllib.parse

from django.http import HttpResponse
from rest_framework.request import Request
from rest_framework.parsers import MultiPartParser
from rest_framework.views import APIView

from common import result
from common.auth import TokenAuth
from common.auth.authentication import WorkspacePermissionMixin
from common.auth.workspace_permissions import workspace_menu_permissions
from common.constants.permission_constants import PermissionConstants
from common.log.log import log
from common.utils.common import query_params_to_single_dict
from marketing.serializers import MarketingAlertService, MarketingNotificationService


class MarketingOperationsPermissionAPIView(WorkspacePermissionMixin, APIView):
    required_workspace_permissions = workspace_menu_permissions(PermissionConstants.MARKETING_OPERATIONS_READ)


class MarketingAlertView(MarketingOperationsPermissionAPIView):
    authentication_classes = [TokenAuth]

    class Page(MarketingOperationsPermissionAPIView):
        authentication_classes = [TokenAuth]

        def get(self, request: Request, workspace_id: str, current_page: int, page_size: int):
            return result.success(
                MarketingAlertService(workspace_id, request.user).page(
                    current_page,
                    page_size,
                    query_params_to_single_dict(request.query_params),
                )
            )

    class Sync(MarketingOperationsPermissionAPIView):
        authentication_classes = [TokenAuth]

        @log(menu="营销运营监控", operate="同步告警并发送通知")
        def post(self, request: Request, workspace_id: str):
            return result.success(
                MarketingNotificationService(workspace_id, request.user).sync_and_notify(request.data)
            )

    class Handle(MarketingOperationsPermissionAPIView):
        authentication_classes = [TokenAuth]

        @log(menu="营销运营监控", operate="处理营销告警")
        def post(self, request: Request, workspace_id: str, alert_id: str):
            data = MarketingAlertService(workspace_id, request.user).handle(alert_id, request.data)
            MarketingNotificationService(workspace_id, request.user).dispatch()
            return result.success(data)

    class Collaborate(MarketingOperationsPermissionAPIView):
        authentication_classes = [TokenAuth]

        @log(menu="营销运营监控", operate="协同处理营销告警")
        def post(self, request: Request, workspace_id: str, alert_id: str):
            data = MarketingAlertService(workspace_id, request.user).collaborate(alert_id, request.data)
            MarketingNotificationService(workspace_id, request.user).dispatch()
            return result.success(data)

    class Subscriber(MarketingOperationsPermissionAPIView):
        authentication_classes = [TokenAuth]

        @log(menu="营销运营监控", operate="更新告警订阅人")
        def post(self, request: Request, workspace_id: str, alert_id: str):
            data = MarketingAlertService(workspace_id, request.user).update_subscriber(alert_id, request.data)
            MarketingNotificationService(workspace_id, request.user).dispatch()
            return result.success(data)

    class Attachment(MarketingOperationsPermissionAPIView):
        authentication_classes = [TokenAuth]
        parser_classes = [MultiPartParser]

        @log(menu="营销运营监控", operate="上传告警附件")
        def post(self, request: Request, workspace_id: str, alert_id: str):
            data = MarketingAlertService(workspace_id, request.user).upload_attachment(
                alert_id,
                request.FILES.get("file"),
            )
            MarketingNotificationService(workspace_id, request.user).dispatch()
            return result.success(data)

    class AttachmentDownload(MarketingOperationsPermissionAPIView):
        authentication_classes = [TokenAuth]

        @log(menu="营销运营监控", operate="下载告警附件")
        def get(self, request: Request, workspace_id: str, alert_id: str, attachment_id: str):
            attachment, stored_file = MarketingAlertService(workspace_id, request.user).attachment_file(
                alert_id,
                attachment_id,
            )
            encoded_name = urllib.parse.quote(attachment.file_name)
            return HttpResponse(
                stored_file.get_bytes(),
                status=200,
                headers={
                    "Content-Type": attachment.content_type,
                    "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_name}",
                },
            )

    class Detail(MarketingOperationsPermissionAPIView):
        authentication_classes = [TokenAuth]

        def get(self, request: Request, workspace_id: str, alert_id: str):
            return result.success(MarketingAlertService(workspace_id, request.user).get(alert_id))

    class Rules(MarketingOperationsPermissionAPIView):
        authentication_classes = [TokenAuth]

        def get(self, request: Request, workspace_id: str):
            return result.success(MarketingAlertService(workspace_id, request.user).rules())

    class Members(MarketingOperationsPermissionAPIView):
        authentication_classes = [TokenAuth]

        def get(self, request: Request, workspace_id: str):
            return result.success(MarketingAlertService(workspace_id, request.user).members())

    class Performance(MarketingOperationsPermissionAPIView):
        authentication_classes = [TokenAuth]

        def get(self, request: Request, workspace_id: str):
            return result.success(
                MarketingAlertService(workspace_id, request.user).performance(
                    query_params_to_single_dict(request.query_params)
                )
            )

    class Retrospective(MarketingOperationsPermissionAPIView):
        authentication_classes = [TokenAuth]

        def get(self, request: Request, workspace_id: str):
            return result.success(
                MarketingAlertService(workspace_id, request.user).retrospective(
                    query_params_to_single_dict(request.query_params)
                )
            )

    class NoiseAnalysis(MarketingOperationsPermissionAPIView):
        authentication_classes = [TokenAuth]

        def get(self, request: Request, workspace_id: str):
            return result.success(
                MarketingAlertService(workspace_id, request.user).noise_analysis(
                    query_params_to_single_dict(request.query_params)
                )
            )

    class RuleEffect(MarketingOperationsPermissionAPIView):
        authentication_classes = [TokenAuth]

        def get(self, request: Request, workspace_id: str):
            return result.success(
                MarketingAlertService(workspace_id, request.user).rule_effect(
                    query_params_to_single_dict(request.query_params)
                )
            )

    class RetrospectiveExport(MarketingOperationsPermissionAPIView):
        authentication_classes = [TokenAuth]

        @log(menu="营销运营监控", operate="导出告警复盘")
        def get(self, request: Request, workspace_id: str):
            rows = MarketingAlertService(workspace_id, request.user).retrospective_export_rows(
                query_params_to_single_dict(request.query_params)
            )
            output = StringIO()
            writer = csv.writer(output)
            writer.writerow(
                [
                    "告警标题",
                    "告警类型",
                    "级别",
                    "负责人",
                    "根因分类",
                    "处置方式",
                    "影响范围",
                    "处理结论",
                    "首次触发时间",
                    "关闭时间",
                    "处理时长（秒）",
                ]
            )
            for row in rows:
                writer.writerow(
                    [
                        row["title"],
                        row["alert_type"],
                        row["severity"],
                        row["assignee_name"],
                        row["root_cause"],
                        row["resolution_type"],
                        row["impact_scope"],
                        row["close_note"],
                        row["first_triggered_at"].isoformat() if row["first_triggered_at"] else "",
                        row["closed_at"].isoformat() if row["closed_at"] else "",
                        row["resolution_seconds"],
                    ]
                )
            return HttpResponse(
                output.getvalue().encode("utf-8-sig"),
                content_type="text/csv; charset=utf-8",
                headers={"Content-Disposition": "attachment; filename=marketing-alert-retrospective.csv"},
            )

    class RuleOperate(MarketingOperationsPermissionAPIView):
        authentication_classes = [TokenAuth]

        @log(menu="营销运营监控", operate="更新告警规则")
        def put(self, request: Request, workspace_id: str, rule_id: str):
            return result.success(
                MarketingAlertService(workspace_id, request.user).update_rule(rule_id, request.data)
            )

    class RuleRollback(MarketingOperationsPermissionAPIView):
        authentication_classes = [TokenAuth]

        @log(menu="营销运营监控", operate="回滚告警规则")
        def post(self, request: Request, workspace_id: str, rule_id: str):
            return result.success(
                MarketingAlertService(workspace_id, request.user).rollback_rule(rule_id, request.data)
            )
