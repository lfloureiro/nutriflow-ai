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
    lookback_start = start_date - timedelta(days=21)

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


def seed_balance_counts(existing_items: list[MealPlanItem]) -> tuple[dict[str, int], dict[str, int], set[int]]:
    category_counts = {key: 0 for key in BALANCE_CATEGORIES}
    meat_protein_counts = {key: 0 for key in MEAT_PROTEINS}
    planned_recipe_ids: set[int] = set()

    for item in existing_items:
        planned_recipe_ids.add(item.recipe_id)

        category = category_key(item.recipe)
        if category in category_counts:
            category_counts[category] += 1

        protein = protein_key(item.recipe)
        if protein in meat_protein_counts and category == "carne":
            meat_protein_counts[protein] += 1

    return category_counts, meat_protein_counts, planned_recipe_ids


def score_recipe_for_slot(
    recipe: Recipe,
    meal_type: str,
    slot_date: date,
    preference_map: dict[int, dict],
    category_counts: dict[str, int],
    meat_protein_counts: dict[str, int],
    history_by_recipe: dict[int, list[date]],
    planned_recipe_ids: set[int],
    last_category: str | None,
    last_protein: str | None,
) -> tuple[float, list[str], float | None, int]:
    score = 40.0
    reasons: list[str] = []

    category = category_key(recipe)
    protein = protein_key(recipe)

    preference = preference_map.get(recipe.id)
    average_rating: float | None = None
    ratings_count = 0

    if preference:
        average_rating = float(preference["average_rating"])
        ratings_count = int(preference["ratings_count"])

        score += average_rating * 12
        score += min(ratings_count, 5) * 2

        if average_rating >= 4:
            reasons.append("boa aceitação familiar")
        elif average_rating <= 2:
            reasons.append("aceitação familiar fraca")
    else:
        score += 18
        reasons.append("sem avaliações, tratada como opção neutra")

    if recipe.adequado_refeicao == meal_type:
        score += 8
        reasons.append("adequada especificamente para este tipo de refeição")
    elif recipe.adequado_refeicao in {None, "", "ambos"}:
        score += 4

    if recipe.categoria_alimentar is None:
        score -= 8
        reasons.append("categoria alimentar ainda por definir")

    if recipe.proteina_principal is None:
        score -= 4
        reasons.append("proteína principal ainda por definir")

    previous_dates = [item_date for item_date in history_by_recipe.get(recipe.id, []) if item_date < slot_date]
    if previous_dates:
        last_used_date = max(previous_dates)
        days_since_last_use = (slot_date - last_used_date).days

        if days_since_last_use <= 7:
            score -= 70
            reasons.append("usada muito recentemente")
        elif days_since_last_use <= 14:
            score -= 35
            reasons.append("usada recentemente")
        elif days_since_last_use <= 21:
            score -= 15

    if recipe.id in planned_recipe_ids:
        score -= 30
        reasons.append("já aparece no intervalo planeado")

    if category in BALANCE_CATEGORIES:
        min_category_count = min(category_counts.values())
        current_category_count = category_counts.get(category, 0)

        if current_category_count == min_category_count:
            score += 12
            reasons.append("ajuda ao equilíbrio entre carne, peixe e vegetariano")
        elif current_category_count > min_category_count + 1:
            score -= 8

    if last_category is not None and category == last_category:
        score -= 18
        reasons.append("evita repetir a mesma categoria na refeição anterior")

    if category == "carne" and protein in MEAT_PROTEINS:
        min_meat_count = min(meat_protein_counts.values())
        current_meat_count = meat_protein_counts.get(protein, 0)

        if current_meat_count == min_meat_count:
            score += 8
            reasons.append("ajuda à rotação entre tipos de carne")
        elif current_meat_count > min_meat_count + 1:
            score -= 6

        if last_protein is not None and protein == last_protein:
            score -= 10
            reasons.append("evita repetir o mesmo tipo de proteína")

    return round(score, 2), reasons, average_rating, ratings_count


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

    _, history_by_recipe, latest_before_range = build_recent_history(
        db=db,
        household_id=household_id,
        start_date=start_date,
        end_date=end_date,
    )

    category_counts, meat_protein_counts, planned_recipe_ids = seed_balance_counts(existing_items)

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

            candidates = [recipe for recipe in eligible_recipes if recipe_suits_meal_type(recipe, meal_type)]

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
                score, reasons, average_rating, ratings_count = score_recipe_for_slot(
                    recipe=recipe,
                    meal_type=meal_type,
                    slot_date=plan_date,
                    preference_map=preference_map,
                    category_counts=category_counts,
                    meat_protein_counts=meat_protein_counts,
                    history_by_recipe=history_by_recipe,
                    planned_recipe_ids=planned_recipe_ids,
                    last_category=last_category,
                    last_protein=last_protein,
                )
                scored_candidates.append(
                    (score, ratings_count, recipe.name.lower(), recipe, reasons, average_rating)
                )

            scored_candidates.sort(key=lambda item: (-item[0], -item[1], item[2]))
            best_score, best_ratings_count, _, best_recipe, best_reasons, best_average_rating = scored_candidates[0]

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

            selected_category = category_key(best_recipe)
            selected_protein = protein_key(best_recipe)

            if selected_category in category_counts:
                category_counts[selected_category] += 1

            if selected_category == "carne" and selected_protein in meat_protein_counts:
                meat_protein_counts[selected_protein] += 1

            last_category = selected_category
            last_protein = selected_protein

    return suggestions