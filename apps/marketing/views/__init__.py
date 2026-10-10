from .scenario import MarketingScenarioView
from .campaign import MarketingCampaignView
from .quality_review import MarketingQualityReviewView
from .task import MarketingTaskView
from .operations import MarketingOperationsView
from .alerts import MarketingAlertView
from .notifications import MarketingNotificationView
from .report import MarketingAnalysisReportView
from .recommendation_engine import RecommendationEngineView
from .ivr import ChangeOperationControlView, ChangeOperationRiskView, IvrProtocolSimulatorView

__all__ = [
    "MarketingScenarioView",
    "MarketingCampaignView",
    "MarketingQualityReviewView",
    "MarketingTaskView",
    "MarketingOperationsView",
    "MarketingAlertView",
    "MarketingNotificationView",
    "MarketingAnalysisReportView",
    "RecommendationEngineView",
    "IvrProtocolSimulatorView",
    "ChangeOperationRiskView",
    "ChangeOperationControlView",
]
