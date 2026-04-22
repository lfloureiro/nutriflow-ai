from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Iterable

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from backend.app.models.meal_plan_item import MealPlanItem
from backend.app.models.recipe import Recipe
from backend.app.models.recipe_preference import RecipePreference


DEFAULT_MEAL_TYPES = ["almoco", "jantar"]
BALANCE_CATEGORIES = ["carne", "peixe", "vegetariano_leguminosas"]
MEAT_PROTEINS = ["frango", "vaca", "porco", "peru", "enchidos_processados"]

RECENT_HISTORY_LOOKBACK_DAYS = 28
WEEK_BALANCE_LOOKBACK_DAYS = 14

BASE_SCORE = 40.0
NO_PREFERENCE_BONUS = 4.0
AVERAGE_RATING_WEIGHT = 6.0
RATINGS_COUNT_WEIGHT = 1.0
MAX_RATINGS_COUNT_BONUS = 4

FAMILY_FAVORITE_THRESHOLD = 4.5
FAMILY_FAVORITE_BONUS = 10
FAMILY_GOOD_THRESHOLD = 4.0
FAMILY_GOOD_BONUS = 5
FAMILY_LOW_THRESHOLD = 2.5
FAMILY_LOW_PENALTY = 18

SPECIFIC_MEAL_TYPE_BONUS = 8
GENERIC_MEAL_TYPE_BONUS = 4

MISSING_CATEGORY_PENALTY = 8
MISSING_PROTEIN_PENALTY = 4

RECIPE_USED_LAST_3_DAYS_PENALTY = 180
RECIPE_USED_LAST_7_DAYS_PENALTY = 140
RECIPE_USED_LAST_14_DAYS_PENALTY = 70
RECIPE_USED_LAST_21_DAYS_PENALTY = 30

RECIPE_ALREADY_IN_PLAN_PENALTY = 50

CATEGORY_BALANCE_BONUS = 14
CATEGORY_OVERUSE_PENALTY = 12
MEAT_BALANCE_BONUS = 10
MEAT_OVERUSE_PENALTY = 10

SAME_PREVIOUS_CATEGORY_PENALTY = 22
SAME_PREVIOUS_PROTEIN_PENALTY = 14

CATEGORY_RECENT_WINDOW = 3
CATEGORY_RECENT_REPEAT_PENALTY = 14
THREE_MEATS_IN_A_ROW_PENALTY = 28

MEAT_PROTEIN_RECENT_WINDOW = 4
MEAT_PROTEIN_REPEAT_PENALTY = 14


@dataclass
class PlannerSuggestion:
    plan_date: date
    meal_type: str
    action: str
    recipe: Recipe | None = None
    score: float | None = None
    average_rating: float | None = None
    ratings_count: int = 0
    reasons: list[str] = field(default_factory=list)


def normalize_meal_types(meal_types: list[str] | None) -> list[str]:
    if not meal_types:
        return DEFAULT_MEAL_TYPES.copy()

    normalized: list[str] = []
    for item in meal_types:
        cleaned = item.strip().lower()
        if cleaned and cleaned not in normalized:
            normalized.append(cleaned)

    return normalized or DEFAULT_MEAL_TYPES.copy()


def daterange(start_date: date, end_date: date) -> Iterable[date]:
    current = start_date
    while current <= end_date:
        yield current
        current += timedelta(days=1)


def week_start_sunday(value: date) -> date:
    days_since_sunday = (value.weekday() + 1) % 7
    return value - timedelta(days=days_since_sunday)


def recipe_suits_meal_type(recipe: Recipe, meal_type: str) -> bool:
    value = (recipe.adequado_refeicao or "").strip().lower()
    return value in {"", meal_type, "ambos"}


def category_key(recipe: Recipe) -> str:
    return (recipe.categoria_alimentar or "outra").strip().lower() or "outra"


def protein_key(recipe: Recipe) -> str:
    return (recipe.proteina_principal or "nenhuma").strip().lower() or "nenhuma"


def build_preference_map(db: Session, household_id: int) -> dict[int, dict]:
    rows = (
        db.query(
            RecipePreference.recipe_id,
            func.avg(RecipePreference.rating),
            func.count(RecipePreference.id),
        )
        .filter(RecipePreference.household_id == household_id)
        .group_by(RecipePreference.recipe_id)
        .all()
    )

    result: dict[int, dict] = {}
    for recipe_id, average_rating, ratings_count in rows:
        result[int(recipe_id)] = {
            "average_rating": round(float(average_rating), 2),
            "ratings_count": int(ratings_count),
        }

    return result


def build_recent_history(
    db: Session,
    household_id: int,
    start_date: date,
    end_date: date,
) -> tuple[list[MealPlanItem], dict[int, list[date]], MealPlanItem | None]:
    lookback_start = start_date - timedelta(days=RECENT_HISTORY_LOOKBACK_DAYS)

    items = (
        db.query(MealPlanItem)
        .options(joinedload(MealPlanItem.recipe))
        .filter(
            MealPlanItem.household_id == household_id,
            MealPlanItem.plan_date >= lookback_start,
            MealPlanItem.plan_date <= end_date,
        )
        .order_by(MealPlanItem.plan_date.asc(), MealPlanItem.id.asc())
        .all()
    )

    history_by_recipe: dict[int, list[date]] = {}
    latest_before_range: MealPlanItem | None = None

    for item in items:
        history_by_recipe.setdefault(item.recipe_id, []).append(item.plan_date)

        if item.plan_date < start_date:
            latest_before_range = item

    return items, history_by_recipe, latest_before_range


def build_meal_type_history(
    items: list[MealPlanItem],
) -> dict[str, list[tuple[date, str, str, int]]]:
    history: dict[str, list[tuple[date, str, str, int]]] = defaultdict(list)

    for item in items:
        history[item.meal_type].append(
            (
                item.plan_date,
                category_key(item.recipe),
                protein_key(item.recipe),
                item.recipe_id,
            )
        )

    return history


def seed_balance_counts(
    recent_items_before_range: list[MealPlanItem],
    existing_items_in_range: list[MealPlanItem],
) -> tuple[dict[date, dict[str, int]], dict[date, dict[str, int]], set[int]]:
    weekly_category_counts: dict[date, dict[str, int]] = {}
    weekly_meat_protein_counts: dict[date, dict[str, int]] = {}
    planned_recipe_ids: set[int] = set()

    def ensure_week_bucket(week_start: date) -> None:
        if week_start not in weekly_category_counts:
            weekly_category_counts[week_start] = {key: 0 for key in BALANCE_CATEGORIES}
        if week_start not in weekly_meat_protein_counts:
            weekly_meat_protein_counts[week_start] = {key: 0 for key in MEAT_PROTEINS}

    for item in recent_items_before_range:
        bucket = week_start_sunday(item.plan_date)
        ensure_week_bucket(bucket)

        category = category_key(item.recipe)
        if category in weekly_category_counts[bucket]:
            weekly_category_counts[bucket][category] += 1

        protein = protein_key(item.recipe)
        if category == "carne" and protein in weekly_meat_protein_counts[bucket]:
            weekly_meat_protein_counts[bucket][protein] += 1

    for item in existing_items_in_range:
        planned_recipe_ids.add(item.recipe_id)

        bucket = week_start_sunday(item.plan_date)
        ensure_week_bucket(bucket)

        category = category_key(item.recipe)
        if category in weekly_category_counts[bucket]:
            weekly_category_counts[bucket][category] += 1

        protein = protein_key(item.recipe)
        if category == "carne" and protein in weekly_meat_protein_counts[bucket]:
            weekly_meat_protein_counts[bucket][protein] += 1

    return weekly_category_counts, weekly_meat_protein_counts, planned_recipe_ids


def get_recent_same_meal_type_entries(
    meal_type_history: dict[str, list[tuple[date, str, str, int]]],
    meal_type: str,
    slot_date: date,
) -> list[tuple[date, str, str, int]]:
    return [
        entry
        for entry in meal_type_history.get(meal_type, [])
        if entry[0] < slot_date
    ]


def score_recipe_for_slot(
    recipe: Recipe,
    meal_type: str,
    slot_date: date,
    preference_map: dict[int, dict],
    weekly_category_counts: dict[date, dict[str, int]],
    weekly_meat_protein_counts: dict[date, dict[str, int]],
    history_by_recipe: dict[int, list[date]],
    meal_type_history: dict[str, list[tuple[date, str, str, int]]],
    planned_recipe_ids: set[int],
    last_category: str | None,
    last_protein: str | None,
) -> tuple[float, list[str], float | None, int, int]:
    score = BASE_SCORE
    reasons: list[str] = []

    category = category_key(recipe)
    protein = protein_key(recipe)

    preference = preference_map.get(recipe.id)
    average_rating: float | None = None
    ratings_count = 0

    if preference:
        average_rating = float(preference["average_rating"])
        ratings_count = int(preference["ratings_count"])

        score += average_rating * AVERAGE_RATING_WEIGHT
        score += min(ratings_count, MAX_RATINGS_COUNT_BONUS) * RATINGS_COUNT_WEIGHT

        if average_rating >= FAMILY_FAVORITE_THRESHOLD:
            score += FAMILY_FAVORITE_BONUS
            reasons.append("receita favorita da família")
        elif average_rating >= FAMILY_GOOD_THRESHOLD:
            score += FAMILY_GOOD_BONUS
            reasons.append("boa aceitação familiar")
        elif average_rating <= FAMILY_LOW_THRESHOLD:
            score -= FAMILY_LOW_PENALTY
            reasons.append("aceitação familiar fraca")
    else:
        score += NO_PREFERENCE_BONUS
        reasons.append("sem avaliações, tratada como opção neutra")

    if recipe.adequado_refeicao == meal_type:
        score += SPECIFIC_MEAL_TYPE_BONUS
        reasons.append("adequada especificamente para este tipo de refeição")
    elif recipe.adequado_refeicao in {None, "", "ambos"}:
        score += GENERIC_MEAL_TYPE_BONUS

    if recipe.categoria_alimentar is None:
        score -= MISSING_CATEGORY_PENALTY
        reasons.append("categoria alimentar ainda por definir")

    if recipe.proteina_principal is None:
        score -= MISSING_PROTEIN_PENALTY
        reasons.append("proteína principal ainda por definir")

    previous_dates = [
        item_date
        for item_date in history_by_recipe.get(recipe.id, [])
        if item_date < slot_date
    ]
    days_since_last_use_for_sort = 9999

    if previous_dates:
        last_used_date = max(previous_dates)
        days_since_last_use = (slot_date - last_used_date).days
        days_since_last_use_for_sort = days_since_last_use

        if days_since_last_use <= 3:
            score -= RECIPE_USED_LAST_3_DAYS_PENALTY
            reasons.append("usada nos últimos 3 dias")
        elif days_since_last_use <= 7:
            score -= RECIPE_USED_LAST_7_DAYS_PENALTY
            reasons.append("usada nos últimos 7 dias")
        elif days_since_last_use <= 14:
            score -= RECIPE_USED_LAST_14_DAYS_PENALTY
            reasons.append("usada nas últimas 2 semanas")
        elif days_since_last_use <= 21:
            score -= RECIPE_USED_LAST_21_DAYS_PENALTY
            reasons.append("usada nas últimas 3 semanas")

    if recipe.id in planned_recipe_ids:
        score -= RECIPE_ALREADY_IN_PLAN_PENALTY
        reasons.append("já aparece neste plano")

    current_week_start = week_start_sunday(slot_date)
    current_week_category_counts = weekly_category_counts.setdefault(
        current_week_start,
        {key: 0 for key in BALANCE_CATEGORIES},
    )
    current_week_meat_counts = weekly_meat_protein_counts.setdefault(
        current_week_start,
        {key: 0 for key in MEAT_PROTEINS},
    )

    if category in BALANCE_CATEGORIES:
        min_category_count = min(current_week_category_counts.values())
        current_category_count = current_week_category_counts.get(category, 0)

        if current_category_count == min_category_count:
            score += CATEGORY_BALANCE_BONUS
            reasons.append("ajuda ao equilíbrio semanal entre carne, peixe e vegetariano")
        elif current_category_count > min_category_count + 1:
            score -= CATEGORY_OVERUSE_PENALTY
            reasons.append("categoria já está acima do equilíbrio desta semana")

    if last_category is not None and category == last_category:
        score -= SAME_PREVIOUS_CATEGORY_PENALTY
        reasons.append("evita repetir a mesma categoria na refeição anterior")

    if category == "carne" and protein in MEAT_PROTEINS:
        min_meat_count = min(current_week_meat_counts.values())
        current_meat_count = current_week_meat_counts.get(protein, 0)

        if current_meat_count == min_meat_count:
            score += MEAT_BALANCE_BONUS
            reasons.append("ajuda à rotação semanal entre tipos de carne")
        elif current_meat_count > min_meat_count + 1:
            score -= MEAT_OVERUSE_PENALTY
            reasons.append("tipo de carne já está acima do equilíbrio desta semana")

        if last_protein is not None and protein == last_protein:
            score -= SAME_PREVIOUS_PROTEIN_PENALTY
            reasons.append("evita repetir o mesmo tipo de proteína")

    recent_same_meal_type_entries = get_recent_same_meal_type_entries(
        meal_type_history=meal_type_history,
        meal_type=meal_type,
        slot_date=slot_date,
    )

    recent_categories = [
        entry[1]
        for entry in recent_same_meal_type_entries[-CATEGORY_RECENT_WINDOW:]
    ]

    if len(recent_categories) >= 2 and recent_categories.count(category) >= 2:
        score -= CATEGORY_RECENT_REPEAT_PENALTY
        reasons.append("categoria repetida demasiadas vezes nas últimas refeições do mesmo tipo")

    if category == "carne":
        recent_categories_for_streak = [entry[1] for entry in recent_same_meal_type_entries[-2:]]
        if len(recent_categories_for_streak) == 2 and all(
            item == "carne" for item in recent_categories_for_streak
        ):
            score -= THREE_MEATS_IN_A_ROW_PENALTY
            reasons.append("evita três refeições seguidas de carne neste tipo de refeição")

        recent_meat_proteins = [
            entry[2]
            for entry in recent_same_meal_type_entries[-MEAT_PROTEIN_RECENT_WINDOW:]
            if entry[1] == "carne" and entry[2] in MEAT_PROTEINS
        ]
        if len(recent_meat_proteins) >= 2 and recent_meat_proteins.count(protein) >= 2:
            score -= MEAT_PROTEIN_REPEAT_PENALTY
            reasons.append("tipo de carne repetido demasiadas vezes recentemente")

    return round(score, 2), reasons, average_rating, ratings_count, days_since_last_use_for_sort


def build_auto_meal_plan_preview(
    db: Session,
    household_id: int,
    start_date: date,
    end_date: date,
    meal_types: list[str] | None = None,
    skip_existing: bool = True,
) -> list[PlannerSuggestion]:
    if end_date < start_date:
        raise ValueError("A data final não pode ser anterior à data inicial.")

    normalized_meal_types = normalize_meal_types(meal_types)

    eligible_recipes = (
        db.query(Recipe)
        .filter(Recipe.auto_plan_enabled.is_(True))
        .order_by(Recipe.name.asc())
        .all()
    )

    preference_map = build_preference_map(db, household_id)

    existing_items = (
        db.query(MealPlanItem)
        .options(joinedload(MealPlanItem.recipe))
        .filter(
            MealPlanItem.household_id == household_id,
            MealPlanItem.plan_date >= start_date,
            MealPlanItem.plan_date <= end_date,
        )
        .order_by(MealPlanItem.plan_date.asc(), MealPlanItem.id.asc())
        .all()
    )
    existing_by_slot = {(item.plan_date, item.meal_type): item for item in existing_items}

    recent_history_items, history_by_recipe, latest_before_range = build_recent_history(
        db=db,
        household_id=household_id,
        start_date=start_date,
        end_date=end_date,
    )

    balance_lookback_start = start_date - timedelta(days=WEEK_BALANCE_LOOKBACK_DAYS)
    recent_items_before_range = [
        item
        for item in recent_history_items
        if balance_lookback_start <= item.plan_date < start_date
    ]

    weekly_category_counts, weekly_meat_protein_counts, planned_recipe_ids = seed_balance_counts(
        recent_items_before_range=recent_items_before_range,
        existing_items_in_range=existing_items,
    )

    meal_type_history = build_meal_type_history(recent_history_items)

    last_category = category_key(latest_before_range.recipe) if latest_before_range else None
    last_protein = protein_key(latest_before_range.recipe) if latest_before_range else None

    suggestions: list[PlannerSuggestion] = []

    for plan_date in daterange(start_date, end_date):
        for meal_type in normalized_meal_types:
            existing = existing_by_slot.get((plan_date, meal_type))

            if existing and skip_existing:
                suggestions.append(
                    PlannerSuggestion(
                        plan_date=plan_date,
                        meal_type=meal_type,
                        action="skip_existing",
                        recipe=existing.recipe,
                        reasons=["já existe uma refeição planeada neste slot"],
                    )
                )

                last_category = category_key(existing.recipe)
                last_protein = protein_key(existing.recipe)
                continue

            candidates = [
                recipe
                for recipe in eligible_recipes
                if recipe_suits_meal_type(recipe, meal_type)
            ]

            if not candidates:
                suggestions.append(
                    PlannerSuggestion(
                        plan_date=plan_date,
                        meal_type=meal_type,
                        action="no_candidate",
                        reasons=["não existem receitas elegíveis para este tipo de refeição"],
                    )
                )
                continue

            scored_candidates = []
            for recipe in candidates:
                (
                    score,
                    reasons,
                    average_rating,
                    ratings_count,
                    days_since_last_use_for_sort,
                ) = score_recipe_for_slot(
                    recipe=recipe,
                    meal_type=meal_type,
                    slot_date=plan_date,
                    preference_map=preference_map,
                    weekly_category_counts=weekly_category_counts,
                    weekly_meat_protein_counts=weekly_meat_protein_counts,
                    history_by_recipe=history_by_recipe,
                    meal_type_history=meal_type_history,
                    planned_recipe_ids=planned_recipe_ids,
                    last_category=last_category,
                    last_protein=last_protein,
                )
                scored_candidates.append(
                    (
                        score,
                        days_since_last_use_for_sort,
                        ratings_count,
                        recipe.name.lower(),
                        recipe,
                        reasons,
                        average_rating,
                    )
                )

            scored_candidates.sort(key=lambda item: (-item[0], -item[1], -item[2], item[3]))
            (
                best_score,
                _best_days_since_last_use,
                best_ratings_count,
                _,
                best_recipe,
                best_reasons,
                best_average_rating,
            ) = scored_candidates[0]

            suggestions.append(
                PlannerSuggestion(
                    plan_date=plan_date,
                    meal_type=meal_type,
                    action="suggest",
                    recipe=best_recipe,
                    score=best_score,
                    average_rating=best_average_rating,
                    ratings_count=best_ratings_count,
                    reasons=best_reasons,
                )
            )

            planned_recipe_ids.add(best_recipe.id)
            history_by_recipe.setdefault(best_recipe.id, []).append(plan_date)
            meal_type_history.setdefault(meal_type, []).append(
                (
                    plan_date,
                    category_key(best_recipe),
                    protein_key(best_recipe),
                    best_recipe.id,
                )
            )

            current_week_start = week_start_sunday(plan_date)
            weekly_category_counts.setdefault(
                current_week_start,
                {key: 0 for key in BALANCE_CATEGORIES},
            )
            weekly_meat_protein_counts.setdefault(
                current_week_start,
                {key: 0 for key in MEAT_PROTEINS},
            )

            selected_category = category_key(best_recipe)
            selected_protein = protein_key(best_recipe)

            if selected_category in weekly_category_counts[current_week_start]:
                weekly_category_counts[current_week_start][selected_category] += 1

            if (
                selected_category == "carne"
                and selected_protein in weekly_meat_protein_counts[current_week_start]
            ):
                weekly_meat_protein_counts[current_week_start][selected_protein] += 1

            last_category = selected_category
            last_protein = selected_protein

    return suggestions