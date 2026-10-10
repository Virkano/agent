# coding=utf-8
from rest_framework.request import Request
from rest_framework.parsers import MultiPartParser
from rest_framework.views import APIView

from common import result
from common.auth import TokenAuth
from common.auth.authentication import WorkspacePermissionMixin
from common.auth.workspace_permissions import workspace_menu_permissions
from common.constants.permission_constants import PermissionConstants
from common.utils.common import query_params_to_single_dict
from common.log.master_data import master_data_read_audit
from common.log.log import log
from marketing.serializers import MarketingCustomerService, MarketingTaskService, MarketingTouchBatchService


class MarketingTaskPermissionAPIView(WorkspacePermissionMixin, APIView):
    required_workspace_permissions = workspace_menu_permissions(PermissionConstants.MARKETING_TASK_READ)


class MarketingTaskView(MarketingTaskPermissionAPIView):
    authentication_classes = [TokenAuth]

    def get(self, request: Request, workspace_id: str):
        return result.success(
            MarketingTaskService(workspace_id, request.user).list(query_params_to_single_dict(request.query_params))
        )

    @log(menu="营销任务", operate="新增营销任务")
    def post(self, request: Request, workspace_id: str):
        return result.success(MarketingTaskService(workspace_id, request.user).create(request.data))

    class ApprovalQueue(MarketingTaskPermissionAPIView):
        authentication_classes = [TokenAuth]

        def get(self, request: Request, workspace_id: str):
            return result.success(MarketingTouchBatchService(workspace_id, request.user).approval_queue())

    class Page(MarketingTaskPermissionAPIView):
        authentication_classes = [TokenAuth]

        def get(self, request: Request, workspace_id: str, current_page: int, page_size: int):
            return result.success(
                MarketingTaskService(workspace_id, request.user).page(
                    current_page, page_size, query_params_to_single_dict(request.query_params)
                )
            )

    class Operate(MarketingTaskPermissionAPIView):
        authentication_classes = [TokenAuth]

        def get(self, request: Request, workspace_id: str, task_id: str):
            return result.success(MarketingTaskService(workspace_id, request.user).get(task_id))

        @log(menu="营销任务", operate="编辑营销任务")
        def put(self, request: Request, workspace_id: str, task_id: str):
            return result.success(MarketingTaskService(workspace_id, request.user).update(task_id, request.data))

        @log(menu="营销任务", operate="删除营销任务")
        def delete(self, request: Request, workspace_id: str, task_id: str):
            return result.success(MarketingTaskService(workspace_id, request.user).delete(task_id))

    class Effect(MarketingTaskPermissionAPIView):
        authentication_classes = [TokenAuth]

        def get(self, request: Request, workspace_id: str, task_id: str, current_page: int, page_size: int):
            return result.success(
                MarketingTaskService(workspace_id, request.user).effect(task_id, current_page, page_size)
            )

    class Dashboard(MarketingTaskPermissionAPIView):
        authentication_classes = [TokenAuth]

        def get(self, request: Request, workspace_id: str, task_id: str):
            return result.success(MarketingTaskService(workspace_id, request.user).dashboard(task_id))

    class Customer(MarketingTaskPermissionAPIView):
        authentication_classes = [TokenAuth]

        @master_data_read_audit("marketing.MarketingCustomer")
        def get(self, request: Request, workspace_id: str, task_id: str):
            return result.success(
                MarketingCustomerService(workspace_id, request.user).list(
                    task_id,
                    query_params_to_single_dict(request.query_params),
                )
            )

        @log(menu="营销任务", operate="新增营销客户")
        def post(self, request: Request, workspace_id: str, task_id: str):
            return result.success(MarketingCustomerService(workspace_id, request.user).create(task_id, request.data))

    class CustomerPage(MarketingTaskPermissionAPIView):
        authentication_classes = [TokenAuth]

        @master_data_read_audit("marketing.MarketingCustomer")
        def get(self, request: Request, workspace_id: str, task_id: str, current_page: int, page_size: int):
            return result.success(
                MarketingCustomerService(workspace_id, request.user).page(
                    task_id,
                    current_page,
                    page_size,
                    query_params_to_single_dict(request.query_params),
                )
            )

    class CustomerBulk(MarketingTaskPermissionAPIView):
        authentication_classes = [TokenAuth]

        @log(menu="营销任务", operate="批量新增营销客户")
        def post(self, request: Request, workspace_id: str, task_id: str):
            return result.success(
                MarketingCustomerService(workspace_id, request.user).bulk_create(task_id, request.data)
            )

    class CustomerImportPreview(MarketingTaskPermissionAPIView):
        authentication_classes = [TokenAuth]
        parser_classes = [MultiPartParser]

        @log(menu="营销任务", operate="预检客户导入文件")
        def post(self, request: Request, workspace_id: str, task_id: str):
            return result.success(
                MarketingCustomerService(workspace_id, request.user).preview_import(
                    task_id,
                    request.FILES.get("file"),
                    request.data.get("mapping"),
                )
            )

    class CustomerImport(MarketingTaskPermissionAPIView):
        authentication_classes = [TokenAuth]

        @log(menu="营销任务", operate="导入营销客户")
        def post(self, request: Request, workspace_id: str, task_id: str):
            return result.success(
                MarketingCustomerService(workspace_id, request.user).confirm_import(task_id, request.data)
            )

    class CustomerImportHistory(MarketingTaskPermissionAPIView):
        authentication_classes = [TokenAuth]

        def get(self, request: Request, workspace_id: str, task_id: str):
            return result.success(MarketingCustomerService(workspace_id, request.user).import_history(task_id))

    class CustomerOperate(MarketingTaskPermissionAPIView):
        authentication_classes = [TokenAuth]

        @log(menu="营销任务", operate="编辑营销客户")
        def put(self, request: Request, workspace_id: str, task_id: str, customer_id: str):
            return result.success(
                MarketingCustomerService(workspace_id, request.user).update(task_id, customer_id, request.data)
            )

        @log(menu="营销任务", operate="删除营销客户")
        def delete(self, request: Request, workspace_id: str, task_id: str, customer_id: str):
            return result.success(MarketingCustomerService(workspace_id, request.user).delete(task_id, customer_id))

    class CustomerFollowUp(MarketingTaskPermissionAPIView):
        authentication_classes = [TokenAuth]

        @log(menu="营销任务", operate="记录客户跟进")
        def post(self, request: Request, workspace_id: str, task_id: str, customer_id: str):
            return result.success(
                MarketingCustomerService(workspace_id, request.user).follow_up(task_id, customer_id, request.data)
            )

    class CustomerConversion(MarketingTaskPermissionAPIView):
        authentication_classes = [TokenAuth]

        @log(menu="营销任务", operate="记录客户转化")
        def post(self, request: Request, workspace_id: str, task_id: str, customer_id: str):
            return result.success(
                MarketingCustomerService(workspace_id, request.user).record_conversion(
                    task_id, customer_id, request.data
                )
            )

    class TouchBatch(MarketingTaskPermissionAPIView):
        authentication_classes = [TokenAuth]

        def get(self, request: Request, workspace_id: str, task_id: str):
            return result.success(MarketingTouchBatchService(workspace_id, request.user).list(task_id))

        @log(menu="营销任务", operate="新增触达批次")
        def post(self, request: Request, workspace_id: str, task_id: str):
            return result.success(MarketingTouchBatchService(workspace_id, request.user).create(task_id, request.data))

    class TouchBatchOperate(MarketingTaskPermissionAPIView):
        authentication_classes = [TokenAuth]

        def get(self, request: Request, workspace_id: str, task_id: str, batch_id: str):
            return result.success(MarketingTouchBatchService(workspace_id, request.user).get(task_id, batch_id))

        @log(menu="营销任务", operate="编辑触达批次")
        def put(self, request: Request, workspace_id: str, task_id: str, batch_id: str):
            return result.success(
                MarketingTouchBatchService(workspace_id, request.user).update(task_id, batch_id, request.data)
            )

    class TouchBatchExecution(MarketingTaskPermissionAPIView):
        authentication_classes = [TokenAuth]

        @log(menu="营销任务", operate="执行触达批次")
        def post(self, request: Request, workspace_id: str, task_id: str, batch_id: str):
            return result.success(
                MarketingTouchBatchService(workspace_id, request.user).record_execution(task_id, batch_id, request.data)
            )

    class TouchBatchApproval(MarketingTaskPermissionAPIView):
        authentication_classes = [TokenAuth]

        @log(menu="营销任务", operate="审批触达批次")
        def post(self, request: Request, workspace_id: str, task_id: str, batch_id: str):
            return result.success(
                MarketingTouchBatchService(workspace_id, request.user).approve(task_id, batch_id, request.data)
            )

    class TouchBatchResubmit(MarketingTaskPermissionAPIView):
        authentication_classes = [TokenAuth]

        @log(menu="营销任务", operate="重新提交触达批次")
        def post(self, request: Request, workspace_id: str, task_id: str, batch_id: str):
            return result.success(
                MarketingTouchBatchService(workspace_id, request.user).resubmit(task_id, batch_id, request.data)
            )

    class FollowUpQueue(MarketingTaskPermissionAPIView):
        authentication_classes = [TokenAuth]

        def get(self, request: Request, workspace_id: str, task_id: str):
            return result.success(MarketingTouchBatchService(workspace_id, request.user).queue(task_id))
