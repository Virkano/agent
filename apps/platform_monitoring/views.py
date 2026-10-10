from rest_framework.request import Request
from rest_framework.views import APIView

from common import result
from common.auth import TokenAuth
from common.auth.authentication import has_permissions
from common.auth.workspace_permissions import workspace_menu_permissions
from common.constants.permission_constants import PermissionConstants
from common.log.log import log
from common.utils.common import query_params_to_single_dict

from .serializers import PlatformMonitoringService
from .metric_foundation import MetricFoundationService


PLATFORM_MONITORING_PERMISSIONS = workspace_menu_permissions(
    PermissionConstants.PLATFORM_MONITORING_READ
)
METRIC_OPERATIONS_PERMISSIONS = workspace_menu_permissions(
    PermissionConstants.METRIC_OPERATIONS_READ
)


class PlatformMonitoringView(APIView):
    authentication_classes = [TokenAuth]

    class Dashboard(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*PLATFORM_MONITORING_PERMISSIONS)
        def get(self, request: Request, workspace_id: str):
            return result.success(PlatformMonitoringService(workspace_id, request.user).dashboard())

    class Collect(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*PLATFORM_MONITORING_PERMISSIONS)
        @log(menu="平台监控", operate="采集平台指标")
        def post(self, request: Request, workspace_id: str):
            return result.success(PlatformMonitoringService(workspace_id, request.user).collect())

    class Rule(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*PLATFORM_MONITORING_PERMISSIONS)
        def get(self, request: Request, workspace_id: str):
            return result.success(PlatformMonitoringService(workspace_id, request.user).list_rules())

        @has_permissions(*PLATFORM_MONITORING_PERMISSIONS)
        @log(menu="平台监控", operate="新增监控规则")
        def post(self, request: Request, workspace_id: str):
            return result.success(PlatformMonitoringService(workspace_id, request.user).save_rule(request.data))

    class RuleOperate(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*PLATFORM_MONITORING_PERMISSIONS)
        @log(menu="平台监控", operate="更新监控规则")
        def put(self, request: Request, workspace_id: str, rule_id: str):
            return result.success(
                PlatformMonitoringService(workspace_id, request.user).save_rule(request.data, rule_id)
            )

    class Alert(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*PLATFORM_MONITORING_PERMISSIONS)
        def get(self, request: Request, workspace_id: str):
            params = query_params_to_single_dict(request.query_params)
            return result.success(
                PlatformMonitoringService(workspace_id, request.user).list_alerts(params.get("status", ""))
            )

    class AlertOperate(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*PLATFORM_MONITORING_PERMISSIONS)
        @log(menu="平台监控", operate="处理平台监控告警")
        def post(self, request: Request, workspace_id: str, alert_id: str):
            return result.success(
                PlatformMonitoringService(workspace_id, request.user).operate_alert(
                    alert_id,
                    request.data.get("action", ""),
                )
            )


class MetricFoundationView(APIView):
    authentication_classes = [TokenAuth]

    class Overview(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*METRIC_OPERATIONS_PERMISSIONS)
        def get(self, request: Request, workspace_id: str):
            return result.success(MetricFoundationService(workspace_id, request.user).overview())

    class Analytics(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*METRIC_OPERATIONS_PERMISSIONS)
        def get(self, request: Request, workspace_id: str):
            params = query_params_to_single_dict(request.query_params)
            return result.success(MetricFoundationService(workspace_id, request.user).metric_analytics(params))

    class ObservationDetail(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*METRIC_OPERATIONS_PERMISSIONS)
        def get(self, request: Request, workspace_id: str, observation_id: str):
            return result.success(
                MetricFoundationService(workspace_id, request.user).observation_detail(observation_id)
            )

    class Definition(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*METRIC_OPERATIONS_PERMISSIONS)
        def get(self, request: Request, workspace_id: str):
            return result.success(MetricFoundationService(workspace_id, request.user).list_definitions())

        @has_permissions(*METRIC_OPERATIONS_PERMISSIONS)
        @log(menu="指标预警中心", operate="新增指标定义")
        def post(self, request: Request, workspace_id: str):
            return result.success(MetricFoundationService(workspace_id, request.user).save_definition(request.data))

    class DefinitionOperate(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*METRIC_OPERATIONS_PERMISSIONS)
        @log(menu="指标预警中心", operate="更新指标定义")
        def put(self, request: Request, workspace_id: str, definition_id: str):
            return result.success(
                MetricFoundationService(workspace_id, request.user).save_definition(request.data, definition_id)
            )

    class Source(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*METRIC_OPERATIONS_PERMISSIONS)
        def get(self, request: Request, workspace_id: str):
            return result.success(MetricFoundationService(workspace_id, request.user).list_sources())

        @has_permissions(*METRIC_OPERATIONS_PERMISSIONS)
        @log(menu="指标预警中心", operate="新增指标数据源")
        def post(self, request: Request, workspace_id: str):
            return result.success(MetricFoundationService(workspace_id, request.user).save_source(request.data))

    class SourceOperate(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*METRIC_OPERATIONS_PERMISSIONS)
        @log(menu="指标预警中心", operate="更新指标数据源")
        def put(self, request: Request, workspace_id: str, source_id: str):
            return result.success(
                MetricFoundationService(workspace_id, request.user).save_source(request.data, source_id)
            )

    class Rule(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*METRIC_OPERATIONS_PERMISSIONS)
        def get(self, request: Request, workspace_id: str):
            return result.success(MetricFoundationService(workspace_id, request.user).list_rules())

        @has_permissions(*METRIC_OPERATIONS_PERMISSIONS)
        @log(menu="指标预警中心", operate="新增指标预警规则")
        def post(self, request: Request, workspace_id: str):
            return result.success(MetricFoundationService(workspace_id, request.user).save_rule(request.data))

    class RuleOperate(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*METRIC_OPERATIONS_PERMISSIONS)
        @log(menu="指标预警中心", operate="更新指标预警规则")
        def put(self, request: Request, workspace_id: str, rule_id: str):
            return result.success(
                MetricFoundationService(workspace_id, request.user).save_rule(request.data, rule_id)
            )

    class ImportBatch(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*METRIC_OPERATIONS_PERMISSIONS)
        @log(menu="指标预警中心", operate="导入指标采集批次")
        def post(self, request: Request, workspace_id: str):
            return result.success(MetricFoundationService(workspace_id, request.user).import_batch(request.data))

    class Assignee(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*METRIC_OPERATIONS_PERMISSIONS)
        def get(self, request: Request, workspace_id: str):
            return result.success(MetricFoundationService(workspace_id, request.user).list_assignees())

    class DutyShift(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*METRIC_OPERATIONS_PERMISSIONS)
        def get(self, request: Request, workspace_id: str):
            params = query_params_to_single_dict(request.query_params)
            return result.success(MetricFoundationService(workspace_id, request.user).list_duty_shifts(params))

        @has_permissions(*METRIC_OPERATIONS_PERMISSIONS)
        @log(menu="指标预警中心", operate="新增指标值班班次")
        def post(self, request: Request, workspace_id: str):
            return result.success(MetricFoundationService(workspace_id, request.user).save_duty_shift(request.data))

    class DutyShiftOperate(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*METRIC_OPERATIONS_PERMISSIONS)
        @log(menu="指标预警中心", operate="更新指标值班班次")
        def put(self, request: Request, workspace_id: str, shift_id: str):
            return result.success(
                MetricFoundationService(workspace_id, request.user).save_duty_shift(request.data, shift_id)
            )

    class OrderOperate(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*METRIC_OPERATIONS_PERMISSIONS)
        @log(menu="指标预警中心", operate="处置指标派单")
        def post(self, request: Request, workspace_id: str, order_id: str):
            return result.success(
                MetricFoundationService(workspace_id, request.user).operate_order(
                    order_id,
                    request.data,
                )
            )

    class OrderEvent(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*METRIC_OPERATIONS_PERMISSIONS)
        def get(self, request: Request, workspace_id: str, order_id: str):
            return result.success(
                MetricFoundationService(workspace_id, request.user).list_order_events(order_id)
            )

    class BootstrapDemo(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*METRIC_OPERATIONS_PERMISSIONS)
        @log(menu="指标预警中心", operate="初始化指标演示数据")
        def post(self, request: Request, workspace_id: str):
            return result.success(MetricFoundationService(workspace_id, request.user).bootstrap_demo())
