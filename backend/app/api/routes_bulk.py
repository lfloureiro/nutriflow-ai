from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from backend.app.db.session import get_db
from backend.app.models.family_member import FamilyMember
from backend.app.models.household import Household
from backend.app.models.ingredient import Ingredient
from backend.app.models.meal_feedback import MealFeedback
from backend.app.models.meal_plan_item import MealPlanItem
from backend.app.models.recipe import Recipe
from backend.app.models.recipe_ingredient import RecipeIngredient
from backend.app.schemas.bulk import (
    BulkDeleteRequest,
    BulkDeleteResult,
    BulkFamilyMemberImportRequest,
    BulkFeedbackImportRequest,
    BulkHouseholdImportRequest,
    BulkImportResult,
    BulkIngredientImportRequest,
    BulkMealPlanImportRequest,
    BulkMealPlanUpdateRequest,
    BulkRecipeImportRequest,
    BulkRecipeIngredientImportRequest,
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


@router.post("/households/import", response_model=BulkImportResult)
def bulk_import_households(
    data: BulkHouseholdImportRequest,
    db: Session = Depends(get_db),
):
    if not data.items:
        raise HTTPException(status_code=400, detail="Não foram enviados agregados.")

    created = 0
    skipped = 0

    for item in data.items:
        name_clean = item.name.strip()

        if not name_clean:
            raise HTTPException(status_code=400, detail="Todos os agregados têm de ter nome.")

        existing = db.query(Household).filter(Household.name == name_clean).first()
        if existing:
            if data.skip_existing:
                skipped += 1
                continue
            raise HTTPException(
                status_code=400,
                detail=f"O agregado '{name_clean}' já existe.",
            )

        db.add(Household(name=name_clean))
        created += 1

    db.commit()

    return BulkImportResult(
        total_received=len(data.items),
        created=created,
        skipped=skipped,
    )


@router.post("/family-members/import", response_model=BulkImportResult)
def bulk_import_family_members(
    data: BulkFamilyMemberImportRequest,
    db: Session = Depends(get_db),
):
    if not data.items:
        raise HTTPException(status_code=400, detail="Não foram enviados membros.")

    created = 0
    skipped = 0

    for item in data.items:
        name_clean = item.name.strip()

        if not name_clean:
            raise HTTPException(status_code=400, detail="Todos os membros têm de ter nome.")

        household = db.query(Household).filter(Household.id == item.household_id).first()
        if not household:
            raise HTTPException(
                status_code=404,
                detail=f"Agregado não encontrado: {item.household_id}",
            )

        existing = (
            db.query(FamilyMember)
            .filter(
                FamilyMember.household_id == item.household_id,
                FamilyMember.name == name_clean,
            )
            .first()
        )
        if existing:
            if data.skip_existing:
                skipped += 1
                continue
            raise HTTPException(
                status_code=400,
                detail=f"O membro '{name_clean}' já existe nesse agregado.",
            )

        db.add(FamilyMember(name=name_clean, household_id=item.household_id))
        created += 1

    db.commit()

    return BulkImportResult(
        total_received=len(data.items),
        created=created,
        skipped=skipped,
    )


@router.post("/recipe-ingredients/import", response_model=BulkImportResult)
def bulk_import_recipe_ingredients(
    data: BulkRecipeIngredientImportRequest,
    db: Session = Depends(get_db),
):
    if not data.items:
        raise HTTPException(
            status_code=400,
            detail="Não foram enviadas ligações receita-ingrediente.",
        )

    created = 0
    skipped = 0

    for item in data.items:
        recipe = db.query(Recipe).filter(Recipe.id == item.recipe_id).first()
        if not recipe:
            raise HTTPException(
                status_code=404,
                detail=f"Receita não encontrada: {item.recipe_id}",
            )

        ingredient = db.query(Ingredient).filter(Ingredient.id == item.ingredient_id).first()
        if not ingredient:
            raise HTTPException(
                status_code=404,
                detail=f"Ingrediente não encontrado: {item.ingredient_id}",
            )

        existing = (
            db.query(RecipeIngredient)
            .filter(
                RecipeIngredient.recipe_id == item.recipe_id,
                RecipeIngredient.ingredient_id == item.ingredient_id,
            )
            .first()
        )
        if existing:
            if data.skip_existing:
                skipped += 1
                continue
            raise HTTPException(
                status_code=400,
                detail=(
                    f"O ingrediente {item.ingredient_id} já está associado "
                    f"à receita {item.recipe_id}."
                ),
            )

        db.add(
            RecipeIngredient(
                recipe_id=item.recipe_id,
                ingredient_id=item.ingredient_id,
                quantity=item.quantity,
                unit=item.unit,
            )
        )
        created += 1

    db.commit()

    return BulkImportResult(
        total_received=len(data.items),
        created=created,
        skipped=skipped,
    )


@router.post("/meal-plan/import", response_model=BulkImportResult)
def bulk_import_meal_plan(
    data: BulkMealPlanImportRequest,
    db: Session = Depends(get_db),
):
    if not data.items:
        raise HTTPException(status_code=400, detail="Não foram enviados itens do plano semanal.")

    created = 0
    skipped = 0

    occupied_slots = {
        (item.household_id, item.plan_date, item.meal_type.strip().lower()): item.id
        for item in db.query(MealPlanItem).all()
    }

    for item in data.items:
        meal_type_clean = item.meal_type.strip().lower()
        if not meal_type_clean:
            raise HTTPException(status_code=400, detail="O tipo de refeição é obrigatório.")

        household = db.query(Household).filter(Household.id == item.household_id).first()
        if not household:
            raise HTTPException(
                status_code=404,
                detail=f"Agregado não encontrado: {item.household_id}",
            )

        recipe = db.query(Recipe).filter(Recipe.id == item.recipe_id).first()
        if not recipe:
            raise HTTPException(
                status_code=404,
                detail=f"Receita não encontrada: {item.recipe_id}",
            )

        slot_key = (item.household_id, item.plan_date, meal_type_clean)

        if slot_key in occupied_slots:
            if data.skip_existing:
                skipped += 1
                continue
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Já existe uma refeição para o agregado {item.household_id}, "
                    f"na data {item.plan_date} e tipo {meal_type_clean}."
                ),
            )

        db.add(
            MealPlanItem(
                household_id=item.household_id,
                plan_date=item.plan_date,
                meal_type=meal_type_clean,
                notes=item.notes,
                recipe_id=item.recipe_id,
            )
        )
        occupied_slots[slot_key] = -1
        created += 1

    db.commit()

    return BulkImportResult(
        total_received=len(data.items),
        created=created,
        skipped=skipped,
    )


@router.post("/feedback/import", response_model=BulkImportResult)
def bulk_import_feedback(
    data: BulkFeedbackImportRequest,
    db: Session = Depends(get_db),
):
    if not data.items:
        raise HTTPException(status_code=400, detail="Não foram enviados feedbacks.")

    created = 0
    skipped = 0

    for item in data.items:
        meal_plan_item = (
            db.query(MealPlanItem)
            .filter(MealPlanItem.id == item.meal_plan_item_id)
            .first()
        )
        if not meal_plan_item:
            raise HTTPException(
                status_code=404,
                detail=f"Refeição planeada não encontrada: {item.meal_plan_item_id}",
            )

        family_member = (
            db.query(FamilyMember)
            .filter(FamilyMember.id == item.family_member_id)
            .first()
        )
        if not family_member:
            raise HTTPException(
                status_code=404,
                detail=f"Membro da família não encontrado: {item.family_member_id}",
            )

        if family_member.household_id != meal_plan_item.household_id:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"O membro {item.family_member_id} não pertence ao mesmo agregado "
                    f"da refeição {item.meal_plan_item_id}."
                ),
            )

        existing = (
            db.query(MealFeedback)
            .filter(
                MealFeedback.meal_plan_item_id == item.meal_plan_item_id,
                MealFeedback.family_member_id == item.family_member_id,
            )
            .first()
        )
        if existing:
            if data.skip_existing:
                skipped += 1
                continue
            raise HTTPException(
                status_code=400,
                detail=(
                    f"O membro {item.family_member_id} já tem feedback "
                    f"para a refeição {item.meal_plan_item_id}."
                ),
            )

        db.add(
            MealFeedback(
                meal_plan_item_id=item.meal_plan_item_id,
                family_member_id=item.family_member_id,
                reaction=item.reaction,
                note=item.note,
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
        (item.household_id, item.plan_date, item.meal_type.strip().lower()): item.id
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
            new_meal_type = item.meal_type.strip().lower()

        new_recipe_id = payload.recipe_id if payload.recipe_id is not None else item.recipe_id

        if payload.recipe_id is not None:
            recipe = db.query(Recipe).filter(Recipe.id == payload.recipe_id).first()
            if not recipe:
                raise HTTPException(
                    status_code=404,
                    detail=f"Receita não encontrada: {payload.recipe_id}",
                )

        slot_key = (item.household_id, new_plan_date, new_meal_type)
        if slot_key in occupied_slots:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Conflito no plano semanal para o agregado {item.household_id}, "
                    f"data {new_plan_date} e refeição {new_meal_type}."
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


@router.post("/meal-plan/delete", response_model=BulkDeleteResult)
def bulk_delete_meal_plan(
    data: BulkDeleteRequest,
    db: Session = Depends(get_db),
):
    if not data.ids:
        raise HTTPException(status_code=400, detail="Não foram enviados IDs para apagar.")

    ids = list(dict.fromkeys(data.ids))

    items = (
        db.query(MealPlanItem)
        .filter(MealPlanItem.id.in_(ids))
        .all()
    )

    if len(items) != len(ids):
        found_ids = {item.id for item in items}
        missing_ids = [item_id for item_id in ids if item_id not in found_ids]
        raise HTTPException(
            status_code=404,
            detail=f"Itens do plano não encontrados: {missing_ids}",
        )

    for item in items:
        db.delete(item)

    db.commit()

    return BulkDeleteResult(
        requested=len(ids),
        deleted=len(items),
    )


@router.post("/feedback/delete", response_model=BulkDeleteResult)
def bulk_delete_feedback(
    data: BulkDeleteRequest,
    db: Session = Depends(get_db),
):
    if not data.ids:
        raise HTTPException(status_code=400, detail="Não foram enviados IDs para apagar.")

    ids = list(dict.fromkeys(data.ids))

    feedback_items = (
        db.query(MealFeedback)
        .filter(MealFeedback.id.in_(ids))
        .all()
    )

    if len(feedback_items) != len(ids):
        found_ids = {item.id for item in feedback_items}
        missing_ids = [item_id for item_id in ids if item_id not in found_ids]
        raise HTTPException(
            status_code=404,
            detail=f"Feedback não encontrado para os IDs: {missing_ids}",
        )

    for item in feedback_items:
        db.delete(item)

    db.commit()

    return BulkDeleteResult(
        requested=len(ids),
        deleted=len(feedback_items),
    )