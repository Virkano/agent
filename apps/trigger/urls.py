# coding=utf-8
"""
    @project: dianxin
    @Author：niu
    @file： urls.py
    @date：2026/1/9 16:15
    @desc:
"""
from django.urls import path

from . import views
from .handler.impl.trigger.event_trigger import EventTriggerView

app_name = "trigger"

# @formatter:off
# fmt: off
urlpatterns = [
    path('workspace/<str:workspace_id>/event-orchestration/dashboard', views.EventOrchestrationDashboardView.as_view(), name='event orchestration dashboard'),
    path('workspace/<str:workspace_id>/event-orchestration/flow', views.EventFlowView.as_view(), name='event flow'),
    path('workspace/<str:workspace_id>/event-orchestration/flow/<str:flow_id>', views.EventFlowDetailView.as_view(), name='event flow detail'),
    path('workspace/<str:workspace_id>/event-orchestration/flow/<str:flow_id>/publish', views.EventFlowPublishView.as_view(), name='event flow publish'),
    path('workspace/<str:workspace_id>/event-orchestration/event', views.StandardEventReceiveView.as_view(), name='standard event receive'),
    path('workspace/<str:workspace_id>/event-orchestration/run', views.EventFlowRunView.as_view(), name='event flow run'),
    path('workspace/<str:workspace_id>/event-orchestration/run/<str:run_id>', views.EventFlowRunDetailView.as_view(), name='event flow run detail'),
    path('workspace/<str:workspace_id>/event-orchestration/run/<str:run_id>/advance', views.EventFlowRunAdvanceView.as_view(), name='event flow run advance'),
    path('workspace/<str:workspace_id>/event-orchestration/run/<str:run_id>/replay', views.EventFlowRunReplayView.as_view(), name='event flow run replay'),
    path('workspace/<str:workspace_id>/event-orchestration/run/<str:run_id>/node/<str:node_id>/operate', views.EventFlowNodeOperateView.as_view(), name='event flow node operate'),
    path('workspace/<str:workspace_id>/resource-coordination/dashboard', views.ResourceCoordinationDashboardView.as_view(), name='resource coordination dashboard'),
    path('workspace/<str:workspace_id>/resource-coordination/pool', views.ResourcePoolView.as_view(), name='resource pool'),
    path('workspace/<str:workspace_id>/resource-coordination/pool/<str:pool_id>/task', views.DispatchTaskSubmitView.as_view(), name='dispatch task submit'),
    path('workspace/<str:workspace_id>/resource-coordination/pool/<str:pool_id>/reclaim', views.ResourcePoolReclaimView.as_view(), name='resource pool reclaim'),
    path('workspace/<str:workspace_id>/resource-coordination/task', views.DispatchTaskView.as_view(), name='dispatch task'),
    path('workspace/<str:workspace_id>/resource-coordination/task/<str:task_id>', views.DispatchTaskDetailView.as_view(), name='dispatch task detail'),
    path('workspace/<str:workspace_id>/resource-coordination/task/<str:task_id>/operate', views.DispatchTaskOperateView.as_view(), name='dispatch task operate'),
    path('workspace/<str:workspace_id>/trigger', views.TriggerView.as_view(), name='trigger'),
    path('workspace/<str:workspace_id>/trigger/batch_delete', views.TriggerView.BatchDelete.as_view(), name='delete batch'),
    path('workspace/<str:workspace_id>/trigger/batch_activate', views.TriggerView.BatchActivate.as_view(), name='activate batch'),
    path('workspace/<str:workspace_id>/trigger/<str:trigger_id>', views.TriggerView.Operate.as_view(), name='trigger operate'),
    path('workspace/<str:workspace_id>/trigger/<int:current_page>/<int:page_size>', views.TriggerView.Page.as_view(), name='trigger_page'),
    path('workspace/<str:workspace_id>/<str:source_type>/<str:source_id>/trigger/<str:trigger_id>', views.TaskSourceTriggerView.Operate.as_view(), name='task source trigger operate'),
    path('workspace/<str:workspace_id>/<str:source_type>/<str:source_id>/trigger', views.TaskSourceTriggerView.as_view(), name='task source trigger'),
    path('workspace/<str:workspace_id>/trigger/<str:trigger_id>/task_record/<int:current_page>/<int:page_size>', views.TriggerTaskRecordPageView.as_view(), name='trigger_task_record'),
    path('workspace/<str:workspace_id>/trigger/<str:trigger_id>/task', views.TriggerTaskView.as_view(), name='task'),
    path('trigger/v1/webhook/<str:trigger_id>', EventTriggerView.as_view(), name='trigger_webhook'),
    path('workspace/<str:workspace_id>/trigger/<str:trigger_id>/trigger_task/<str:trigger_task_id>/trigger_task_record/<str:trigger_task_record_id>', views.TriggerTaskRecordExecutionDetailsView.as_view(), name='task source trigger'),
]
