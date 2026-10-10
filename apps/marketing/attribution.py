from marketing.models import MarketingCustomer, MarketingTask
from marketing.recommendation import select_recommendation


def build_marketing_source(application_id, marketing_task_id, marketing_customer_id=None):
    if not marketing_task_id and marketing_customer_id:
        customer = MarketingCustomer.objects.filter(id=marketing_customer_id).select_related("task").first()
        if customer:
            marketing_task_id = customer.task_id
    if not marketing_task_id:
        return {}
    task = (
        MarketingTask.objects.filter(id=marketing_task_id, application_id=application_id)
        .select_related("scenario")
        .first()
    )
    if task is None:
        return {}
    source = {
        "marketing_task_id": str(task.id),
        "marketing_task_name": task.name,
        "marketing_scenario_id": str(task.scenario_id),
        "marketing_scenario_name": task.scenario.name if task.scenario else "",
        "marketing_channel": task.channel,
        "marketing_target_audience": task.target_audience,
        "marketing_objective": task.objective,
    }
    if marketing_customer_id:
        customer = MarketingCustomer.objects.filter(
            id=marketing_customer_id,
            task_id=task.id,
            workspace_id=task.workspace_id,
        ).first()
        if customer:
            task_config = task.config if isinstance(task.config, dict) else {}
            campaign_snapshot = task_config.get("marketing_campaign_snapshot")
            recommendation_policy = (
                {"enabled": True, "offers": campaign_snapshot}
                if isinstance(campaign_snapshot, list) and campaign_snapshot
                else (
                    task.scenario.config.get("recommendation_policy", {})
                    if isinstance(task.scenario.config, dict)
                    else {}
                )
            )
            source.update(
                {
                    "marketing_customer_id": str(customer.id),
                    "marketing_customer_name": customer.name,
                    "marketing_customer_phone_masked": (
                        f"{customer.phone[:3]}****{customer.phone[-4:]}"
                        if len(customer.phone or "") >= 7
                        else customer.phone
                    ),
                    "marketing_customer_plan": customer.current_plan,
                    "marketing_customer_province": customer.province,
                    "marketing_customer_data_usage": customer.monthly_data_usage,
                    "marketing_customer_call_usage": customer.monthly_call_usage,
                    "marketing_recommendation": select_recommendation(
                        recommendation_policy,
                        {
                            "plan": customer.current_plan,
                            "province": customer.province,
                            "data_usage": customer.monthly_data_usage,
                            "call_usage": customer.monthly_call_usage,
                        },
                    ),
                }
            )
    return source
