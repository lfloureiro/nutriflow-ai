from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from backend.app.db.session import get_db
from backend.app.models.household import Household
from backend.app.models.meal_plan_item import MealPlanItem
from backend.app.models.recipe import Recipe
from backend.app.schemas.meal_plan import (
    MealPlanItemRead,
    NextMealSlotRead,
)
from backend.app.schemas.meal_plan_auto import (
    AutoMealPlanAdjustedApplyRead,
    AutoMealPlanAdjustedRequest,
    AutoMealPlanApplyRead,
    AutoMealPlanPreviewRead,
    AutoMealPlanRequest,
    AutoMealPlanSuggestionRead,
)
from backend.app.schemas.meal_plan_manage import (
    MealPlanItemCreateScoped,
    MealPlanItemUpdateScoped,
)
from backend.app.services.auto_meal_planner import (
    PlannerSuggestion,
    build_auto_meal_plan_preview,
    normalize_meal_types,
)
from backend.app.services.auto_meal_plan_logging import (
    ApplyExecutionResult,
    detach_meal_plan_item_from_logs,
    get_latest_auto_plan_apply_event,
    log_auto_meal_plan_run,
    log_post_apply_lifecycle_event,
    snapshot_meal_plan_item,
)

router = APIRouter(prefix="/meal-plan", tags=["meal-plan"])

MEAL_SLOT_ORDER = [
    ("pequeno-almoco", time(8, 0)),
    ("almoco", time(13, 0)),
    ("lanche", time(17, 0)),
    ("jantar", time(20, 0)),
]

MEAL_TYPE_SORT_ORDER = {
    "pequeno-almoco": 0,
    "almoco": 1,
    "lanche": 2,
    "jantar": 3,
}


def meal_type_sort_key(value: str) -> int:
    return MEAL_TYPE_SORT_ORDER.get(value, 99)


def get_next_available_slot(db: Session, household_id: int) -> tuple[date, str]:
    now = datetime.now()

    existing_items = (
        db.query(MealPlanItem)
        .filter(
            MealPlanItem.household_id == household_id,
            MealPlanItem.plan_date >= now.date(),
        )
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


def build_suggestion_read(
    *,
    plan_date: date,
    meal_type: str,
    action: str,
    recipe: Recipe | None,
    score: float | None,
    average_rating: float | None,
    ratings_count: int,
    reasons: list[str],
) -> AutoMealPlanSuggestionRead:
    return AutoMealPlanSuggestionRead(
        plan_date=plan_date,
        meal_type=meal_type,
        action=action,
        recipe_id=recipe.id if recipe else None,
        recipe_name=recipe.name if recipe else None,
        categoria_alimentar=recipe.categoria_alimentar if recipe else None,
        proteina_principal=recipe.proteina_principal if recipe else None,
        score=score,
        average_rating=average_rating,
        ratings_count=ratings_count,
        reasons=reasons,
    )


def suggestion_to_read(item: PlannerSuggestion) -> AutoMealPlanSuggestionRead:
    return build_suggestion_read(
        plan_date=item.plan_date,
        meal_type=item.meal_type,
        action=item.action,
        recipe=item.recipe,
        score=item.score,
        average_rating=item.average_rating,
        ratings_count=item.ratings_count,
        reasons=item.reasons,
    )


@router.get("/next-slot", response_model=NextMealSlotRead)
def get_next_meal_slot(
    household_id: int = Query(...),
    db: Session = Depends(get_db),
):
    household = db.query(Household).filter(Household.id == household_id).first()
    if not household:
        raise HTTPException(status_code=404, detail="Agregado não encontrado.")

    plan_date, meal_type = get_next_available_slot(db, household_id)
    return NextMealSlotRead(plan_date=plan_date, meal_type=meal_type)


@router.get("/", response_model=list[MealPlanItemRead])
def list_meal_plan(
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
        .options(joinedload(MealPlanItem.recipe))
        .filter(MealPlanItem.household_id == household_id)
    )

    if start_date:
        query = query.filter(MealPlanItem.plan_date >= start_date)

    if end_date:
        query = query.filter(MealPlanItem.plan_date <= end_date)

    items = query.order_by(MealPlanItem.plan_date.asc(), MealPlanItem.id.asc()).all()
    return items


@router.post("/", response_model=MealPlanItemRead, status_code=201)
def create_meal_plan_item(
    data: MealPlanItemCreateScoped,
    db: Session = Depends(get_db),
):
    household = db.query(Household).filter(Household.id == data.household_id).first()
    if not household:
        raise HTTPException(status_code=404, detail="Agregado não encontrado.")

    recipe = db.query(Recipe).filter(Recipe.id == data.recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Receita não encontrada.")

    meal_type_clean = data.meal_type.strip().lower()
    if not meal_type_clean:
        raise HTTPException(status_code=400, detail="O tipo de refeição é obrigatório.")

    item = MealPlanItem(
        household_id=data.household_id,
        plan_date=date.fromisoformat(data.plan_date),
        meal_type=meal_type_clean,
        notes=data.notes,
        recipe_id=data.recipe_id,
    )

    existing = (
        db.query(MealPlanItem)
        .filter(
            MealPlanItem.household_id == data.household_id,
            MealPlanItem.plan_date == item.plan_date,
            MealPlanItem.meal_type == meal_type_clean,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Já existe uma refeição planeada para essa data e esse tipo de refeição neste agregado.",
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
    data: MealPlanItemUpdateScoped,
    db: Session = Depends(get_db),
):
    item = db.query(MealPlanItem).filter(MealPlanItem.id == meal_plan_item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Refeição planeada não encontrada.")

    before_snapshot = snapshot_meal_plan_item(item)
    source_event = get_latest_auto_plan_apply_event(db, item.id)

    new_household_id = data.household_id if data.household_id is not None else item.household_id
    new_plan_date = date.fromisoformat(data.plan_date) if data.plan_date is not None else item.plan_date

    if data.meal_type is not None:
        meal_type_clean = data.meal_type.strip().lower()
        if not meal_type_clean:
            raise HTTPException(status_code=400, detail="O tipo de refeição é obrigatório.")
        new_meal_type = meal_type_clean
    else:
        new_meal_type = item.meal_type

    new_recipe_id = data.recipe_id if data.recipe_id is not None else item.recipe_id

    household = db.query(Household).filter(Household.id == new_household_id).first()
    if not household:
        raise HTTPException(status_code=404, detail="Agregado não encontrado.")

    if data.recipe_id is not None:
        recipe = db.query(Recipe).filter(Recipe.id == data.recipe_id).first()
        if not recipe:
            raise HTTPException(status_code=404, detail="Receita não encontrada.")

    existing = (
        db.query(MealPlanItem)
        .filter(
            MealPlanItem.household_id == new_household_id,
            MealPlanItem.plan_date == new_plan_date,
            MealPlanItem.meal_type == new_meal_type,
            MealPlanItem.id != meal_plan_item_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Já existe uma refeição planeada para essa data e esse tipo de refeição neste agregado.",
        )

    item.household_id = new_household_id
    item.plan_date = new_plan_date
    item.meal_type = new_meal_type
    item.recipe_id = new_recipe_id

    if "notes" in data.model_fields_set:
        item.notes = data.notes

    change_reasons: list[str] = []
    if before_snapshot.household_id != item.household_id:
        change_reasons.append("household_changed")
    if before_snapshot.plan_date != item.plan_date:
        change_reasons.append("plan_date_changed")
    if before_snapshot.meal_type != item.meal_type:
        change_reasons.append("meal_type_changed")
    if before_snapshot.recipe_id != item.recipe_id:
        change_reasons.append("recipe_changed")
    if (before_snapshot.notes or "") != (item.notes or ""):
        change_reasons.append("notes_changed")

    db.flush()

    if source_event and change_reasons:
        log_post_apply_lifecycle_event(
            db=db,
            source_event=source_event,
            item_snapshot=before_snapshot,
            event_kind="post_apply_update",
            execution_status="recipe_replaced" if "recipe_changed" in change_reasons else "updated",
            final_plan_date=item.plan_date,
            final_meal_type=item.meal_type,
            final_recipe_id=item.recipe_id,
            keep_meal_plan_item_link=True,
            reasons=change_reasons,
        )

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

    source_event = get_latest_auto_plan_apply_event(db, item.id)
    before_snapshot = snapshot_meal_plan_item(item)

    if source_event:
        detach_meal_plan_item_from_logs(db, item.id)
        log_post_apply_lifecycle_event(
            db=db,
            source_event=source_event,
            item_snapshot=before_snapshot,
            event_kind="post_apply_delete",
            execution_status="deleted",
            final_plan_date=before_snapshot.plan_date,
            final_meal_type=before_snapshot.meal_type,
            final_recipe_id=None,
            keep_meal_plan_item_link=False,
            reasons=[
                "item_deleted",
                f"deleted_meal_plan_item_id={before_snapshot.meal_plan_item_id}",
            ],
        )

    db.delete(item)
    db.commit()

    return {"message": "Refeição planeada apagada com sucesso."}


@router.post("/auto-plan/preview", response_model=AutoMealPlanPreviewRead)
def preview_auto_meal_plan(
    data: AutoMealPlanRequest,
    db: Session = Depends(get_db),
):
    household = db.query(Household).filter(Household.id == data.household_id).first()
    if not household:
        raise HTTPException(status_code=404, detail="Agregado não encontrado.")

    if not data.skip_existing:
        raise HTTPException(
            status_code=400,
            detail="Nesta fase o auto-planeamento só suporta skip_existing=true.",
        )

    suggestions = build_auto_meal_plan_preview(
        db=db,
        household_id=data.household_id,
        start_date=data.start_date,
        end_date=data.end_date,
        meal_types=data.meal_types,
        skip_existing=data.skip_existing,
    )

    log_auto_meal_plan_run(
        db=db,
        household_id=data.household_id,
        event_kind="preview",
        start_date=data.start_date,
        end_date=data.end_date,
        meal_types=data.meal_types,
        skip_existing=data.skip_existing,
        suggestions=suggestions,
    )
    db.commit()

    return AutoMealPlanPreviewRead(
        household_id=data.household_id,
        start_date=data.start_date,
        end_date=data.end_date,
        meal_types=normalize_meal_types(data.meal_types),
        skip_existing=data.skip_existing,
        suggestions=[suggestion_to_read(item) for item in suggestions],
    )


@router.post("/auto-plan/apply", response_model=AutoMealPlanApplyRead)
def apply_auto_meal_plan(
    data: AutoMealPlanRequest,
    db: Session = Depends(get_db),
):
    household = db.query(Household).filter(Household.id == data.household_id).first()
    if not household:
        raise HTTPException(status_code=404, detail="Agregado não encontrado.")

    if not data.skip_existing:
        raise HTTPException(
            status_code=400,
            detail="Nesta fase o auto-planeamento só suporta skip_existing=true.",
        )

    suggestions = build_auto_meal_plan_preview(
        db=db,
        household_id=data.household_id,
        start_date=data.start_date,
        end_date=data.end_date,
        meal_types=data.meal_types,
        skip_existing=data.skip_existing,
    )

    created_count = 0
    skipped_count = 0
    apply_results: dict[tuple[date, str], ApplyExecutionResult] = {}

    for item in suggestions:
        slot_key = (item.plan_date, item.meal_type)

        if item.action != "suggest" or item.recipe is None:
            skipped_count += 1
            apply_results[slot_key] = ApplyExecutionResult(
                execution_status="skipped_non_suggest",
                final_recipe_id=item.recipe.id if item.recipe else None,
            )
            continue

        existing = (
            db.query(MealPlanItem)
            .filter(
                MealPlanItem.household_id == data.household_id,
                MealPlanItem.plan_date == item.plan_date,
                MealPlanItem.meal_type == item.meal_type,
            )
            .first()
        )

        if existing:
            skipped_count += 1
            apply_results[slot_key] = ApplyExecutionResult(
                execution_status="skipped_existing",
                meal_plan_item_id=existing.id,
                final_recipe_id=existing.recipe_id,
            )
            continue

        db_item = MealPlanItem(
            household_id=data.household_id,
            plan_date=item.plan_date,
            meal_type=item.meal_type,
            notes="Auto-planeado",
            recipe_id=item.recipe.id,
        )
        db.add(db_item)
        db.flush()

        created_count += 1
        apply_results[slot_key] = ApplyExecutionResult(
            execution_status="created",
            meal_plan_item_id=db_item.id,
            final_recipe_id=db_item.recipe_id,
        )

    log_auto_meal_plan_run(
        db=db,
        household_id=data.household_id,
        event_kind="apply",
        start_date=data.start_date,
        end_date=data.end_date,
        meal_types=data.meal_types,
        skip_existing=data.skip_existing,
        suggestions=suggestions,
        apply_results=apply_results,
    )

    db.commit()

    return AutoMealPlanApplyRead(
        household_id=data.household_id,
        start_date=data.start_date,
        end_date=data.end_date,
        meal_types=normalize_meal_types(data.meal_types),
        skip_existing=data.skip_existing,
        created_count=created_count,
        skipped_count=skipped_count,
        suggestions=[suggestion_to_read(item) for item in suggestions],
    )


@router.post("/auto-plan/apply-adjusted", response_model=AutoMealPlanAdjustedApplyRead)
def apply_adjusted_auto_meal_plan(
    data: AutoMealPlanAdjustedRequest,
    db: Session = Depends(get_db),
):
    household = db.query(Household).filter(Household.id == data.household_id).first()
    if not household:
        raise HTTPException(status_code=404, detail="Agregado não encontrado.")

    if not data.skip_existing:
        raise HTTPException(
            status_code=400,
            detail="Nesta fase o auto-planeamento só suporta skip_existing=true.",
        )

    if not data.suggestions:
        raise HTTPException(
            status_code=400,
            detail="Não existem sugestões ajustadas para aplicar.",
        )

    created_count = 0
    skipped_count = 0
    ignored_count = 0
    replaced_count = 0

    suggestions_for_logging: list[PlannerSuggestion] = []
    response_suggestions: list[AutoMealPlanSuggestionRead] = []
    apply_results: dict[tuple[date, str], ApplyExecutionResult] = {}

    sorted_suggestions = sorted(
        data.suggestions,
        key=lambda item: (item.plan_date, meal_type_sort_key(item.meal_type)),
    )

    for item in sorted_suggestions:
        meal_type_clean = item.meal_type.strip().lower()
        slot_key = (item.plan_date, meal_type_clean)

        original_recipe = None
        if item.original_recipe_id is not None:
            original_recipe = db.query(Recipe).filter(Recipe.id == item.original_recipe_id).first()
            if not original_recipe:
                raise HTTPException(status_code=404, detail="Receita original não encontrada.")

        original_suggestion = PlannerSuggestion(
            plan_date=item.plan_date,
            meal_type=meal_type_clean,
            action=item.original_action,
            recipe=original_recipe,
            score=item.score,
            average_rating=item.average_rating,
            ratings_count=item.ratings_count,
            reasons=item.reasons,
        )
        suggestions_for_logging.append(original_suggestion)

        if item.original_action != "suggest":
            skipped_count += 1
            apply_results[slot_key] = ApplyExecutionResult(
                execution_status="skipped_non_suggest",
                final_recipe_id=original_recipe.id if original_recipe else None,
            )
            response_suggestions.append(suggestion_to_read(original_suggestion))
            continue

        if item.apply_decision == "ignore":
            ignored_count += 1
            apply_results[slot_key] = ApplyExecutionResult(
                execution_status="ignored_by_user",
                final_recipe_id=None,
            )
            response_suggestions.append(
                build_suggestion_read(
                    plan_date=item.plan_date,
                    meal_type=meal_type_clean,
                    action="ignored",
                    recipe=original_recipe,
                    score=item.score,
                    average_rating=item.average_rating,
                    ratings_count=item.ratings_count,
                    reasons=item.reasons,
                )
            )
            continue

        final_recipe = original_recipe
        if item.apply_decision == "replace":
            if item.adjusted_recipe_id is None:
                raise HTTPException(
                    status_code=400,
                    detail="Falta a receita escolhida para uma substituição.",
                )

            final_recipe = db.query(Recipe).filter(Recipe.id == item.adjusted_recipe_id).first()
            if not final_recipe:
                raise HTTPException(status_code=404, detail="Receita ajustada não encontrada.")

            if original_recipe is None or final_recipe.id != original_recipe.id:
                replaced_count += 1
        else:
            if final_recipe is None:
                raise HTTPException(
                    status_code=400,
                    detail="A sugestão não tem receita original válida para manter.",
                )

        existing = (
            db.query(MealPlanItem)
            .filter(
                MealPlanItem.household_id == data.household_id,
                MealPlanItem.plan_date == item.plan_date,
                MealPlanItem.meal_type == meal_type_clean,
            )
            .first()
        )

        if existing:
            skipped_count += 1
            apply_results[slot_key] = ApplyExecutionResult(
                execution_status="skipped_existing",
                meal_plan_item_id=existing.id,
                final_recipe_id=existing.recipe_id,
            )

            existing_recipe = db.query(Recipe).filter(Recipe.id == existing.recipe_id).first()
            response_suggestions.append(
                build_suggestion_read(
                    plan_date=item.plan_date,
                    meal_type=meal_type_clean,
                    action="skip_existing",
                    recipe=existing_recipe,
                    score=item.score,
                    average_rating=item.average_rating,
                    ratings_count=item.ratings_count,
                    reasons=item.reasons,
                )
            )
            continue

        db_item = MealPlanItem(
            household_id=data.household_id,
            plan_date=item.plan_date,
            meal_type=meal_type_clean,
            notes="Auto-planeado (ajustado)" if item.apply_decision == "replace" else "Auto-planeado",
            recipe_id=final_recipe.id,
        )
        db.add(db_item)
        db.flush()

        created_count += 1
        apply_results[slot_key] = ApplyExecutionResult(
            execution_status="created",
            meal_plan_item_id=db_item.id,
            final_recipe_id=db_item.recipe_id,
        )

        response_suggestions.append(
            build_suggestion_read(
                plan_date=item.plan_date,
                meal_type=meal_type_clean,
                action="adjusted_replace" if item.apply_decision == "replace" else "suggest",
                recipe=final_recipe,
                score=item.score,
                average_rating=item.average_rating,
                ratings_count=item.ratings_count,
                reasons=item.reasons,
            )
        )

    log_auto_meal_plan_run(
        db=db,
        household_id=data.household_id,
        event_kind="apply",
        start_date=data.start_date,
        end_date=data.end_date,
        meal_types=data.meal_types,
        skip_existing=data.skip_existing,
        suggestions=suggestions_for_logging,
        apply_results=apply_results,
    )

    db.commit()

    return AutoMealPlanAdjustedApplyRead(
        household_id=data.household_id,
        start_date=data.start_date,
        end_date=data.end_date,
        meal_types=normalize_meal_types(data.meal_types),
        skip_existing=data.skip_existing,
        created_count=created_count,
        skipped_count=skipped_count,
        ignored_count=ignored_count,
        replaced_count=replaced_count,
        suggestions=response_suggestions,
    )