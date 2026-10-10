from django.http import HttpResponse
from rest_framework.request import Request
from rest_framework.views import APIView

from common import result
from common.auth import TokenAuth
from common.auth.authentication import has_permissions
from common.auth.workspace_permissions import workspace_menu_permissions
from common.constants.permission_constants import PermissionConstants
from common.exception.app_exception import AppApiException
from common.log.log import log
from common.utils.common import query_params_to_single_dict

from .auxiliary_exports import (
    AUXILIARY_EXPORT_CONTENT_TYPES,
    auxiliary_export_filename,
    build_auxiliary_export,
)
from .exports import (
    build_batch_validation_csv,
    build_complaint_csv,
    build_data_simulation_csv,
    build_import_template_csv,
    build_process_run_csv,
    build_simulation_record_csv,
    build_traceback_csv,
)
from .serializers import RehearsalService


REHEARSAL_READ_PERMISSIONS = workspace_menu_permissions(PermissionConstants.REHEARSAL_READ)
REHEARSAL_WRITE_PERMISSIONS = REHEARSAL_READ_PERMISSIONS


def _csv_response(content, filename):
    response = HttpResponse(content, content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


def _attachment_response(content, filename, content_type):
    response = HttpResponse(content, content_type=content_type)
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


class RehearsalView(APIView):
    authentication_classes = [TokenAuth]

    class Dashboard(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_READ_PERMISSIONS)
        def get(self, request: Request, workspace_id: str):
            return result.success(RehearsalService(workspace_id, request.user).dashboard())

    class Scenario(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_WRITE_PERMISSIONS)
        @log(menu="故障与场景预演", operate="新增演练场景")
        def post(self, request: Request, workspace_id: str):
            return result.success(RehearsalService(workspace_id, request.user).create_scenario(request.data))

    class Instance(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_WRITE_PERMISSIONS)
        @log(menu="故障与场景预演", operate="创建演练实例")
        def post(self, request: Request, workspace_id: str):
            return result.success(RehearsalService(workspace_id, request.user).create_instance(request.data))

    class InstanceDetail(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_READ_PERMISSIONS)
        def get(self, request: Request, workspace_id: str, instance_id: str):
            return result.success(RehearsalService(workspace_id, request.user).instance_detail(instance_id))

    class InstanceOperate(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_WRITE_PERMISSIONS)
        @log(menu="故障与场景预演", operate="操作演练实例")
        def post(self, request: Request, workspace_id: str, instance_id: str):
            return result.success(
                RehearsalService(workspace_id, request.user).operate_instance(instance_id, request.data)
            )

    class GenerateComplaints(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_WRITE_PERMISSIONS)
        @log(menu="故障与场景预演", operate="生成模拟投诉数据")
        def post(self, request: Request, workspace_id: str, instance_id: str):
            return result.success(
                RehearsalService(workspace_id, request.user).generate_complaints(instance_id, request.data)
            )

    class ImportComplaints(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_WRITE_PERMISSIONS)
        @log(menu="故障与场景预演", operate="导入模拟投诉数据")
        def post(self, request: Request, workspace_id: str, instance_id: str):
            return result.success(
                RehearsalService(workspace_id, request.user).import_complaints(
                    instance_id,
                    request.data.get("request_id", ""),
                    request.FILES.get("file"),
                )
            )

    class Complaints(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_READ_PERMISSIONS)
        def get(self, request: Request, workspace_id: str):
            params = query_params_to_single_dict(request.query_params)
            return result.success(RehearsalService(workspace_id, request.user).list_complaints(params))

    class ComplaintExport(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_READ_PERMISSIONS)
        @log(menu="故障与场景预演", operate="导出演练投诉数据")
        def get(self, request: Request, workspace_id: str):
            params = query_params_to_single_dict(request.query_params)
            queryset = RehearsalService(workspace_id, request.user).complaint_queryset(params)
            return _csv_response(build_complaint_csv(queryset), "rehearsal-complaints.csv")

    class ImportTemplate(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_READ_PERMISSIONS)
        @log(menu="故障与场景预演", operate="下载投诉导入模板")
        def get(self, request: Request, workspace_id: str):
            return _csv_response(build_import_template_csv(), "rehearsal-complaint-import-template.csv")

    class BatchValidationExport(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_READ_PERMISSIONS)
        @log(menu="故障与场景预演", operate="导出批次校验结果")
        def get(self, request: Request, workspace_id: str, batch_id: str):
            service = RehearsalService(workspace_id, request.user)
            batch = service._get_batch(batch_id)
            return _csv_response(build_batch_validation_csv(batch), f"rehearsal-batch-{batch.version}-validation.csv")

    class ProcessTemplate(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_WRITE_PERMISSIONS)
        @log(menu="故障与场景预演", operate="新增处置流程模板")
        def post(self, request: Request, workspace_id: str):
            return result.success(RehearsalService(workspace_id, request.user).create_process_template(request.data))

    class ProcessRun(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_READ_PERMISSIONS)
        def get(self, request: Request, workspace_id: str):
            params = query_params_to_single_dict(request.query_params)
            return result.success(RehearsalService(workspace_id, request.user).list_process_runs(params))

    class ProcessRunCreate(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_WRITE_PERMISSIONS)
        @log(menu="故障与场景预演", operate="生成处置流程")
        def post(self, request: Request, workspace_id: str, instance_id: str):
            return result.success(
                RehearsalService(workspace_id, request.user).create_process_run(instance_id, request.data)
            )

    class ProcessRunDetail(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_READ_PERMISSIONS)
        def get(self, request: Request, workspace_id: str, run_id: str):
            return result.success(RehearsalService(workspace_id, request.user).process_run_detail(run_id))

    class ProcessRunOperate(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_WRITE_PERMISSIONS)
        @log(menu="故障与场景预演", operate="操作处置流程")
        def post(self, request: Request, workspace_id: str, run_id: str):
            return result.success(
                RehearsalService(workspace_id, request.user).operate_process_run(run_id, request.data)
            )

    class ProcessRunExport(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_READ_PERMISSIONS)
        @log(menu="故障与场景预演", operate="导出处置流程")
        def get(self, request: Request, workspace_id: str):
            params = query_params_to_single_dict(request.query_params)
            queryset = RehearsalService(workspace_id, request.user).process_run_queryset(params)
            return _csv_response(build_process_run_csv(queryset), "rehearsal-process-runs.csv")

    class DataTemplate(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_WRITE_PERMISSIONS)
        @log(menu="故障与场景预演", operate="新增模拟数据模板")
        def post(self, request: Request, workspace_id: str):
            return result.success(RehearsalService(workspace_id, request.user).create_data_template(request.data))

    class DataBatch(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_READ_PERMISSIONS)
        def get(self, request: Request, workspace_id: str):
            params = query_params_to_single_dict(request.query_params)
            return result.success(RehearsalService(workspace_id, request.user).list_data_batches(params))

    class DataBatchGenerate(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_WRITE_PERMISSIONS)
        @log(menu="故障与场景预演", operate="生成模拟数据")
        def post(self, request: Request, workspace_id: str, instance_id: str):
            return result.success(
                RehearsalService(workspace_id, request.user).generate_simulation_data(instance_id, request.data)
            )

    class DataBatchDetail(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_READ_PERMISSIONS)
        def get(self, request: Request, workspace_id: str, batch_id: str):
            return result.success(RehearsalService(workspace_id, request.user).data_batch_detail(batch_id))

    class DataModel(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_READ_PERMISSIONS)
        def get(self, request: Request, workspace_id: str):
            params = query_params_to_single_dict(request.query_params)
            return result.success(RehearsalService(workspace_id, request.user).list_data_models(params))

    class DataModelCreate(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_WRITE_PERMISSIONS)
        @log(menu="故障与场景预演", operate="创建演练数据模型")
        def post(self, request: Request, workspace_id: str, instance_id: str):
            return result.success(RehearsalService(workspace_id, request.user).create_data_model(instance_id, request.data))

    class DataModelDetail(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_READ_PERMISSIONS)
        def get(self, request: Request, workspace_id: str, model_id: str):
            return result.success(RehearsalService(workspace_id, request.user).data_model_detail(model_id))

    class DataModelLoad(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_WRITE_PERMISSIONS)
        @log(menu="故障与场景预演", operate="加载演练数据模型")
        def post(self, request: Request, workspace_id: str, model_id: str):
            return result.success(RehearsalService(workspace_id, request.user).load_data_model(model_id, request.data))

    class Traceback(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_READ_PERMISSIONS)
        def get(self, request: Request, workspace_id: str):
            params = query_params_to_single_dict(request.query_params)
            return result.success(RehearsalService(workspace_id, request.user).list_tracebacks(params))

    class TracebackCreate(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_WRITE_PERMISSIONS)
        @log(menu="故障与场景预演", operate="创建动态回溯快照")
        def post(self, request: Request, workspace_id: str, instance_id: str):
            return result.success(RehearsalService(workspace_id, request.user).create_traceback(instance_id, request.data))

    class TracebackDetail(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_READ_PERMISSIONS)
        def get(self, request: Request, workspace_id: str, traceback_id: str):
            return result.success(RehearsalService(workspace_id, request.user).traceback_detail(traceback_id))

    class TracebackExport(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_READ_PERMISSIONS)
        @log(menu="故障与场景预演", operate="导出动态回溯")
        def get(self, request: Request, workspace_id: str):
            params = query_params_to_single_dict(request.query_params)
            queryset = RehearsalService(workspace_id, request.user).traceback_queryset(params)
            return _csv_response(build_traceback_csv(queryset), "rehearsal-tracebacks.csv")

    class SimulationRecord(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_READ_PERMISSIONS)
        def get(self, request: Request, workspace_id: str):
            params = query_params_to_single_dict(request.query_params)
            return result.success(RehearsalService(workspace_id, request.user).list_simulation_records(params))

    class SimulationRecordDetail(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_READ_PERMISSIONS)
        def get(self, request: Request, workspace_id: str, kind: str, record_id: str):
            return result.success(
                RehearsalService(workspace_id, request.user).simulation_record_detail(kind, record_id)
            )

    class SimulationRecordExport(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_READ_PERMISSIONS)
        @log(menu="故障与场景预演", operate="导出模拟记录")
        def get(self, request: Request, workspace_id: str):
            params = query_params_to_single_dict(request.query_params)
            records = RehearsalService(workspace_id, request.user).simulation_records(params)
            for record in records:
                record.pop("_sort_at", None)
            return _csv_response(build_simulation_record_csv(records), "rehearsal-simulation-records.csv")

    class CapabilityMock(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_READ_PERMISSIONS)
        def get(self, request: Request, workspace_id: str):
            params = query_params_to_single_dict(request.query_params)
            return result.success(RehearsalService(workspace_id, request.user).list_capability_mocks(params))

        @has_permissions(*REHEARSAL_WRITE_PERMISSIONS)
        @log(menu="故障与场景预演", operate="新增能力模拟配置")
        def post(self, request: Request, workspace_id: str):
            return result.success(RehearsalService(workspace_id, request.user).create_capability_mock(request.data))

    class CapabilityCall(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_READ_PERMISSIONS)
        def get(self, request: Request, workspace_id: str):
            params = query_params_to_single_dict(request.query_params)
            return result.success(RehearsalService(workspace_id, request.user).list_capability_calls(params))

    class CapabilityCallInvoke(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_WRITE_PERMISSIONS)
        @log(menu="故障与场景预演", operate="调用能力模拟")
        def post(self, request: Request, workspace_id: str, instance_id: str):
            return result.success(
                RehearsalService(workspace_id, request.user).invoke_capability(instance_id, request.data)
            )

    class CapabilityCallDetail(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_READ_PERMISSIONS)
        def get(self, request: Request, workspace_id: str, call_id: str):
            return result.success(RehearsalService(workspace_id, request.user).capability_call_detail(call_id))

    class CapabilityCallReplay(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_WRITE_PERMISSIONS)
        @log(menu="故障与场景预演", operate="重放能力调用")
        def post(self, request: Request, workspace_id: str, call_id: str):
            return result.success(
                RehearsalService(workspace_id, request.user).replay_capability_call(call_id, request.data)
            )

    class FaultConfiguration(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_READ_PERMISSIONS)
        def get(self, request: Request, workspace_id: str):
            params = query_params_to_single_dict(request.query_params)
            return result.success(
                RehearsalService(workspace_id, request.user).list_fault_configurations(params)
            )

        @has_permissions(*REHEARSAL_WRITE_PERMISSIONS)
        @log(menu="故障与场景预演", operate="新增故障模拟配置")
        def post(self, request: Request, workspace_id: str):
            return result.success(
                RehearsalService(workspace_id, request.user).create_fault_configuration(request.data)
            )

    class FaultConfigurationDetail(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_READ_PERMISSIONS)
        def get(self, request: Request, workspace_id: str, configuration_id: str):
            return result.success(
                RehearsalService(workspace_id, request.user).fault_configuration_detail(configuration_id)
            )

    class FaultConfigurationClone(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_WRITE_PERMISSIONS)
        @log(menu="故障与场景预演", operate="复制故障模拟配置")
        def post(self, request: Request, workspace_id: str, configuration_id: str):
            return result.success(
                RehearsalService(workspace_id, request.user).clone_fault_configuration(
                    configuration_id, request.data
                )
            )

    class FaultConfigurationValidate(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_WRITE_PERMISSIONS)
        @log(menu="故障与场景预演", operate="校验故障模拟配置")
        def post(self, request: Request, workspace_id: str, configuration_id: str):
            return result.success(
                RehearsalService(workspace_id, request.user).validate_fault_configuration(
                    configuration_id, request.data
                )
            )

    class FaultConfigurationArchive(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_WRITE_PERMISSIONS)
        @log(menu="故障与场景预演", operate="归档故障模拟配置")
        def post(self, request: Request, workspace_id: str, configuration_id: str):
            return result.success(
                RehearsalService(workspace_id, request.user).archive_fault_configuration(
                    configuration_id, request.data
                )
            )

    class FaultConfigurationApply(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_WRITE_PERMISSIONS)
        @log(menu="故障与场景预演", operate="应用故障模拟配置")
        def post(self, request: Request, workspace_id: str, instance_id: str):
            return result.success(
                RehearsalService(workspace_id, request.user).apply_fault_configuration(
                    instance_id, request.data
                )
            )

    class SceneReplay(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_READ_PERMISSIONS)
        def get(self, request: Request, workspace_id: str):
            params = query_params_to_single_dict(request.query_params)
            return result.success(RehearsalService(workspace_id, request.user).list_scene_replays(params))

    class SceneReplayCreate(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_WRITE_PERMISSIONS)
        @log(menu="故障与场景预演", operate="创建场景动态回溯")
        def post(self, request: Request, workspace_id: str, instance_id: str):
            return result.success(
                RehearsalService(workspace_id, request.user).create_scene_replay(instance_id, request.data)
            )

    class SceneReplayDetail(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_READ_PERMISSIONS)
        def get(self, request: Request, workspace_id: str, replay_id: str):
            return result.success(RehearsalService(workspace_id, request.user).scene_replay_detail(replay_id))

    class FaultReportTemplate(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_READ_PERMISSIONS)
        def get(self, request: Request, workspace_id: str):
            params = query_params_to_single_dict(request.query_params)
            return result.success(
                RehearsalService(workspace_id, request.user).list_fault_report_templates(params)
            )

        @has_permissions(*REHEARSAL_WRITE_PERMISSIONS)
        @log(menu="故障与场景预演", operate="新增故障上报模板")
        def post(self, request: Request, workspace_id: str):
            return result.success(
                RehearsalService(workspace_id, request.user).create_fault_report_template(request.data)
            )

    class FaultReport(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_READ_PERMISSIONS)
        def get(self, request: Request, workspace_id: str):
            params = query_params_to_single_dict(request.query_params)
            return result.success(RehearsalService(workspace_id, request.user).list_fault_reports(params))

    class FaultReportCreate(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_WRITE_PERMISSIONS)
        @log(menu="故障与场景预演", operate="创建故障上报")
        def post(self, request: Request, workspace_id: str, instance_id: str):
            return result.success(
                RehearsalService(workspace_id, request.user).create_fault_report(instance_id, request.data)
            )

    class FaultReportDetail(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_READ_PERMISSIONS)
        def get(self, request: Request, workspace_id: str, report_id: str):
            return result.success(RehearsalService(workspace_id, request.user).fault_report_detail(report_id))

    class FaultReportOperate(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_WRITE_PERMISSIONS)
        @log(menu="故障与场景预演", operate="操作故障上报")
        def post(self, request: Request, workspace_id: str, report_id: str):
            return result.success(
                RehearsalService(workspace_id, request.user).operate_fault_report(report_id, request.data)
            )

    class AuxiliarySimulation(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_READ_PERMISSIONS)
        def get(self, request: Request, workspace_id: str):
            params = query_params_to_single_dict(request.query_params)
            return result.success(
                RehearsalService(workspace_id, request.user).list_auxiliary_simulations(params)
            )

    class AuxiliarySimulationCreate(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_WRITE_PERMISSIONS)
        @log(menu="故障与场景预演", operate="创建辅助随机因素模拟")
        def post(self, request: Request, workspace_id: str, instance_id: str):
            return result.success(
                RehearsalService(workspace_id, request.user).create_auxiliary_simulation(
                    instance_id, request.data
                )
            )

    class AuxiliarySimulationDetail(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_READ_PERMISSIONS)
        def get(self, request: Request, workspace_id: str, simulation_id: str):
            return result.success(
                RehearsalService(workspace_id, request.user).auxiliary_simulation_detail(simulation_id)
            )

    class AuxiliarySimulationExport(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_READ_PERMISSIONS)
        @log(menu="故障与场景预演", operate="导出辅助模拟报告")
        def get(self, request: Request, workspace_id: str, simulation_id: str):
            export_format = str(request.query_params.get("export_format") or "pdf").lower()
            report_level = str(request.query_params.get("report_level") or "summary").lower()
            if export_format not in AUXILIARY_EXPORT_CONTENT_TYPES:
                raise AppApiException(400, "报告格式仅支持 PDF、Excel 或 JSON")
            if report_level not in ("summary", "full"):
                raise AppApiException(400, "报告版本仅支持精简版或完整版")
            service = RehearsalService(workspace_id, request.user)
            simulation = service._get_auxiliary_simulation(simulation_id)
            content = build_auxiliary_export(simulation, export_format, report_level)
            return _attachment_response(
                content,
                auxiliary_export_filename(simulation, export_format, report_level),
                AUXILIARY_EXPORT_CONTENT_TYPES[export_format],
            )

    class DataBatchExport(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_READ_PERMISSIONS)
        @log(menu="故障与场景预演", operate="导出模拟数据")
        def get(self, request: Request, workspace_id: str):
            params = query_params_to_single_dict(request.query_params)
            queryset = RehearsalService(workspace_id, request.user).data_batch_queryset(params, include_points=True)
            return _csv_response(build_data_simulation_csv(queryset), "rehearsal-simulation-data.csv")

    class SceneScript(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_WRITE_PERMISSIONS)
        @log(menu="故障与场景预演", operate="新增场景脚本")
        def post(self, request: Request, workspace_id: str):
            return result.success(RehearsalService(workspace_id, request.user).create_scene_script(request.data))

    class SceneLibrary(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_READ_PERMISSIONS)
        def get(self, request: Request, workspace_id: str):
            params = query_params_to_single_dict(request.query_params)
            return result.success(RehearsalService(workspace_id, request.user).list_scene_libraries(params))

        @has_permissions(*REHEARSAL_WRITE_PERMISSIONS)
        @log(menu="故障与场景预演", operate="新增演练场景库")
        def post(self, request: Request, workspace_id: str):
            return result.success(RehearsalService(workspace_id, request.user).create_scene_library(request.data))

    class SceneLibraryDetail(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_READ_PERMISSIONS)
        def get(self, request: Request, workspace_id: str, library_id: str):
            return result.success(RehearsalService(workspace_id, request.user).scene_library_detail(library_id))

    class SceneLibraryClone(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_WRITE_PERMISSIONS)
        @log(menu="故障与场景预演", operate="复制演练场景库")
        def post(self, request: Request, workspace_id: str, library_id: str):
            return result.success(RehearsalService(workspace_id, request.user).clone_scene_library(library_id, request.data))

    class SceneLibraryOperate(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_WRITE_PERMISSIONS)
        @log(menu="故障与场景预演", operate="操作演练场景库")
        def post(self, request: Request, workspace_id: str, library_id: str):
            return result.success(
                RehearsalService(workspace_id, request.user).operate_scene_library(library_id, request.data)
            )

    class SceneLibraryRun(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_WRITE_PERMISSIONS)
        @log(menu="故障与场景预演", operate="从场景库发起演练")
        def post(self, request: Request, workspace_id: str, library_id: str):
            return result.success(
                RehearsalService(workspace_id, request.user).create_scene_run_from_library(library_id, request.data)
            )

    class SceneRun(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_READ_PERMISSIONS)
        def get(self, request: Request, workspace_id: str):
            params = query_params_to_single_dict(request.query_params)
            return result.success(RehearsalService(workspace_id, request.user).list_scene_runs(params))

    class SceneRunCreate(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_WRITE_PERMISSIONS)
        @log(menu="故障与场景预演", operate="创建场景演练运行")
        def post(self, request: Request, workspace_id: str, instance_id: str):
            return result.success(
                RehearsalService(workspace_id, request.user).create_scene_run(instance_id, request.data)
            )

    class SceneRunDetail(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_READ_PERMISSIONS)
        def get(self, request: Request, workspace_id: str, run_id: str):
            return result.success(RehearsalService(workspace_id, request.user).scene_run_detail(run_id))

    class SceneRunOperate(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_WRITE_PERMISSIONS)
        @log(menu="故障与场景预演", operate="操作场景演练运行")
        def post(self, request: Request, workspace_id: str, run_id: str):
            return result.success(
                RehearsalService(workspace_id, request.user).operate_scene_run(run_id, request.data)
            )

    class WorkOrder(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_READ_PERMISSIONS)
        def get(self, request: Request, workspace_id: str):
            params = query_params_to_single_dict(request.query_params)
            return result.success(RehearsalService(workspace_id, request.user).list_work_orders(params))

    class WorkOrderCreate(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_WRITE_PERMISSIONS)
        @log(menu="故障与场景预演", operate="创建演练工单")
        def post(self, request: Request, workspace_id: str, run_id: str):
            return result.success(
                RehearsalService(workspace_id, request.user).create_work_order(run_id, request.data)
            )

    class WorkOrderOperate(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_WRITE_PERMISSIONS)
        @log(menu="故障与场景预演", operate="操作演练工单")
        def post(self, request: Request, workspace_id: str, order_id: str):
            return result.success(
                RehearsalService(workspace_id, request.user).operate_work_order(order_id, request.data)
            )

    class AlertTemplate(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_READ_PERMISSIONS)
        def get(self, request: Request, workspace_id: str):
            return result.success(RehearsalService(workspace_id, request.user).list_alert_templates())

        @has_permissions(*REHEARSAL_WRITE_PERMISSIONS)
        @log(menu="故障与场景预演", operate="新增演练告警模板")
        def post(self, request: Request, workspace_id: str):
            return result.success(RehearsalService(workspace_id, request.user).create_alert_template(request.data))

    class Alert(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_READ_PERMISSIONS)
        def get(self, request: Request, workspace_id: str):
            params = query_params_to_single_dict(request.query_params)
            return result.success(RehearsalService(workspace_id, request.user).list_alerts(params))

    class AlertCreate(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_WRITE_PERMISSIONS)
        @log(menu="故障与场景预演", operate="创建演练告警")
        def post(self, request: Request, workspace_id: str, instance_id: str):
            return result.success(RehearsalService(workspace_id, request.user).create_alert(instance_id, request.data))

    class AlertDetail(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_READ_PERMISSIONS)
        def get(self, request: Request, workspace_id: str, alert_id: str):
            return result.success(RehearsalService(workspace_id, request.user).alert_detail(alert_id))

    class AlertOperate(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_WRITE_PERMISSIONS)
        @log(menu="故障与场景预演", operate="操作演练告警")
        def post(self, request: Request, workspace_id: str, alert_id: str):
            return result.success(RehearsalService(workspace_id, request.user).operate_alert(alert_id, request.data))

    class InstanceTimeline(APIView):
        authentication_classes = [TokenAuth]

        @has_permissions(*REHEARSAL_READ_PERMISSIONS)
        def get(self, request: Request, workspace_id: str, instance_id: str):
            return result.success(RehearsalService(workspace_id, request.user).instance_timeline(instance_id))
