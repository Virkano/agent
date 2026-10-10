# coding=utf-8
from dataclasses import dataclass
from typing import Protocol


class ModelLifecycleTrackingAdapter(Protocol):
    def create_run(self, *, experiment_name: str, parameters: dict, tags: dict) -> str:
        """Create an external tracking run and return its identifier."""

    def finish_run(self, *, run_id: str, status: str, metrics: dict) -> None:
        """Finish an external tracking run."""


@dataclass(frozen=True)
class LocalLifecycleTrackingAdapter:
    """Local fallback used when no external experiment tracker is configured."""

    def create_run(self, *, experiment_name: str, parameters: dict, tags: dict) -> str:
        return ""

    def finish_run(self, *, run_id: str, status: str, metrics: dict) -> None:
        return None


def get_lifecycle_tracking_adapter() -> ModelLifecycleTrackingAdapter:
    """Return the configured tracker. MLflow can be added without coupling core state to it."""
    return LocalLifecycleTrackingAdapter()
