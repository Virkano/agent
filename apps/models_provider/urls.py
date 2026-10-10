import os

from django.urls import path

from . import views

app_name = "models_provider"
# @formatter:off
# fmt: off
urlpatterns = [
    path('provider', views.Provide.as_view()),
    path('provider/model_type_list', views.Provide.ModelTypeList.as_view()),
    path('provider/model_list', views.Provide.ModelList.as_view()),
    path('provider/model_params_form', views.Provide.ModelParamsForm.as_view()),
    path('provider/model_form', views.Provide.ModelForm.as_view()),
    path('workspace/<str:workspace_id>/model', views.ModelSetting.as_view()),
    path('workspace/<str:workspace_id>/model_list', views.ModelList.as_view()),
    path('workspace/<str:workspace_id>/model/<str:model_id>/model_params_form', views.ModelSetting.ModelParamsForm.as_view()),
    path('workspace/<str:workspace_id>/model/<str:model_id>', views.ModelSetting.Operate.as_view()),
    path('workspace/<str:workspace_id>/model/<str:model_id>/pause_download', views.ModelSetting.PauseDownload.as_view()),
    path('workspace/<str:workspace_id>/model/<str:model_id>/meta', views.ModelSetting.ModelMeta.as_view()),
    path('workspace/<str:workspace_id>/model-lifecycle/overview', views.ModelLifecycleView.Overview.as_view()),
    path('workspace/<str:workspace_id>/model-lifecycle/experiment', views.ModelLifecycleView.Experiment.as_view()),
    path('workspace/<str:workspace_id>/model-lifecycle/experiment/<str:experiment_id>', views.ModelLifecycleView.ExperimentOperate.as_view()),
    path('workspace/<str:workspace_id>/model-lifecycle/version', views.ModelLifecycleView.Version.as_view()),
    path('workspace/<str:workspace_id>/model-lifecycle/version/<str:version_id>', views.ModelLifecycleView.VersionOperate.as_view()),
    path('workspace/<str:workspace_id>/model-lifecycle/version/<str:version_id>/evaluate', views.ModelLifecycleView.Evaluate.as_view()),
    path('workspace/<str:workspace_id>/model-lifecycle/version/<str:version_id>/publish', views.ModelLifecycleView.Publish.as_view()),
    path('workspace/<str:workspace_id>/model-lifecycle/version/<str:version_id>/rollback', views.ModelLifecycleView.Rollback.as_view()),
    path('workspace/<str:workspace_id>/model-lifecycle/release', views.ModelLifecycleView.Release.as_view()),
    path('workspace/<str:workspace_id>/model-pipeline', views.ModelPipelineView.Pipeline.as_view()),
    path('workspace/<str:workspace_id>/model-pipeline/<str:pipeline_id>', views.ModelPipelineView.PipelineOperate.as_view()),
    path('workspace/<str:workspace_id>/model-pipeline/<str:pipeline_id>/run', views.ModelPipelineView.Run.as_view()),
    path('workspace/<str:workspace_id>/model-pipeline-run', views.ModelPipelineView.RunList.as_view()),
    path('workspace/<str:workspace_id>/model-pipeline-run/<str:run_id>', views.ModelPipelineView.RunOperate.as_view()),
    path('workspace/<str:workspace_id>/model-pipeline-run/<str:run_id>/approve', views.ModelPipelineView.Approve.as_view()),
    path('workspace/<str:workspace_id>/model-pipeline-run/<str:run_id>/retry', views.ModelPipelineView.Retry.as_view()),
    path('system/shared/workspace/<str:workspace_id>/model', views.WorkspaceSharedModelSetting.as_view()),
]

if os.environ.get('SERVER_NAME', 'web') == 'local_model':
    urlpatterns += [
        path('model/<str:model_id>/embed_documents', views.ModelApply.EmbedDocuments.as_view()),
        path('model/<str:model_id>/embed_query', views.ModelApply.EmbedQuery.as_view()),
        path('model/<str:model_id>/compress_documents', views.ModelApply.CompressDocuments.as_view()),
    ]
