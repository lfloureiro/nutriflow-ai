from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from backend.app.db.session import get_db
from backend.app.models.ingredient import Ingredient
from backend.app.models.meal_plan_item import MealPlanItem
from backend.app.models.recipe import Recipe
from backend.app.schemas.bulk import (
    BulkImportResult,
    BulkIngredientImportRequest,
    BulkMealPlanUpdateRequest,
    BulkRecipeImportRequest,
)
from backend.app.schemas.meal_plan import MealPlanItemRead

router = APIRouter(prefix="/bulk", tags=["bulk"])


@router.post("/ingredients/import", response_model=BulkImportResult)
def bulk_import_ingredients(
    data: BulkIngredientImportRequest,
    db: Session = Depends(get_db),
):
    if not data.items:
        raise HTTPException(status_code=400, detail="Não foram enviados ingredientes.")

    created = 0
    skipped = 0

    for item in data.items:
        name_clean = item.name.strip()

        if not name_clean:
            raise HTTPException(status_code=400, detail="Todos os ingredientes têm de ter nome.")

        existing = db.query(Ingredient).filter(Ingredient.name == name_clean).first()
        if existing:
            if data.skip_existing:
                skipped += 1
                continue
            raise HTTPException(
                status_code=400,
                detail=f"O ingrediente '{name_clean}' já existe.",
            )

        db.add(Ingredient(name=name_clean))
        created += 1

    db.commit()

    return BulkImportResult(
        total_received=len(data.items),
        created=created,
        skipped=skipped,
    )


@router.post("/recipes/import", response_model=BulkImportResult)
def bulk_import_recipes(
    data: BulkRecipeImportRequest,
    db: Session = Depends(get_db),
):
    if not data.items:
        raise HTTPException(status_code=400, detail="Não foram enviadas receitas.")

    created = 0
    skipped = 0

    for item in data.items:
        name_clean = item.name.strip()

        if not name_clean:
            raise HTTPException(status_code=400, detail="Todas as receitas têm de ter nome.")

        existing = db.query(Recipe).filter(Recipe.name == name_clean).first()
        if existing:
            if data.skip_existing:
                skipped += 1
                continue
            raise HTTPException(
                status_code=400,
                detail=f"A receita '{name_clean}' já existe.",
            )

        db.add(
            Recipe(
                name=name_clean,
                description=item.description,
            )
        )
        created += 1

    db.commit()

    return BulkImportResult(
        total_received=len(data.items),
        created=created,
        skipped=skipped,
    )


@router.patch("/meal-plan", response_model=list[MealPlanItemRead])
def bulk_update_meal_plan(
    data: BulkMealPlanUpdateRequest,
    db: Session = Depends(get_db),
):
    if not data.items:
        raise HTTPException(status_code=400, detail="Não foram enviados itens para atualizar.")

    ids = [item.id for item in data.items]
    unique_ids = set(ids)
    if len(ids) != len(unique_ids):
        raise HTTPException(status_code=400, detail="Existem IDs repetidos no pedido.")

    meal_plan_items = (
        db.query(MealPlanItem)
        .filter(MealPlanItem.id.in_(ids))
        .all()
    )

    if len(meal_plan_items) != len(ids):
        found_ids = {item.id for item in meal_plan_items}
        missing_ids = [item_id for item_id in ids if item_id not in found_ids]
        raise HTTPException(
            status_code=404,
            detail=f"Itens do plano não encontrados: {missing_ids}",
        )

    meal_plan_by_id = {item.id: item for item in meal_plan_items}

    all_items = db.query(MealPlanItem).all()
    occupied_slots = {
        (item.plan_date, item.meal_type): item.id
        for item in all_items
        if item.id not in unique_ids
    }

    for payload in data.items:
        item = meal_plan_by_id[payload.id]

        new_plan_date = payload.plan_date if payload.plan_date is not None else item.plan_date

        if payload.meal_type is not None:
            meal_type_clean = payload.meal_type.strip().lower()
            if not meal_type_clean:
                raise HTTPException(status_code=400, detail="O tipo de refeição é obrigatório.")
            new_meal_type = meal_type_clean
        else:
            new_meal_type = item.meal_type

        new_recipe_id = payload.recipe_id if payload.recipe_id is not None else item.recipe_id

        if payload.recipe_id is not None:
            recipe = db.query(Recipe).filter(Recipe.id == payload.recipe_id).first()
            if not recipe:
                raise HTTPException(
                    status_code=404,
                    detail=f"Receita não encontrada: {payload.recipe_id}",
                )

        slot_key = (new_plan_date, new_meal_type)
        if slot_key in occupied_slots:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Conflito no plano semanal para data {new_plan_date} "
                    f"e refeição {new_meal_type}."
                ),
            )

        occupied_slots[slot_key] = item.id

        item.plan_date = new_plan_date
        item.meal_type = new_meal_type
        item.recipe_id = new_recipe_id

        if "notes" in payload.model_fields_set:
            item.notes = payload.notes

    db.commit()

    updated_items = (
        db.query(MealPlanItem)
        .options(joinedload(MealPlanItem.recipe))
        .filter(MealPlanItem.id.in_(ids))
        .order_by(MealPlanItem.plan_date.asc(), MealPlanItem.id.asc())
        .all()
    )

    return updated_items