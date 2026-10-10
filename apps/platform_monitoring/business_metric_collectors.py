"""PostgreSQL-backed collectors for cross-module business facts."""

from django.db import IntegrityError
from django.db.models import Max

from common.exception.app_exception import AppApiException
from trigger.models import EventFlowRun, FlowNodeRunStatus

from .metric_foundation import MetricFoundationService
from .models import MetricCollectionBatch, MetricDefinition


RECOMMENDATION_REVIEW_METRIC_KEY = "m12_recommendation_review_pending"
RECOMMENDATION_EXPOSURE_EVENT_TYPE = "marketing.recommendation.exposed"
REQUIRED_DIMENSIONS = {"task_id", "ranking_run_id", "flow_run_id"}


def _batch_no(run, changed_at):
    marker = changed_at.strftime("%Y%m%d%H%M%S%f")
    return f"AUTO-REC-REVIEW-{run.id}-{marker}"


def collect_recommendation_review_metrics():
    """Collect one immutable observation for every new recommendation-review state."""
    definitions = {
        row.workspace_id: row
        for row in MetricDefinition.objects.filter(
            metric_key=RECOMMENDATION_REVIEW_METRIC_KEY,
            enabled=True,
        ).select_related("owner")
        if REQUIRED_DIMENSIONS.issubset(set(row.dimensions_schema or []))
    }
    if not definitions:
        return {"run_count": 0, "created_count": 0, "reused_count": 0, "errors": []}
    runs = (
        EventFlowRun.objects.filter(
            workspace_id__in=definitions,
            standard_event__event_type=RECOMMENDATION_EXPOSURE_EVENT_TYPE,
        )
        .select_related("standard_event", "flow_version__created_by")
        .annotate(latest_node_update=Max("node_runs__update_time"))
        .order_by("create_time")
    )
    created_count = 0
    reused_count = 0
    errors = []
    for run in runs:
        payload = run.standard_event.payload_snapshot or {}
        if not all(payload.get(key) for key in ("task_id", "ranking_run_id")):
            errors.append({"run_id": str(run.id), "error": "MISSING_EVENT_LINKAGE"})
            continue
        changed_at = max(filter(None, (run.update_time, run.latest_node_update)))
        batch_no = _batch_no(run, changed_at)
        if MetricCollectionBatch.objects.filter(workspace_id=run.workspace_id, batch_no=batch_no).exists():
            reused_count += 1
            continue
        pending_count = run.node_runs.filter(status=FlowNodeRunStatus.WAITING_MANUAL).count()
        operator = definitions[run.workspace_id].owner or run.flow_version.created_by
        try:
            MetricFoundationService(run.workspace_id, operator).import_batch({
                "batch_no": batch_no,
                "rows": [{
                    "metric_key": RECOMMENDATION_REVIEW_METRIC_KEY,
                    "value": pending_count,
                    "dimensions": {
                        "task_id": str(payload["task_id"]),
                        "ranking_run_id": str(payload["ranking_run_id"]),
                        "flow_run_id": str(run.id),
                    },
                    "observed_at": changed_at,
                }],
            })
            created_count += 1
        except (AppApiException, IntegrityError):
            if MetricCollectionBatch.objects.filter(workspace_id=run.workspace_id, batch_no=batch_no).exists():
                reused_count += 1
            else:
                errors.append({"run_id": str(run.id), "error": "IMPORT_REJECTED"})
    return {
        "run_count": runs.count(),
        "created_count": created_count,
        "reused_count": reused_count,
        "errors": errors,
    }
