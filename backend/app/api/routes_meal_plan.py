from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from backend.app.db.session import get_db
from backend.app.models.meal_plan_item import MealPlanItem
from backend.app.models.recipe import Recipe
from backend.app.schemas.meal_plan import MealPlanItemCreate, MealPlanItemRead

router = APIRouter(prefix="/meal-plan", tags=["meal-plan"])


@router.get("/", response_model=list[MealPlanItemRead])
def list_meal_plan(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    query = db.query(MealPlanItem).options(joinedload(MealPlanItem.recipe))

    if start_date:
        query = query.filter(MealPlanItem.plan_date >= start_date)

    if end_date:
        query = query.filter(MealPlanItem.plan_date <= end_date)

    items = query.order_by(MealPlanItem.plan_date.asc(), MealPlanItem.id.asc()).all()
    return items


@router.post("/", response_model=MealPlanItemRead, status_code=201)
def create_meal_plan_item(
    data: MealPlanItemCreate,
    db: Session = Depends(get_db),
):
    recipe = db.query(Recipe).filter(Recipe.id == data.recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Receita não encontrada.")

    meal_type_clean = data.meal_type.strip().lower()
    if not meal_type_clean:
        raise HTTPException(status_code=400, detail="O tipo de refeição é obrigatório.")

    item = MealPlanItem(
        plan_date=data.plan_date,
        meal_type=meal_type_clean,
        notes=data.notes,
        recipe_id=data.recipe_id,
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    item = (
        db.query(MealPlanItem)
        .options(joinedload(MealPlanItem.recipe))
        .filter(MealPlanItem.id == item.id)
        .first()
    )

    return item