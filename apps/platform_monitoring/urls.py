from django.urls import path

from .views import MetricFoundationView, PlatformMonitoringView


urlpatterns = [
    path("workspace/<str:workspace_id>/platform-monitoring/dashboard", PlatformMonitoringView.Dashboard.as_view()),
    path("workspace/<str:workspace_id>/platform-monitoring/collect", PlatformMonitoringView.Collect.as_view()),
    path("workspace/<str:workspace_id>/platform-monitoring/rule", PlatformMonitoringView.Rule.as_view()),
    path(
        "workspace/<str:workspace_id>/platform-monitoring/rule/<str:rule_id>",
        PlatformMonitoringView.RuleOperate.as_view(),
    ),
    path("workspace/<str:workspace_id>/platform-monitoring/alert", PlatformMonitoringView.Alert.as_view()),
    path(
        "workspace/<str:workspace_id>/platform-monitoring/alert/<str:alert_id>/operate",
        PlatformMonitoringView.AlertOperate.as_view(),
    ),
    path("workspace/<str:workspace_id>/metric-foundation/overview", MetricFoundationView.Overview.as_view()),
    path("workspace/<str:workspace_id>/metric-foundation/analytics", MetricFoundationView.Analytics.as_view()),
    path(
        "workspace/<str:workspace_id>/metric-foundation/observation/<str:observation_id>",
        MetricFoundationView.ObservationDetail.as_view(),
    ),
    path("workspace/<str:workspace_id>/metric-foundation/definition", MetricFoundationView.Definition.as_view()),
    path(
        "workspace/<str:workspace_id>/metric-foundation/definition/<str:definition_id>",
        MetricFoundationView.DefinitionOperate.as_view(),
    ),
    path("workspace/<str:workspace_id>/metric-foundation/source", MetricFoundationView.Source.as_view()),
    path(
        "workspace/<str:workspace_id>/metric-foundation/source/<str:source_id>",
        MetricFoundationView.SourceOperate.as_view(),
    ),
    path("workspace/<str:workspace_id>/metric-foundation/rule", MetricFoundationView.Rule.as_view()),
    path(
        "workspace/<str:workspace_id>/metric-foundation/rule/<str:rule_id>",
        MetricFoundationView.RuleOperate.as_view(),
    ),
    path("workspace/<str:workspace_id>/metric-foundation/import", MetricFoundationView.ImportBatch.as_view()),
    path("workspace/<str:workspace_id>/metric-foundation/assignee", MetricFoundationView.Assignee.as_view()),
    path("workspace/<str:workspace_id>/metric-foundation/duty-shift", MetricFoundationView.DutyShift.as_view()),
    path(
        "workspace/<str:workspace_id>/metric-foundation/duty-shift/<str:shift_id>",
        MetricFoundationView.DutyShiftOperate.as_view(),
    ),
    path(
        "workspace/<str:workspace_id>/metric-foundation/order/<str:order_id>/operate",
        MetricFoundationView.OrderOperate.as_view(),
    ),
    path(
        "workspace/<str:workspace_id>/metric-foundation/order/<str:order_id>/events",
        MetricFoundationView.OrderEvent.as_view(),
    ),
    path("workspace/<str:workspace_id>/metric-foundation/bootstrap", MetricFoundationView.BootstrapDemo.as_view()),
]
