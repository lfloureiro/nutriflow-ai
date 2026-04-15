from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload

from backend.app.db.session import get_db
from backend.app.models.meal_plan_item import MealPlanItem
from backend.app.models.recipe import Recipe
from backend.app.models.recipe_ingredient import RecipeIngredient
from backend.app.schemas.shopping_list import ShoppingListItemRead

router = APIRouter(prefix="/shopping-list", tags=["shopping-list"])


@router.get("/generate", response_model=list[ShoppingListItemRead])
def generate_shopping_list(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    query = (
        db.query(MealPlanItem)
        .options(
            joinedload(MealPlanItem.recipe)
            .joinedload(Recipe.ingredient_links)
            .joinedload(RecipeIngredient.ingredient)
        )
    )

    if start_date:
        query = query.filter(MealPlanItem.plan_date >= start_date)

    if end_date:
        query = query.filter(MealPlanItem.plan_date <= end_date)

    meal_plan_items = query.order_by(MealPlanItem.plan_date.asc(), MealPlanItem.id.asc()).all()

    result = []

    for item in meal_plan_items:
        for link in item.recipe.ingredient_links:
            result.append(
                ShoppingListItemRead(
                    ingredient_id=link.ingredient.id,
                    ingredient_name=link.ingredient.name,
                    quantity=link.quantity,
                    unit=link.unit,
                    recipe_id=item.recipe.id,
                    recipe_name=item.recipe.name,
                    plan_date=item.plan_date.isoformat(),
                    meal_type=item.meal_type,
                )
            )

    return result