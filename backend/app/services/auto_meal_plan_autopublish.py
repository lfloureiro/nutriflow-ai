from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.models.auto_meal_plan_event import AutoMealPlanEvent
from backend.app.services import auto_meal_plan_training_dataset
from backend.app.services.auto_meal_plan_model_publishing import (
    DEFAULT_PUBLISH_EVALUATION_STRATEGY,
    DEFAULT_PUBLISH_INCLUDE_SUGGESTED_RECIPE_ID,
    DEFAULT_PUBLISH_TARGET,
    publish_auto_meal_plan_model,
)
from backend.app.services.auto_meal_plan_model_runtime import (
    load_published_auto_meal_plan_model_artifact,
)

AUTO_PUBLISH_MIN_DATASET_ROWS = 8
AUTO_PUBLISH_MIN_NEW_EVENTS = 5
AUTO_PUBLISH_DATASET_FILENAME = "auto_meal_plan_training_autopublish.csv"

AUTO_PUBLISH_TARGET = DEFAULT_PUBLISH_TARGET
AUTO_PUBLISH_INCLUDE_SUGGESTED_RECIPE_ID = DEFAULT_PUBLISH_INCLUDE_SUGGESTED_RECIPE_ID
AUTO_PUBLISH_EVALUATION_STRATEGY = DEFAULT_PUBLISH_EVALUATION_STRATEGY
AUTO_PUBLISH_FALLBACK_EVALUATION_STRATEGY = "stratified_kfold"


@dataclass
class AutoMealPlanAutoPublishResult:
    status: str
    message: str
    trigger_reason: str
    dataset_path: str | None = None
    row_count: int | None = None
    latest_auto_event_id: int | None = None
    previous_published_event_id: int | None = None
    model_path: str | None = None
    report_path: str | None = None
    metadata: dict[str, Any] | None = None


def get_latest_auto_event_id(db: Session) -> int:
    value = db.query(func.max(AutoMealPlanEvent.id)).scalar()
    return int(value or 0)


def build_auto_publish_dataset_path() -> Path:
    return auto_meal_plan_training_dataset.DATASET_DIR / AUTO_PUBLISH_DATASET_FILENAME


def should_try_fallback_for_exception(exc: Exception, primary_strategy: str) -> bool:
    if primary_strategy != "grouped_by_suggested_recipe_id":
        return False

    message = str(exc)
    return "insufficient_evaluation_support" in message


def try_publish_with_strategy(
    *,
    exported_dataset_path: Path,
    row_count: int,
    latest_auto_event_id: int,
    trigger_reason: str,
    primary_strategy: str,
    effective_strategy: str,
    used_fallback: bool,
) -> tuple[Path, Path, dict[str, Any]]:
    model_path, report_path, metadata = publish_auto_meal_plan_model(
        dataset_path=str(exported_dataset_path),
        target=AUTO_PUBLISH_TARGET,
        include_suggested_recipe_id=AUTO_PUBLISH_INCLUDE_SUGGESTED_RECIPE_ID,
        evaluation_strategy=effective_strategy,
        additional_artifact_fields={
            "source_max_auto_event_id": latest_auto_event_id,
            "source_dataset_row_count": row_count,
            "auto_publish_trigger_reason": trigger_reason,
            "auto_publish_enabled": True,
            "auto_publish_primary_strategy": primary_strategy,
            "auto_publish_effective_strategy": effective_strategy,
            "auto_publish_used_fallback": used_fallback,
        },
    )

    metadata = metadata or {}
    metadata.update(
        {
            "source_max_auto_event_id": latest_auto_event_id,
            "source_dataset_row_count": row_count,
            "auto_publish_trigger_reason": trigger_reason,
            "auto_publish_enabled": True,
            "auto_publish_primary_strategy": primary_strategy,
            "auto_publish_effective_strategy": effective_strategy,
            "auto_publish_used_fallback": used_fallback,
        }
    )

    return model_path, report_path, metadata


def maybe_auto_publish_auto_meal_plan_model(
    db: Session,
    *,
    trigger_reason: str,
) -> AutoMealPlanAutoPublishResult:
    latest_auto_event_id = get_latest_auto_event_id(db)
    if latest_auto_event_id <= 0:
        return AutoMealPlanAutoPublishResult(
            status="skipped_no_events",
            message="Ainda não existem eventos de auto-planeamento para publicar.",
            trigger_reason=trigger_reason,
            latest_auto_event_id=latest_auto_event_id,
        )

    artifact = load_published_auto_meal_plan_model_artifact()
    previous_published_event_id = int((artifact or {}).get("source_max_auto_event_id") or 0)

    if artifact is not None:
        new_event_count = latest_auto_event_id - previous_published_event_id
        if new_event_count < AUTO_PUBLISH_MIN_NEW_EVENTS:
            return AutoMealPlanAutoPublishResult(
                status="skipped_not_enough_new_events",
                message=(
                    "Ainda não existem eventos novos suficientes desde a última publicação "
                    f"({new_event_count}/{AUTO_PUBLISH_MIN_NEW_EVENTS})."
                ),
                trigger_reason=trigger_reason,
                latest_auto_event_id=latest_auto_event_id,
                previous_published_event_id=previous_published_event_id,
            )

    dataset_path = build_auto_publish_dataset_path()
    exported_dataset_path, row_count = auto_meal_plan_training_dataset.export_auto_plan_training_dataset(
        db,
        household_id=None,
        output_path=str(dataset_path),
    )

    if row_count < AUTO_PUBLISH_MIN_DATASET_ROWS:
        return AutoMealPlanAutoPublishResult(
            status="skipped_not_enough_rows",
            message=(
                "Ainda não existem linhas suficientes no dataset para autopublicação "
                f"({row_count}/{AUTO_PUBLISH_MIN_DATASET_ROWS})."
            ),
            trigger_reason=trigger_reason,
            dataset_path=str(exported_dataset_path),
            row_count=row_count,
            latest_auto_event_id=latest_auto_event_id,
            previous_published_event_id=previous_published_event_id,
        )

    primary_strategy = AUTO_PUBLISH_EVALUATION_STRATEGY

    try:
        model_path, report_path, metadata = try_publish_with_strategy(
            exported_dataset_path=exported_dataset_path,
            row_count=row_count,
            latest_auto_event_id=latest_auto_event_id,
            trigger_reason=trigger_reason,
            primary_strategy=primary_strategy,
            effective_strategy=primary_strategy,
            used_fallback=False,
        )
        return AutoMealPlanAutoPublishResult(
            status="published",
            message="Modelo de auto-planeamento publicado automaticamente com sucesso.",
            trigger_reason=trigger_reason,
            dataset_path=str(exported_dataset_path),
            row_count=row_count,
            latest_auto_event_id=latest_auto_event_id,
            previous_published_event_id=previous_published_event_id,
            model_path=str(model_path),
            report_path=str(report_path),
            metadata=metadata,
        )
    except Exception as primary_exc:
        if not should_try_fallback_for_exception(primary_exc, primary_strategy):
            return AutoMealPlanAutoPublishResult(
                status="skipped_publish_not_ready",
                message=str(primary_exc),
                trigger_reason=trigger_reason,
                dataset_path=str(exported_dataset_path),
                row_count=row_count,
                latest_auto_event_id=latest_auto_event_id,
                previous_published_event_id=previous_published_event_id,
            )

        fallback_strategy = AUTO_PUBLISH_FALLBACK_EVALUATION_STRATEGY

        try:
            model_path, report_path, metadata = try_publish_with_strategy(
                exported_dataset_path=exported_dataset_path,
                row_count=row_count,
                latest_auto_event_id=latest_auto_event_id,
                trigger_reason=trigger_reason,
                primary_strategy=primary_strategy,
                effective_strategy=fallback_strategy,
                used_fallback=True,
            )
            return AutoMealPlanAutoPublishResult(
                status="published",
                message=(
                    "Modelo de auto-planeamento publicado automaticamente com fallback "
                    "para stratified_kfold."
                ),
                trigger_reason=trigger_reason,
                dataset_path=str(exported_dataset_path),
                row_count=row_count,
                latest_auto_event_id=latest_auto_event_id,
                previous_published_event_id=previous_published_event_id,
                model_path=str(model_path),
                report_path=str(report_path),
                metadata=metadata,
            )
        except Exception as fallback_exc:
            return AutoMealPlanAutoPublishResult(
                status="skipped_publish_not_ready",
                message=(
                    f"Falha na estratégia primária ({primary_strategy}): {primary_exc} | "
                    f"Falha no fallback ({fallback_strategy}): {fallback_exc}"
                ),
                trigger_reason=trigger_reason,
                dataset_path=str(exported_dataset_path),
                row_count=row_count,
                latest_auto_event_id=latest_auto_event_id,
                previous_published_event_id=previous_published_event_id,
            )