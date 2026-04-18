from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from backend.app.db.session import get_db
from backend.app.models.household import Household
from backend.app.models.meal_plan_item import MealPlanItem
from backend.app.models.recipe import Recipe
from backend.app.models.recipe_ingredient import RecipeIngredient
from backend.app.schemas.shopping_list import (
    ShoppingListItemRead,
    ShoppingListSourceRead,
)

router = APIRouter(prefix="/shopping-list", tags=["shopping-list"])


def try_parse_number(value: str | None) -> float | None:
    if value is None:
        return None

    value = value.strip().replace(",", ".")
    if not value:
        return None

    try:
        return float(value)
    except ValueError:
        return None


@router.get("/generate", response_model=list[ShoppingListItemRead])
def generate_shopping_list(
    household_id: int = Query(...),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    household = db.query(Household).filter(Household.id == household_id).first()
    if not household:
        raise HTTPException(status_code=404, detail="Agregado não encontrado.")

    query = (
        db.query(MealPlanItem)
        .options(
            joinedload(MealPlanItem.recipe)
            .joinedload(Recipe.ingredient_links)
            .joinedload(RecipeIngredient.ingredient)
        )
        .filter(MealPlanItem.household_id == household_id)
    )

    if start_date:
        query = query.filter(MealPlanItem.plan_date >= start_date)

    if end_date:
        query = query.filter(MealPlanItem.plan_date <= end_date)

    meal_plan_items = query.order_by(MealPlanItem.plan_date.asc(), MealPlanItem.id.asc()).all()

    grouped: dict[tuple[int, str | None], dict] = {}

    for item in meal_plan_items:
        for link in item.recipe.ingredient_links:
            key = (link.ingredient.id, link.unit)

            if key not in grouped:
                grouped[key] = {
                    "ingredient_id": link.ingredient.id,
                    "ingredient_name": link.ingredient.name,
                    "unit": link.unit,
                    "raw_quantities": [],
                    "numeric_total": 0.0,
                    "all_numeric": True,
                    "sources": [],
                }

            qty_number = try_parse_number(link.quantity)

            if qty_number is None:
                grouped[key]["all_numeric"] = False
                if link.quantity:
                    grouped[key]["raw_quantities"].append(link.quantity)
            else:
                grouped[key]["numeric_total"] += qty_number

            grouped[key]["sources"].append(
                ShoppingListSourceRead(
                    recipe_id=item.recipe.id,
                    recipe_name=item.recipe.name,
                    plan_date=item.plan_date.isoformat(),
                    meal_type=item.meal_type,
                )
            )

    result = []

    for _, data in sorted(grouped.items(), key=lambda x: x[1]["ingredient_name"].lower()):
        quantity: str | None = None

        if data["all_numeric"]:
            total = data["numeric_total"]
            if total.is_integer():
                quantity = str(int(total))
            else:
                quantity = str(round(total, 2))
        elif data["raw_quantities"]:
            quantity = " + ".join(data["raw_quantities"])

        result.append(
            ShoppingListItemRead(
                ingredient_id=data["ingredient_id"],
                ingredient_name=data["ingredient_name"],
                quantity=quantity,
                unit=data["unit"],
                sources=data["sources"],
            )
        )

    return result