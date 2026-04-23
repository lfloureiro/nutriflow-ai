import csv
import json
import unicodedata
from datetime import timezone, datetime
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from backend.app.models.auto_meal_plan_event import AutoMealPlanEvent
from backend.app.models.ingredient import Ingredient
from backend.app.models.recipe import Recipe
from backend.app.models.recipe_ingredient import RecipeIngredient

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATASET_DIR = PROJECT_ROOT / "data" / "ml_datasets"

RECIPE_INGREDIENT_PROFILE_COLUMNS = [
    "suggested_recipe_ingredient_count",
    "suggested_recipe_distinct_ingredient_count",
    "suggested_recipe_profile_flag_count",
    "suggested_recipe_has_arroz_ingredient",
    "suggested_recipe_has_massa_ingredient",
    "suggested_recipe_has_batata_ingredient",
    "suggested_recipe_has_ovos_ingredient",
    "suggested_recipe_has_peixe_marisco_ingredient",
    "suggested_recipe_has_frango_aves_ingredient",
    "suggested_recipe_has_vaca_ingredient",
    "suggested_recipe_has_porco_ingredient",
    "suggested_recipe_has_queijo_lacticinios_ingredient",
    "suggested_recipe_has_leguminosas_ingredient",
    "suggested_recipe_has_tomate_ingredient",
    "suggested_recipe_has_cebola_alho_ingredient",
]

RECIPE_INGREDIENT_KEYWORD_GROUPS = {
    "suggested_recipe_has_arroz_ingredient": [
        "arroz",
    ],
    "suggested_recipe_has_massa_ingredient": [
        "massa",
        "esparguete",
        "macarrao",
        "noodle",
        "noodles",
        "penne",
        "fusilli",
        "lasanha",
        "ravioli",
        "tortellini",
        "tagliatelle",
        "couscous",
        "cuscuz",
    ],
    "suggested_recipe_has_batata_ingredient": [
        "batata",
    ],
    "suggested_recipe_has_ovos_ingredient": [
        "ovo",
        "ovos",
    ],
    "suggested_recipe_has_peixe_marisco_ingredient": [
        "atum",
        "sardinha",
        "bacalhau",
        "pescada",
        "salmao",
        "peixe",
        "camarao",
        "marisco",
        "dourada",
        "robalo",
        "lula",
        "polvo",
    ],
    "suggested_recipe_has_frango_aves_ingredient": [
        "frango",
        "peru",
        "pato",
        "aves",
    ],
    "suggested_recipe_has_vaca_ingredient": [
        "vaca",
        "vitela",
        "novilho",
        "carne picada",
        "bife",
    ],
    "suggested_recipe_has_porco_ingredient": [
        "porco",
        "lombo",
        "bacon",
        "presunto",
        "chourico",
        "linguica",
        "salsicha",
    ],
    "suggested_recipe_has_queijo_lacticinios_ingredient": [
        "queijo",
        "mozzarella",
        "mozarela",
        "requeijao",
        "natas",
        "bechamel",
        "iogurte",
        "leite",
    ],
    "suggested_recipe_has_leguminosas_ingredient": [
        "feijao",
        "grao",
        "lentilha",
        "lentilhas",
        "ervilha",
        "ervilhas",
        "favas",
        "grao-de-bico",
    ],
    "suggested_recipe_has_tomate_ingredient": [
        "tomate",
        "polpa de tomate",
        "molho de tomate",
    ],
    "suggested_recipe_has_cebola_alho_ingredient": [
        "cebola",
        "alho",
    ],
}

DATASET_COLUMNS = [
    "source_event_id",
    "run_id",
    "household_id",
    "request_start_date",
    "request_end_date",
    "request_meal_types",
    "skip_existing",
    "plan_date",
    "meal_type",
    "weekday_index",
    "is_weekend",
    "suggestion_action",
    "suggested_recipe_id",
    "suggested_recipe_name",
    "suggested_categoria_alimentar",
    "suggested_proteina_principal",
    "suggested_adequado_refeicao",
    *RECIPE_INGREDIENT_PROFILE_COLUMNS,
    "score",
    "average_rating",
    "ratings_count",
    "reasons",
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


def normalize_ingredient_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    without_accents = "".join(char for char in normalized if not unicodedata.combining(char))
    collapsed = " ".join(without_accents.lower().strip().split())
    return collapsed


def empty_recipe_feature_profile() -> dict[str, int]:
    profile = {
        "suggested_recipe_ingredient_count": 0,
        "suggested_recipe_distinct_ingredient_count": 0,
        "suggested_recipe_profile_flag_count": 0,
    }

    for column in RECIPE_INGREDIENT_KEYWORD_GROUPS:
        profile[column] = 0

    return profile


def build_recipe_feature_profiles(db: Session) -> dict[int, dict[str, int]]:
    rows = (
        db.query(RecipeIngredient.recipe_id, Ingredient.name)
        .join(Ingredient, Ingredient.id == RecipeIngredient.ingredient_id)
        .order_by(RecipeIngredient.recipe_id.asc(), RecipeIngredient.id.asc())
        .all()
    )

    profiles: dict[int, dict[str, int]] = {}
    distinct_ingredient_names: dict[int, set[str]] = {}

    for recipe_id, ingredient_name in rows:
        profile = profiles.setdefault(recipe_id, empty_recipe_feature_profile())
        profile["suggested_recipe_ingredient_count"] += 1

        normalized_name = normalize_ingredient_text(ingredient_name or "")
        if not normalized_name:
            continue

        distinct_ingredient_names.setdefault(recipe_id, set()).add(normalized_name)

        for column, keywords in RECIPE_INGREDIENT_KEYWORD_GROUPS.items():
            if profile[column] == 1:
                continue

            if any(keyword in normalized_name for keyword in keywords):
                profile[column] = 1

    for recipe_id, profile in profiles.items():
        profile["suggested_recipe_distinct_ingredient_count"] = len(
            distinct_ingredient_names.get(recipe_id, set())
        )
        profile["suggested_recipe_profile_flag_count"] = sum(
            profile[column] for column in RECIPE_INGREDIENT_KEYWORD_GROUPS
        )

    return profiles


def recipe_index(db: Session) -> dict[int, Recipe]:
    rows = db.query(Recipe).order_by(Recipe.id.asc()).all()
    return {row.id: row for row in rows}


def event_sort_key(event: AutoMealPlanEvent) -> tuple[datetime, int]:
    return (event.created_at, event.id)


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

        changed_recipe = int(
            source_event.suggested_recipe_id is not None
            and final_recipe_id is not None
            and int(final_recipe_id) != int(source_event.suggested_recipe_id)
        )

        if changed_recipe:
            return {
                "lifecycle_count": 0,
                "latest_lifecycle_event_kind": "",
                "latest_execution_status": "",
                "final_recipe_id": final_recipe_id,
                "outcome_label": "accepted_with_recipe_change",
                "accepted_as_suggested": 0,
                "changed_recipe": 1,
                "deleted_after_apply": 0,
            }

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
    recipe_feature_profiles = build_recipe_feature_profiles(db)

    rows: list[dict[str, Any]] = []

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

        suggested_recipe_profile = (
            recipe_feature_profiles.get(
                source_event.suggested_recipe_id,
                empty_recipe_feature_profile(),
            )
            if source_event.suggested_recipe_id is not None
            else empty_recipe_feature_profile()
        )

        weekday_index = source_event.plan_date.weekday()
        is_weekend = int(weekday_index >= 5)

        row = {
            "source_event_id": source_event.id,
            "run_id": source_event.run_id,
            "household_id": source_event.household_id,
            "request_start_date": source_event.request_start_date.isoformat(),
            "request_end_date": source_event.request_end_date.isoformat(),
            "request_meal_types": serialize_json(source_event.request_meal_types),
            "skip_existing": int(source_event.skip_existing),
            "plan_date": source_event.plan_date.isoformat(),
            "meal_type": source_event.meal_type,
            "weekday_index": weekday_index,
            "is_weekend": is_weekend,
            "suggestion_action": source_event.suggestion_action,
            "suggested_recipe_id": source_event.suggested_recipe_id or "",
            "suggested_recipe_name": suggested_recipe.name if suggested_recipe else "",
            "suggested_categoria_alimentar": (
                suggested_recipe.categoria_alimentar if suggested_recipe else ""
            ),
            "suggested_proteina_principal": (
                suggested_recipe.proteina_principal if suggested_recipe else ""
            ),
            "suggested_adequado_refeicao": (
                suggested_recipe.adequado_refeicao if suggested_recipe else ""
            ),
            "score": source_event.score if source_event.score is not None else "",
            "average_rating": (
                source_event.average_rating
                if source_event.average_rating is not None
                else ""
            ),
            "ratings_count": source_event.ratings_count,
            "reasons": serialize_json(source_event.reasons),
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

        row.update(suggested_recipe_profile)
        rows.append(row)

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