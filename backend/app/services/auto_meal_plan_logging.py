import uuid
from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session

from backend.app.models.auto_meal_plan_event import AutoMealPlanEvent
from backend.app.models.meal_plan_item import MealPlanItem
from backend.app.services.auto_meal_planner import PlannerSuggestion, normalize_meal_types

ENGINE_VERSION = "heuristic_v1"


@dataclass
class ApplyExecutionResult:
    execution_status: str
    meal_plan_item_id: int | None = None
    final_recipe_id: int | None = None


@dataclass
class MealPlanItemSnapshot:
    meal_plan_item_id: int
    household_id: int
    plan_date: date
    meal_type: str
    recipe_id: int
    notes: str | None


def snapshot_meal_plan_item(item: MealPlanItem) -> MealPlanItemSnapshot:
    return MealPlanItemSnapshot(
        meal_plan_item_id=item.id,
        household_id=item.household_id,
        plan_date=item.plan_date,
        meal_type=item.meal_type,
        recipe_id=item.recipe_id,
        notes=item.notes,
    )


def get_latest_auto_plan_apply_event(
    db: Session,
    meal_plan_item_id: int,
) -> AutoMealPlanEvent | None:
    return (
        db.query(AutoMealPlanEvent)
        .filter(
            AutoMealPlanEvent.meal_plan_item_id == meal_plan_item_id,
            AutoMealPlanEvent.event_kind == "apply",
            AutoMealPlanEvent.execution_status == "created",
        )
        .order_by(AutoMealPlanEvent.created_at.desc(), AutoMealPlanEvent.id.desc())
        .first()
    )


def detach_meal_plan_item_from_logs(
    db: Session,
    meal_plan_item_id: int,
) -> None:
    (
        db.query(AutoMealPlanEvent)
        .filter(AutoMealPlanEvent.meal_plan_item_id == meal_plan_item_id)
        .update({"meal_plan_item_id": None}, synchronize_session=False)
    )


def log_post_apply_lifecycle_event(
    db: Session,
    *,
    source_event: AutoMealPlanEvent,
    item_snapshot: MealPlanItemSnapshot,
    event_kind: str,
    execution_status: str,
    final_plan_date: date | None = None,
    final_meal_type: str | None = None,
    final_recipe_id: int | None = None,
    keep_meal_plan_item_link: bool = True,
    reasons: list[str] | None = None,
) -> AutoMealPlanEvent:
    row = AutoMealPlanEvent(
        run_id=source_event.run_id,
        household_id=item_snapshot.household_id,
        event_kind=event_kind,
        engine_version=source_event.engine_version,
        request_start_date=source_event.request_start_date,
        request_end_date=source_event.request_end_date,
        request_meal_types=source_event.request_meal_types,
        skip_existing=source_event.skip_existing,
        plan_date=final_plan_date or item_snapshot.plan_date,
        meal_type=final_meal_type or item_snapshot.meal_type,
        suggestion_action=source_event.suggestion_action,
        execution_status=execution_status,
        suggested_recipe_id=source_event.suggested_recipe_id,
        final_recipe_id=final_recipe_id,
        meal_plan_item_id=item_snapshot.meal_plan_item_id if keep_meal_plan_item_link else None,
        score=source_event.score,
        average_rating=source_event.average_rating,
        ratings_count=source_event.ratings_count,
        reasons=reasons or [],
    )
    db.add(row)
    return row


def log_auto_meal_plan_run(
    db: Session,
    *,
    household_id: int,
    event_kind: str,
    start_date: date,
    end_date: date,
    meal_types: list[str] | None,
    skip_existing: bool,
    suggestions: list[PlannerSuggestion],
    apply_results: dict[tuple[date, str], ApplyExecutionResult] | None = None,
) -> str:
    normalized_meal_types = normalize_meal_types(meal_types)
    run_id = str(uuid.uuid4())

    rows: list[AutoMealPlanEvent] = []
    for suggestion in suggestions:
        apply_result = None
        if apply_results is not None:
            apply_result = apply_results.get((suggestion.plan_date, suggestion.meal_type))

        rows.append(
            AutoMealPlanEvent(
                run_id=run_id,
                household_id=household_id,
                event_kind=event_kind,
                engine_version=ENGINE_VERSION,
                request_start_date=start_date,
                request_end_date=end_date,
                request_meal_types=normalized_meal_types,
                skip_existing=skip_existing,
                plan_date=suggestion.plan_date,
                meal_type=suggestion.meal_type,
                suggestion_action=suggestion.action,
                execution_status=apply_result.execution_status if apply_result else None,
                suggested_recipe_id=suggestion.recipe.id if suggestion.recipe else None,
                final_recipe_id=apply_result.final_recipe_id if apply_result else None,
                meal_plan_item_id=apply_result.meal_plan_item_id if apply_result else None,
                score=suggestion.score,
                average_rating=suggestion.average_rating,
                ratings_count=suggestion.ratings_count,
                reasons=suggestion.reasons,
            )
        )

    db.add_all(rows)
    return run_id