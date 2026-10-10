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
from marketing.change_quality_exports import (
    CHANGE_QUALITY_EXPORT_CONTENT_TYPES,
    build_change_quality_export,
    safe_change_quality_filename,
)
from marketing.serializers import (
    ChangeOperationControlService,
    ChangeOperationRiskService,
    IvrProtocolSimulatorService,
)


ivr_permissions = workspace_menu_permissions(PermissionConstants.IVR_SIMULATOR_READ)


class IvrProtocolSimulatorView:
    class Dashboard(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*ivr_permissions)
        def get(self, request: Request, workspace_id: str):
            return result.success(IvrProtocolSimulatorService(workspace_id, request.user).dashboard())

    class Protocol(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*ivr_permissions)
        def get(self, request: Request, workspace_id: str):
            return result.success(IvrProtocolSimulatorService(workspace_id, request.user).protocol())

    class Session(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*ivr_permissions)
        @log(menu="IVR 与变更控制", operate="创建 IVR 会话")
        def post(self, request: Request, workspace_id: str):
            return result.success(IvrProtocolSimulatorService(workspace_id, request.user).create_session(request.data))

    class SessionDetail(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*ivr_permissions)
        def get(self, request: Request, workspace_id: str, session_id: str):
            return result.success(IvrProtocolSimulatorService(workspace_id, request.user).get(session_id))

    class AudioChunk(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*ivr_permissions)
        @log(menu="IVR 与变更控制", operate="处理 IVR 音频分片")
        def post(self, request: Request, workspace_id: str, session_id: str):
            return result.success(
                IvrProtocolSimulatorService(workspace_id, request.user).process_audio(session_id, request.data)
            )

    class StateEvent(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*ivr_permissions)
        @log(menu="IVR 与变更控制", operate="记录 IVR 状态事件")
        def post(self, request: Request, workspace_id: str, session_id: str):
            return result.success(
                IvrProtocolSimulatorService(workspace_id, request.user).record_event(session_id, request.data)
            )


class ChangeOperationRiskView:
    class Dashboard(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*ivr_permissions)
        def get(self, request: Request, workspace_id: str):
            return result.success(ChangeOperationRiskService(workspace_id, request.user).dashboard())

    class Operation(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*ivr_permissions)
        @log(menu="IVR 与变更控制", operate="新增变更操作")
        def post(self, request: Request, workspace_id: str):
            return result.success(ChangeOperationRiskService(workspace_id, request.user).create(request.data))

    class Detail(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*ivr_permissions)
        def get(self, request: Request, workspace_id: str, operation_id: str):
            return result.success(ChangeOperationRiskService(workspace_id, request.user).detail(operation_id))

    class Evaluate(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*ivr_permissions)
        @log(menu="IVR 与变更控制", operate="执行变更风险评估")
        def post(self, request: Request, workspace_id: str, operation_id: str):
            return result.success(
                ChangeOperationRiskService(workspace_id, request.user).evaluate(operation_id, request.data)
            )

    class Confirm(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*ivr_permissions)
        @log(menu="IVR 与变更控制", operate="确认高风险变更")
        def post(self, request: Request, workspace_id: str, operation_id: str):
            return result.success(
                ChangeOperationRiskService(workspace_id, request.user).confirm(operation_id, request.data)
            )


class ChangeOperationControlView:
    class Dashboard(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*ivr_permissions)
        def get(self, request: Request, workspace_id: str):
            return result.success(ChangeOperationControlService(workspace_id, request.user).dashboard())

    class Detail(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*ivr_permissions)
        def get(self, request: Request, workspace_id: str, operation_id: str):
            return result.success(ChangeOperationControlService(workspace_id, request.user).detail(operation_id))

    class Communication(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*ivr_permissions)
        @log(menu="IVR 与变更控制", operate="创建变更通信")
        def post(self, request: Request, workspace_id: str, operation_id: str):
            return result.success(
                ChangeOperationControlService(workspace_id, request.user).create_communication(
                    operation_id, request.data
                )
            )

    class CommunicationStatus(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*ivr_permissions)
        @log(menu="IVR 与变更控制", operate="更新变更通信状态")
        def post(self, request: Request, workspace_id: str, communication_id: str):
            return result.success(
                ChangeOperationControlService(workspace_id, request.user).update_communication_status(
                    communication_id, request.data
                )
            )

    class Control(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*ivr_permissions)
        @log(menu="IVR 与变更控制", operate="执行变更控制动作")
        def post(self, request: Request, workspace_id: str, operation_id: str):
            return result.success(
                ChangeOperationControlService(workspace_id, request.user).control(operation_id, request.data)
            )

    class QualityReport(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*ivr_permissions)
        @log(menu="IVR 与变更控制", operate="生成变更质量报告")
        def post(self, request: Request, workspace_id: str):
            return result.success(
                ChangeOperationControlService(workspace_id, request.user).generate_report(request.data)
            )

    class QualityReportDetail(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*ivr_permissions)
        def get(self, request: Request, workspace_id: str, report_id: str):
            return result.success(ChangeOperationControlService(workspace_id, request.user).report_detail(report_id))

    class QualityReportDrilldown(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*ivr_permissions)
        def get(self, request: Request, workspace_id: str, report_id: str):
            return result.success(
                ChangeOperationControlService(workspace_id, request.user).report_drilldown(
                    report_id, request.query_params.get("date", "")
                )
            )

    class QualityReportExport(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*ivr_permissions)
        @log(menu="IVR 与变更控制", operate="导出变更质量报告")
        def get(self, request: Request, workspace_id: str, report_id: str, export_format: str):
            if export_format not in CHANGE_QUALITY_EXPORT_CONTENT_TYPES:
                return result.error("仅支持 CSV 或 PDF 导出")
            report = ChangeOperationControlService(workspace_id, request.user).get_report(report_id)
            content = build_change_quality_export(report, export_format)
            filename = safe_change_quality_filename(report, export_format)
            response = HttpResponse(content, content_type=CHANGE_QUALITY_EXPORT_CONTENT_TYPES[export_format])
            response["Content-Disposition"] = f"attachment; filename*=UTF-8''{quote(filename)}"
            return response
