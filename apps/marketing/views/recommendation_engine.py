from rest_framework.request import Request
from rest_framework.views import APIView

from common import result
from common.auth import TokenAuth
from common.auth.authentication import WorkspacePermissionMixin
from common.auth.workspace_permissions import workspace_menu_permissions
from common.constants.permission_constants import PermissionConstants
from common.log.log import log
from marketing.serializers.recommendation_engine import RecommendationEngineService
from marketing.serializers.recommendation_effect import RecommendationEffectService
from marketing.serializers.recommendation_fusion import RecommendationFusionService
from marketing.serializers.recommendation_incremental import RecommendationIncrementalService
from marketing.serializers.recommendation_ranking import RecommendationRankingService


class RecommendationEnginePermissionAPIView(WorkspacePermissionMixin, APIView):
    required_workspace_permissions = workspace_menu_permissions(PermissionConstants.RECOMMENDATION_ENGINE_READ)


class RecommendationEngineView:
    class Dashboard(RecommendationEnginePermissionAPIView):
        authentication_classes = [TokenAuth]

        def get(self, request: Request, workspace_id: str):
            return result.success(RecommendationEngineService(workspace_id, request.user).dashboard())

    class FeatureSnapshot(RecommendationEnginePermissionAPIView):
        authentication_classes = [TokenAuth]

        @log(menu="召回与精排推荐引擎", operate="生成特征快照")
        def post(self, request: Request, workspace_id: str):
            return result.success(
                RecommendationEngineService(workspace_id, request.user).build_feature_snapshot(request.data)
            )

    class Train(RecommendationEnginePermissionAPIView):
        authentication_classes = [TokenAuth]

        @log(menu="召回与精排推荐引擎", operate="训练召回模型")
        def post(self, request: Request, workspace_id: str):
            return result.success(RecommendationEngineService(workspace_id, request.user).train(request.data))

    class Publish(RecommendationEnginePermissionAPIView):
        authentication_classes = [TokenAuth]

        @log(menu="召回与精排推荐引擎", operate="发布召回模型")
        def post(self, request: Request, workspace_id: str, model_version_id: str):
            return result.success(RecommendationEngineService(workspace_id, request.user).publish(model_version_id))

    class Recommend(RecommendationEnginePermissionAPIView):
        authentication_classes = [TokenAuth]

        @log(menu="召回与精排推荐引擎", operate="执行召回推荐")
        def post(self, request: Request, workspace_id: str):
            return result.success(RecommendationEngineService(workspace_id, request.user).recommend(request.data))

    class FusionConfig(RecommendationEnginePermissionAPIView):
        authentication_classes = [TokenAuth]

        def get(self, request: Request, workspace_id: str):
            return result.success(RecommendationFusionService(workspace_id, request.user).get_config())

        @log(menu="召回与精排推荐引擎", operate="保存多路融合配置")
        def put(self, request: Request, workspace_id: str):
            return result.success(RecommendationFusionService(workspace_id, request.user).save_config(request.data))

    class FusionDashboard(RecommendationEnginePermissionAPIView):
        authentication_classes = [TokenAuth]

        def get(self, request: Request, workspace_id: str):
            return result.success(RecommendationFusionService(workspace_id, request.user).dashboard())

    class FusionInfer(RecommendationEnginePermissionAPIView):
        authentication_classes = [TokenAuth]

        @log(menu="召回与精排推荐引擎", operate="执行多路融合推理")
        def post(self, request: Request, workspace_id: str):
            return result.success(RecommendationFusionService(workspace_id, request.user).infer(request.data))

    class RankingDashboard(RecommendationEnginePermissionAPIView):
        authentication_classes = [TokenAuth]

        def get(self, request: Request, workspace_id: str):
            return result.success(RecommendationRankingService(workspace_id, request.user).dashboard())

    class RankingVersion(RecommendationEnginePermissionAPIView):
        authentication_classes = [TokenAuth]

        @log(menu="召回与精排推荐引擎", operate="创建精排模型版本")
        def post(self, request: Request, workspace_id: str):
            return result.success(RecommendationRankingService(workspace_id, request.user).create_version(request.data))

    class RankingPublish(RecommendationEnginePermissionAPIView):
        authentication_classes = [TokenAuth]

        @log(menu="召回与精排推荐引擎", operate="发布精排模型")
        def post(self, request: Request, workspace_id: str, ranking_version_id: str):
            return result.success(RecommendationRankingService(workspace_id, request.user).publish(ranking_version_id))

    class RankingInfer(RecommendationEnginePermissionAPIView):
        authentication_classes = [TokenAuth]

        @log(menu="召回与精排推荐引擎", operate="执行精排推理")
        def post(self, request: Request, workspace_id: str):
            return result.success(RecommendationRankingService(workspace_id, request.user).infer(request.data))

    class IncrementalDashboard(RecommendationEnginePermissionAPIView):
        authentication_classes = [TokenAuth]

        def get(self, request: Request, workspace_id: str):
            return result.success(RecommendationIncrementalService(workspace_id, request.user).dashboard())

    class Feedback(RecommendationEnginePermissionAPIView):
        authentication_classes = [TokenAuth]

        @log(menu="召回与精排推荐引擎", operate="记录推荐反馈")
        def post(self, request: Request, workspace_id: str):
            return result.success(
                RecommendationIncrementalService(workspace_id, request.user).record_feedback(request.data)
            )

    class IncrementalSync(RecommendationEnginePermissionAPIView):
        authentication_classes = [TokenAuth]

        @log(menu="召回与精排推荐引擎", operate="同步增量反馈")
        def post(self, request: Request, workspace_id: str):
            return result.success(RecommendationIncrementalService(workspace_id, request.user).sync_business_feedback())

    class IncrementalTrain(RecommendationEnginePermissionAPIView):
        authentication_classes = [TokenAuth]

        @log(menu="召回与精排推荐引擎", operate="执行增量训练")
        def post(self, request: Request, workspace_id: str):
            return result.success(RecommendationIncrementalService(workspace_id, request.user).train(request.data))

    class EffectDashboard(RecommendationEnginePermissionAPIView):
        authentication_classes = [TokenAuth]

        def get(self, request: Request, workspace_id: str):
            return result.success(RecommendationEffectService(workspace_id).dashboard(request.query_params))
