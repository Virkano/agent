"""Verify the M12 task's model and knowledge version lineage."""

import logging

from scripts.m12_linkage_inventory import DEMO_WORKSPACE_ID


RELEASE_REASON = "M12验收模拟：验证同一任务知识索引发布与回滚，不改写历史版本"


def run(workspace_id=DEMO_WORKSPACE_ID):
    logging.disable(logging.DEBUG)
    from knowledge.models import (
        KnowledgeIndexReleaseAction,
        KnowledgeIndexReleaseRecord,
        KnowledgeIndexVersion,
        KnowledgeIndexVersionStatus,
    )
    from knowledge.serializers.etl import KnowledgeEtlService
    from marketing.models import (
        RecommendationModelStatus,
        RecommendationRankingRun,
        RecommendationTrainingStatus,
    )

    ranking = RecommendationRankingRun.objects.filter(
        workspace_id=workspace_id,
    ).select_related(
        "customer__task__user",
        "fusion_run__model_version__training_run",
    ).order_by("-create_time").first()
    if ranking is None or ranking.customer is None or ranking.fusion_run is None:
        raise RuntimeError("Run the M12 recommendation probe first")
    task = ranking.customer.task
    model_version = ranking.fusion_run.model_version
    if model_version is None or model_version.status != RecommendationModelStatus.PUBLISHED:
        raise RuntimeError("M12 ranking is not bound to a published recommendation model")
    if model_version.training_run.status != RecommendationTrainingStatus.SUCCESS:
        raise RuntimeError("M12 recommendation model has no successful training fact")
    if not model_version.metrics:
        raise RuntimeError("M12 recommendation model has no evaluation metrics")
    if task.knowledge_id is None:
        raise RuntimeError("M12 task is not bound to a knowledge base")
    operator = task.user or model_version.user
    if operator is None:
        raise RuntimeError("M12 version lineage has no acceptance operator")

    service = KnowledgeEtlService(workspace_id, str(task.knowledge_id), operator)
    original = KnowledgeIndexVersion.objects.filter(
        workspace_id=workspace_id,
        knowledge_id=task.knowledge_id,
        status=KnowledgeIndexVersionStatus.PUBLISHED,
    ).first()
    if original is None:
        raise RuntimeError("M12 knowledge base has no published index version")
    rollback = KnowledgeIndexReleaseRecord.objects.filter(
        workspace_id=workspace_id,
        knowledge_id=task.knowledge_id,
        action=KnowledgeIndexReleaseAction.ROLLBACK,
        reason=RELEASE_REASON,
    ).select_related("from_version", "target_version").first()
    created_release = False
    if rollback is None:
        candidate = service.start_run({})
        if candidate["status"] != "WAITING_RELEASE":
            raise RuntimeError("Acceptance knowledge ETL did not pass its quality gate")
        service.publish_run(candidate["id"], {"reason": RELEASE_REASON})
        service.rollback_version(str(original.id), {"reason": RELEASE_REASON})
        rollback = KnowledgeIndexReleaseRecord.objects.get(
            workspace_id=workspace_id,
            knowledge_id=task.knowledge_id,
            action=KnowledgeIndexReleaseAction.ROLLBACK,
            reason=RELEASE_REASON,
        )
        created_release = True
    original.refresh_from_db()
    if rollback.target_version_id != original.id:
        raise RuntimeError("Knowledge rollback did not restore the original published version")
    if original.status != KnowledgeIndexVersionStatus.PUBLISHED:
        raise RuntimeError("Original knowledge index is not published after rollback")
    releases = list(
        KnowledgeIndexReleaseRecord.objects.filter(
            workspace_id=workspace_id,
            knowledge_id=task.knowledge_id,
        ).values_list("action", flat=True)
    )
    if KnowledgeIndexReleaseAction.PUBLISH not in releases:
        raise RuntimeError("Knowledge index has no publish fact")
    print(
        {
            "workspace_id": workspace_id,
            "task_id": str(task.id),
            "knowledge_id": str(task.knowledge_id),
            "published_knowledge_version_id": str(original.id),
            "knowledge_release_actions": releases,
            "recommendation_model_version_id": str(model_version.id),
            "recommendation_model_status": model_version.status,
            "training_run_id": str(model_version.training_run_id),
            "training_status": model_version.training_run.status,
            "evaluation_metric_keys": sorted(model_version.metrics),
            "created_release_facts": created_release,
            "acceptance_simulated": True,
        }
    )
