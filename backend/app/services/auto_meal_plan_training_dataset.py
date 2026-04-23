import csv
import json
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from backend.app.models.auto_meal_plan_event import AutoMealPlanEvent
from backend.app.models.recipe import Recipe

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATASET_DIR = PROJECT_ROOT / "data" / "ml_datasets"

MEAL_TYPE_ORDER = {
    "pequeno-almoco": 0,
    "almoco": 1,
    "lanche": 2,
    "jantar": 3,
}

REASON_FLAG_COLUMNS = [
    "reason_family_favorite",
    "reason_good_family_acceptance",
    "reason_low_family_acceptance",
    "reason_specific_meal_type",
    "reason_unrated_neutral",
    "reason_missing_category",
    "reason_missing_protein",
    "reason_recent_last_3_days",
    "reason_recent_last_7_days",
    "reason_recent_last_14_days",
    "reason_recent_last_21_days",
    "reason_already_in_plan",
    "reason_weekly_category_balance",
    "reason_weekly_category_overuse",
    "reason_weekly_meat_rotation",
    "reason_weekly_meat_overuse",
    "reason_same_previous_category",
    "reason_same_previous_protein",
    "reason_recent_category_repeat",
    "reason_three_meats_in_row",
    "reason_recent_meat_protein_repeat",
]

DATASET_COLUMNS = [
    "source_event_id",
    "run_id",
    "household_id",
    "request_start_date",
    "request_end_date",
    "request_meal_types",
    "skip_existing",
    "plan_date",
    "week_start_date",
    "meal_type",
    "weekday_index",
    "is_weekend",
    "run_slot_index",
    "week_slot_index",
    "suggestion_action",
    "suggested_recipe_id",
    "suggested_recipe_name",
    "suggested_categoria_alimentar",
    "suggested_proteina_principal",
    "suggested_adequado_refeicao",
    "suggested_family_preference_tier",
    "suggested_is_family_favorite",
    "score",
    "average_rating",
    "ratings_count",
    "reasons",
    "previous_suggested_categoria_alimentar",
    "previous_suggested_proteina_principal",
    "previous_same_meal_type_categoria_alimentar",
    "previous_same_meal_type_proteina_principal",
    "days_since_last_auto_plan_same_recipe",
    "weekly_same_category_count_before_slot",
    "weekly_same_protein_count_before_slot",
    "weekly_meal_type_slot_count_before_slot",
    "prior_household_recipe_seen_count",
    "prior_household_recipe_accept_rate",
    "prior_household_recipe_change_rate",
    "prior_household_recipe_delete_rate",
    *REASON_FLAG_COLUMNS,
    "lifecycle_count",
    "latest_lifecycle_event_kind",
    "latest_execution_status",
    "final_recipe_id",
    "final_recipe_name",
    "outcome_label",
    "accepted_as_suggested",
    "changed_recipe",
    "deleted_after_apply",
]


def ensure_dataset_dir() -> None:
    DATASET_DIR.mkdir(parents=True, exist_ok=True)


def serialize_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def recipe_index(db: Session) -> dict[int, Recipe]:
    rows = db.query(Recipe).order_by(Recipe.id.asc()).all()
    return {row.id: row for row in rows}


def meal_type_sort_key(value: str) -> int:
    return MEAL_TYPE_ORDER.get(value, 99)


def sunday_start(value: date) -> date:
    days_since_sunday = (value.weekday() + 1) % 7
    return value - timedelta(days=days_since_sunday)


def category_key(recipe: Recipe | None) -> str:
    if recipe is None:
        return ""
    return (recipe.categoria_alimentar or "").strip().lower()


def protein_key(recipe: Recipe | None) -> str:
    if recipe is None:
        return ""
    return (recipe.proteina_principal or "").strip().lower()


def event_sort_key(event: AutoMealPlanEvent) -> tuple[datetime, int]:
    return (event.created_at, event.id)


def source_event_sort_key(source_event: AutoMealPlanEvent) -> tuple[int, date, int, datetime, int]:
    return (
        source_event.household_id,
        source_event.plan_date,
        meal_type_sort_key(source_event.meal_type),
        source_event.created_at,
        source_event.id,
    )


def family_preference_tier(average_rating: float | None, ratings_count: int) -> str:
    if average_rating is None or ratings_count <= 0:
        return "unrated"
    if average_rating >= 4.5:
        return "favorite"
    if average_rating >= 4.0:
        return "good"
    if average_rating <= 2.5:
        return "low"
    return "neutral"


def build_reason_flags(reasons: list[str]) -> dict[str, int]:
    normalized = [(reason or "").strip().lower() for reason in reasons]

    def has_text(fragment: str) -> int:
        return int(any(fragment in reason for reason in normalized))

    return {
        "reason_family_favorite": has_text("receita favorita da família"),
        "reason_good_family_acceptance": has_text("boa aceitação familiar"),
        "reason_low_family_acceptance": has_text("aceitação familiar fraca"),
        "reason_specific_meal_type": has_text("adequada especificamente para este tipo de refeição"),
        "reason_unrated_neutral": has_text("sem avaliações, tratada como opção neutra"),
        "reason_missing_category": has_text("categoria alimentar ainda por definir"),
        "reason_missing_protein": has_text("proteína principal ainda por definir"),
        "reason_recent_last_3_days": has_text("usada nos últimos 3 dias"),
        "reason_recent_last_7_days": has_text("usada nos últimos 7 dias"),
        "reason_recent_last_14_days": has_text("usada nas últimas 2 semanas"),
        "reason_recent_last_21_days": has_text("usada nas últimas 3 semanas"),
        "reason_already_in_plan": has_text("já aparece neste plano"),
        "reason_weekly_category_balance": has_text(
            "ajuda ao equilíbrio semanal entre carne, peixe e vegetariano"
        ),
        "reason_weekly_category_overuse": has_text(
            "categoria já está acima do equilíbrio desta semana"
        ),
        "reason_weekly_meat_rotation": has_text(
            "ajuda à rotação semanal entre tipos de carne"
        ),
        "reason_weekly_meat_overuse": has_text(
            "tipo de carne já está acima do equilíbrio desta semana"
        ),
        "reason_same_previous_category": has_text(
            "evita repetir a mesma categoria na refeição anterior"
        ),
        "reason_same_previous_protein": has_text(
            "evita repetir o mesmo tipo de proteína"
        ),
        "reason_recent_category_repeat": has_text(
            "categoria repetida demasiadas vezes nas últimas refeições do mesmo tipo"
        ),
        "reason_three_meats_in_row": has_text(
            "evita três refeições seguidas de carne neste tipo de refeição"
        ),
        "reason_recent_meat_protein_repeat": has_text(
            "tipo de carne repetido demasiadas vezes recentemente"
        ),
    }


def select_matching_lifecycle_events(
    source_event: AutoMealPlanEvent,
    lifecycle_events: list[AutoMealPlanEvent],
) -> list[AutoMealPlanEvent]:
    matching_base = [
        item
        for item in lifecycle_events
        if item.run_id == source_event.run_id
        and item.household_id == source_event.household_id
        and item.created_at > source_event.created_at
        and item.suggested_recipe_id == source_event.suggested_recipe_id
    ]

    if not matching_base:
        return []

    if source_event.meal_plan_item_id is not None:
        matched_by_item = [
            item
            for item in matching_base
            if item.meal_plan_item_id == source_event.meal_plan_item_id
        ]
        if matched_by_item:
            return sorted(matched_by_item, key=event_sort_key)

    matched_by_slot = [
        item
        for item in matching_base
        if item.plan_date == source_event.plan_date
        and item.meal_type == source_event.meal_type
    ]
    if matched_by_slot:
        return sorted(matched_by_slot, key=event_sort_key)

    return sorted(matching_base, key=event_sort_key)


def derive_outcome(
    source_event: AutoMealPlanEvent,
    lifecycle_events: list[AutoMealPlanEvent],
) -> dict[str, Any]:
    if not lifecycle_events:
        final_recipe_id = source_event.final_recipe_id or source_event.suggested_recipe_id
        return {
            "lifecycle_count": 0,
            "latest_lifecycle_event_kind": "",
            "latest_execution_status": "",
            "final_recipe_id": final_recipe_id,
            "outcome_label": "accepted_as_suggested",
            "accepted_as_suggested": 1,
            "changed_recipe": 0,
            "deleted_after_apply": 0,
        }

    latest_event = lifecycle_events[-1]
    changed_recipe = int(
        any(item.execution_status == "recipe_replaced" for item in lifecycle_events)
    )

    if latest_event.execution_status == "deleted":
        outcome_label = "deleted_after_apply"
        accepted_as_suggested = 0
        deleted_after_apply = 1
        final_recipe_id = None
    elif changed_recipe:
        outcome_label = "accepted_with_recipe_change"
        accepted_as_suggested = 0
        deleted_after_apply = 0
        final_recipe_id = latest_event.final_recipe_id
    else:
        outcome_label = "accepted_with_metadata_change"
        accepted_as_suggested = 0
        deleted_after_apply = 0
        final_recipe_id = latest_event.final_recipe_id or source_event.final_recipe_id

    return {
        "lifecycle_count": len(lifecycle_events),
        "latest_lifecycle_event_kind": latest_event.event_kind,
        "latest_execution_status": latest_event.execution_status or "",
        "final_recipe_id": final_recipe_id,
        "outcome_label": outcome_label,
        "accepted_as_suggested": accepted_as_suggested,
        "changed_recipe": changed_recipe,
        "deleted_after_apply": deleted_after_apply,
    }


def build_auto_plan_training_dataset(
    db: Session,
    household_id: int | None = None,
) -> list[dict[str, Any]]:
    source_query = db.query(AutoMealPlanEvent).filter(
        AutoMealPlanEvent.event_kind == "apply",
        AutoMealPlanEvent.execution_status == "created",
    )

    lifecycle_query = db.query(AutoMealPlanEvent).filter(
        AutoMealPlanEvent.event_kind.in_(["post_apply_update", "post_apply_delete"])
    )

    if household_id is not None:
        source_query = source_query.filter(AutoMealPlanEvent.household_id == household_id)
        lifecycle_query = lifecycle_query.filter(AutoMealPlanEvent.household_id == household_id)

    source_events = source_query.order_by(
        AutoMealPlanEvent.created_at.asc(),
        AutoMealPlanEvent.id.asc(),
    ).all()

    lifecycle_events = lifecycle_query.order_by(
        AutoMealPlanEvent.created_at.asc(),
        AutoMealPlanEvent.id.asc(),
    ).all()

    lifecycle_by_run: dict[str, list[AutoMealPlanEvent]] = {}
    for item in lifecycle_events:
        lifecycle_by_run.setdefault(item.run_id, []).append(item)

    recipes = recipe_index(db)

    source_records: list[dict[str, Any]] = []
    for source_event in source_events:
        matching_lifecycle = select_matching_lifecycle_events(
            source_event,
            lifecycle_by_run.get(source_event.run_id, []),
        )
        outcome = derive_outcome(source_event, matching_lifecycle)

        suggested_recipe = (
            recipes.get(source_event.suggested_recipe_id)
            if source_event.suggested_recipe_id is not None
            else None
        )
        final_recipe = (
            recipes.get(outcome["final_recipe_id"])
            if outcome["final_recipe_id"] is not None
            else None
        )

        source_records.append(
            {
                "source_event": source_event,
                "outcome": outcome,
                "suggested_recipe": suggested_recipe,
                "final_recipe": final_recipe,
            }
        )

    source_records.sort(key=lambda item: source_event_sort_key(item["source_event"]))

    rows: list[dict[str, Any]] = []

    run_states: dict[tuple[int, str], dict[str, Any]] = {}
    household_recipe_last_date: dict[tuple[int, int], date] = {}
    household_recipe_history_stats: dict[tuple[int, int], dict[str, int]] = defaultdict(
        lambda: {
            "seen": 0,
            "accepted": 0,
            "changed": 0,
            "deleted": 0,
        }
    )

    for record in source_records:
        source_event: AutoMealPlanEvent = record["source_event"]
        outcome: dict[str, Any] = record["outcome"]
        suggested_recipe: Recipe | None = record["suggested_recipe"]
        final_recipe: Recipe | None = record["final_recipe"]

        suggested_category = category_key(suggested_recipe)
        suggested_protein = protein_key(suggested_recipe)

        weekday_index = source_event.plan_date.weekday()
        is_weekend = int(weekday_index >= 5)
        week_start_date = sunday_start(source_event.plan_date)

        run_key = (source_event.household_id, source_event.run_id)
        run_state = run_states.setdefault(
            run_key,
            {
                "run_slot_index": 0,
                "previous_category": "",
                "previous_protein": "",
                "last_by_meal_type": {},
                "weekly_category_counts": defaultdict(lambda: defaultdict(int)),
                "weekly_protein_counts": defaultdict(lambda: defaultdict(int)),
                "weekly_meal_type_counts": defaultdict(lambda: defaultdict(int)),
                "weekly_total_counts": defaultdict(int),
            },
        )

        run_slot_index = int(run_state["run_slot_index"]) + 1
        week_slot_index = int(run_state["weekly_total_counts"][week_start_date]) + 1

        previous_suggested_category = str(run_state["previous_category"])
        previous_suggested_protein = str(run_state["previous_protein"])

        previous_same_meal_type = run_state["last_by_meal_type"].get(source_event.meal_type, {})
        previous_same_meal_type_category = str(previous_same_meal_type.get("category", ""))
        previous_same_meal_type_protein = str(previous_same_meal_type.get("protein", ""))

        weekly_same_category_count_before_slot = (
            int(run_state["weekly_category_counts"][week_start_date].get(suggested_category, 0))
            if suggested_category
            else 0
        )
        weekly_same_protein_count_before_slot = (
            int(run_state["weekly_protein_counts"][week_start_date].get(suggested_protein, 0))
            if suggested_category == "carne" and suggested_protein
            else 0
        )
        weekly_meal_type_slot_count_before_slot = int(
            run_state["weekly_meal_type_counts"][week_start_date].get(source_event.meal_type, 0)
        )

        last_same_recipe_date = None
        if source_event.suggested_recipe_id is not None:
            last_same_recipe_date = household_recipe_last_date.get(
                (source_event.household_id, source_event.suggested_recipe_id)
            )

        days_since_last_auto_plan_same_recipe: int | str
        if last_same_recipe_date is None:
            days_since_last_auto_plan_same_recipe = ""
        else:
            days_since_last_auto_plan_same_recipe = (
                source_event.plan_date - last_same_recipe_date
            ).days

        prior_household_recipe_seen_count = 0
        prior_household_recipe_accept_rate: float | str = ""
        prior_household_recipe_change_rate: float | str = ""
        prior_household_recipe_delete_rate: float | str = ""

        if source_event.suggested_recipe_id is not None:
            prior_stats = household_recipe_history_stats[
                (source_event.household_id, source_event.suggested_recipe_id)
            ]
            prior_household_recipe_seen_count = int(prior_stats["seen"])

            if prior_household_recipe_seen_count > 0:
                prior_household_recipe_accept_rate = round(
                    prior_stats["accepted"] / prior_household_recipe_seen_count,
                    4,
                )
                prior_household_recipe_change_rate = round(
                    prior_stats["changed"] / prior_household_recipe_seen_count,
                    4,
                )
                prior_household_recipe_delete_rate = round(
                    prior_stats["deleted"] / prior_household_recipe_seen_count,
                    4,
                )

        suggested_family_preference_tier = family_preference_tier(
            source_event.average_rating,
            source_event.ratings_count,
        )
        suggested_is_family_favorite = int(suggested_family_preference_tier == "favorite")

        reason_flags = build_reason_flags(source_event.reasons)

        row = {
            "source_event_id": source_event.id,
            "run_id": source_event.run_id,
            "household_id": source_event.household_id,
            "request_start_date": source_event.request_start_date.isoformat(),
            "request_end_date": source_event.request_end_date.isoformat(),
            "request_meal_types": serialize_json(source_event.request_meal_types),
            "skip_existing": int(source_event.skip_existing),
            "plan_date": source_event.plan_date.isoformat(),
            "week_start_date": week_start_date.isoformat(),
            "meal_type": source_event.meal_type,
            "weekday_index": weekday_index,
            "is_weekend": is_weekend,
            "run_slot_index": run_slot_index,
            "week_slot_index": week_slot_index,
            "suggestion_action": source_event.suggestion_action,
            "suggested_recipe_id": source_event.suggested_recipe_id or "",
            "suggested_recipe_name": suggested_recipe.name if suggested_recipe else "",
            "suggested_categoria_alimentar": suggested_recipe.categoria_alimentar if suggested_recipe else "",
            "suggested_proteina_principal": suggested_recipe.proteina_principal if suggested_recipe else "",
            "suggested_adequado_refeicao": suggested_recipe.adequado_refeicao if suggested_recipe else "",
            "suggested_family_preference_tier": suggested_family_preference_tier,
            "suggested_is_family_favorite": suggested_is_family_favorite,
            "score": source_event.score if source_event.score is not None else "",
            "average_rating": (
                source_event.average_rating if source_event.average_rating is not None else ""
            ),
            "ratings_count": source_event.ratings_count,
            "reasons": serialize_json(source_event.reasons),
            "previous_suggested_categoria_alimentar": previous_suggested_category,
            "previous_suggested_proteina_principal": previous_suggested_protein,
            "previous_same_meal_type_categoria_alimentar": previous_same_meal_type_category,
            "previous_same_meal_type_proteina_principal": previous_same_meal_type_protein,
            "days_since_last_auto_plan_same_recipe": days_since_last_auto_plan_same_recipe,
            "weekly_same_category_count_before_slot": weekly_same_category_count_before_slot,
            "weekly_same_protein_count_before_slot": weekly_same_protein_count_before_slot,
            "weekly_meal_type_slot_count_before_slot": weekly_meal_type_slot_count_before_slot,
            "prior_household_recipe_seen_count": prior_household_recipe_seen_count,
            "prior_household_recipe_accept_rate": prior_household_recipe_accept_rate,
            "prior_household_recipe_change_rate": prior_household_recipe_change_rate,
            "prior_household_recipe_delete_rate": prior_household_recipe_delete_rate,
            "lifecycle_count": outcome["lifecycle_count"],
            "latest_lifecycle_event_kind": outcome["latest_lifecycle_event_kind"],
            "latest_execution_status": outcome["latest_execution_status"],
            "final_recipe_id": outcome["final_recipe_id"] or "",
            "final_recipe_name": final_recipe.name if final_recipe else "",
            "outcome_label": outcome["outcome_label"],
            "accepted_as_suggested": outcome["accepted_as_suggested"],
            "changed_recipe": outcome["changed_recipe"],
            "deleted_after_apply": outcome["deleted_after_apply"],
        }

        row.update(reason_flags)
        rows.append(row)

        run_state["run_slot_index"] = run_slot_index
        run_state["previous_category"] = suggested_category
        run_state["previous_protein"] = suggested_protein
        run_state["last_by_meal_type"][source_event.meal_type] = {
            "category": suggested_category,
            "protein": suggested_protein,
        }
        if suggested_category:
            run_state["weekly_category_counts"][week_start_date][suggested_category] += 1
        if suggested_category == "carne" and suggested_protein:
            run_state["weekly_protein_counts"][week_start_date][suggested_protein] += 1
        run_state["weekly_meal_type_counts"][week_start_date][source_event.meal_type] += 1
        run_state["weekly_total_counts"][week_start_date] += 1

        if source_event.suggested_recipe_id is not None:
            household_recipe_last_date[
                (source_event.household_id, source_event.suggested_recipe_id)
            ] = source_event.plan_date

            current_stats = household_recipe_history_stats[
                (source_event.household_id, source_event.suggested_recipe_id)
            ]
            current_stats["seen"] += 1
            current_stats["accepted"] += int(outcome["accepted_as_suggested"])
            current_stats["changed"] += int(outcome["changed_recipe"])
            current_stats["deleted"] += int(outcome["deleted_after_apply"])

    return rows


def export_auto_plan_training_dataset(
    db: Session,
    *,
    household_id: int | None = None,
    output_path: str | None = None,
) -> tuple[Path, int]:
    rows = build_auto_plan_training_dataset(db, household_id=household_id)

    if output_path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
    else:
        ensure_dataset_dir()
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")
        scope = f"household_{household_id}" if household_id is not None else "all_households"
        path = DATASET_DIR / f"{timestamp}_auto_meal_plan_training_{scope}.csv"

    with path.open("w", encoding="utf-8", newline="") as file_handle:
        writer = csv.DictWriter(file_handle, fieldnames=DATASET_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    return path, len(rows)