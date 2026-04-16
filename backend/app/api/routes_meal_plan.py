from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from backend.app.db.session import get_db
from backend.app.models.meal_plan_item import MealPlanItem
from backend.app.models.recipe import Recipe
from backend.app.schemas.meal_plan import (
    MealPlanItemCreate,
    MealPlanItemRead,
    MealPlanItemUpdate,
    NextMealSlotRead,
)

router = APIRouter(prefix="/meal-plan", tags=["meal-plan"])

MEAL_SLOT_ORDER = [
    ("pequeno-almoco", time(8, 0)),
    ("almoco", time(13, 0)),
    ("lanche", time(17, 0)),
    ("jantar", time(20, 0)),
]


def get_next_available_slot(db: Session) -> tuple[date, str]:
    now = datetime.now()

    existing_items = (
        db.query(MealPlanItem)
        .filter(MealPlanItem.plan_date >= now.date())
        .all()
    )

    occupied_slots = {(item.plan_date, item.meal_type) for item in existing_items}

    for day_offset in range(0, 30):
        candidate_date = now.date() + timedelta(days=day_offset)

        for meal_type, slot_time in MEAL_SLOT_ORDER:
            candidate_datetime = datetime.combine(candidate_date, slot_time)

            if candidate_datetime <= now:
                continue

            if (candidate_date, meal_type) not in occupied_slots:
                return candidate_date, meal_type

    fallback_date = now.date() + timedelta(days=31)
    return fallback_date, "almoco"


@router.get("/next-slot", response_model=NextMealSlotRead)
def get_next_meal_slot(db: Session = Depends(get_db)):
    plan_date, meal_type = get_next_available_slot(db)
    return NextMealSlotRead(plan_date=plan_date, meal_type=meal_type)


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

    existing = (
        db.query(MealPlanItem)
        .filter(
            MealPlanItem.plan_date == data.plan_date,
            MealPlanItem.meal_type == meal_type_clean,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Já existe uma refeição planeada para essa data e esse tipo de refeição.",
        )

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


@router.patch("/{meal_plan_item_id}", response_model=MealPlanItemRead)
def update_meal_plan_item(
    meal_plan_item_id: int,
    data: MealPlanItemUpdate,
    db: Session = Depends(get_db),
):
    item = db.query(MealPlanItem).filter(MealPlanItem.id == meal_plan_item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Refeição planeada não encontrada.")

    new_plan_date = data.plan_date if data.plan_date is not None else item.plan_date

    if data.meal_type is not None:
        meal_type_clean = data.meal_type.strip().lower()
        if not meal_type_clean:
            raise HTTPException(status_code=400, detail="O tipo de refeição é obrigatório.")
        new_meal_type = meal_type_clean
    else:
        new_meal_type = item.meal_type

    new_recipe_id = data.recipe_id if data.recipe_id is not None else item.recipe_id

    if data.recipe_id is not None:
        recipe = db.query(Recipe).filter(Recipe.id == data.recipe_id).first()
        if not recipe:
            raise HTTPException(status_code=404, detail="Receita não encontrada.")

    existing = (
        db.query(MealPlanItem)
        .filter(
            MealPlanItem.plan_date == new_plan_date,
            MealPlanItem.meal_type == new_meal_type,
            MealPlanItem.id != meal_plan_item_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Já existe uma refeição planeada para essa data e esse tipo de refeição.",
        )

    item.plan_date = new_plan_date
    item.meal_type = new_meal_type
    item.recipe_id = new_recipe_id

    if "notes" in data.model_fields_set:
        item.notes = data.notes

    db.commit()
    db.refresh(item)

    item = (
        db.query(MealPlanItem)
        .options(joinedload(MealPlanItem.recipe))
        .filter(MealPlanItem.id == item.id)
        .first()
    )

    return item


@router.delete("/{meal_plan_item_id}")
def delete_meal_plan_item(
    meal_plan_item_id: int,
    db: Session = Depends(get_db),
):
    item = db.query(MealPlanItem).filter(MealPlanItem.id == meal_plan_item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Refeição planeada não encontrada.")

    db.delete(item)
    db.commit()

    return {"message": "Refeição planeada apagada com sucesso."}