from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from backend.app.db.session import get_db
from backend.app.models.family_member import FamilyMember
from backend.app.models.meal_feedback import MealFeedback
from backend.app.models.meal_plan_item import MealPlanItem
from backend.app.models.recipe import Recipe
from backend.app.schemas.meal_feedback import (
    MealFeedbackCreate,
    MealFeedbackRead,
    MealFeedbackUpdate,
    RecipeFeedbackSummaryRead,
)

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.get("/meal-plan/{meal_plan_item_id}", response_model=list[MealFeedbackRead])
def list_meal_feedback(meal_plan_item_id: int, db: Session = Depends(get_db)):
    meal_item = db.query(MealPlanItem).filter(MealPlanItem.id == meal_plan_item_id).first()
    if not meal_item:
        raise HTTPException(status_code=404, detail="Refeição planeada não encontrada.")

    feedback = (
        db.query(MealFeedback)
        .options(joinedload(MealFeedback.family_member))
        .filter(MealFeedback.meal_plan_item_id == meal_plan_item_id)
        .order_by(MealFeedback.id.asc())
        .all()
    )
    return feedback


@router.post("/meal-plan/{meal_plan_item_id}", response_model=MealFeedbackRead, status_code=201)
def create_meal_feedback(
    meal_plan_item_id: int,
    data: MealFeedbackCreate,
    db: Session = Depends(get_db),
):
    meal_item = db.query(MealPlanItem).filter(MealPlanItem.id == meal_plan_item_id).first()
    if not meal_item:
        raise HTTPException(status_code=404, detail="Refeição planeada não encontrada.")

    member = db.query(FamilyMember).filter(FamilyMember.id == data.family_member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Membro da família não encontrado.")

    existing = (
        db.query(MealFeedback)
        .filter(
            MealFeedback.meal_plan_item_id == meal_plan_item_id,
            MealFeedback.family_member_id == data.family_member_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Esse membro já deu feedback para esta refeição.",
        )

    feedback = MealFeedback(
        meal_plan_item_id=meal_plan_item_id,
        family_member_id=data.family_member_id,
        reaction=data.reaction,
        note=data.note,
    )

    db.add(feedback)
    db.commit()
    db.refresh(feedback)

    feedback = (
        db.query(MealFeedback)
        .options(joinedload(MealFeedback.family_member))
        .filter(MealFeedback.id == feedback.id)
        .first()
    )

    return feedback


@router.patch("/{feedback_id}", response_model=MealFeedbackRead)
def update_meal_feedback(
    feedback_id: int,
    data: MealFeedbackUpdate,
    db: Session = Depends(get_db),
):
    feedback = db.query(MealFeedback).filter(MealFeedback.id == feedback_id).first()
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback não encontrado.")

    new_family_member_id = (
        data.family_member_id if data.family_member_id is not None else feedback.family_member_id
    )

    if data.family_member_id is not None:
        member = db.query(FamilyMember).filter(FamilyMember.id == data.family_member_id).first()
        if not member:
            raise HTTPException(status_code=404, detail="Membro da família não encontrado.")

    existing = (
        db.query(MealFeedback)
        .filter(
            MealFeedback.meal_plan_item_id == feedback.meal_plan_item_id,
            MealFeedback.family_member_id == new_family_member_id,
            MealFeedback.id != feedback_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Esse membro já deu feedback para esta refeição.",
        )

    feedback.family_member_id = new_family_member_id

    if data.reaction is not None:
        feedback.reaction = data.reaction

    if "note" in data.model_fields_set:
        feedback.note = data.note

    db.commit()
    db.refresh(feedback)

    feedback = (
        db.query(MealFeedback)
        .options(joinedload(MealFeedback.family_member))
        .filter(MealFeedback.id == feedback.id)
        .first()
    )

    return feedback


@router.delete("/{feedback_id}")
def delete_meal_feedback(
    feedback_id: int,
    db: Session = Depends(get_db),
):
    feedback = db.query(MealFeedback).filter(MealFeedback.id == feedback_id).first()
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback não encontrado.")

    db.delete(feedback)
    db.commit()

    return {"message": "Feedback apagado com sucesso."}


@router.get("/recipes/{recipe_id}/summary", response_model=RecipeFeedbackSummaryRead)
def get_recipe_feedback_summary(recipe_id: int, db: Session = Depends(get_db)):
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Receita não encontrada.")

    feedback_entries = (
        db.query(MealFeedback)
        .join(MealPlanItem, MealFeedback.meal_plan_item_id == MealPlanItem.id)
        .filter(MealPlanItem.recipe_id == recipe_id)
        .all()
    )

    liked_count = sum(1 for f in feedback_entries if f.reaction == "gostou")
    neutral_count = sum(1 for f in feedback_entries if f.reaction == "neutro")
    disliked_count = sum(1 for f in feedback_entries if f.reaction == "nao_gostou")
    total_feedback = len(feedback_entries)

    if total_feedback == 0:
        acceptance_score = 0.0
    else:
        acceptance_score = round(
            ((liked_count * 1.0) + (neutral_count * 0.5)) / total_feedback * 100,
            2,
        )

    return RecipeFeedbackSummaryRead(
        recipe_id=recipe.id,
        recipe_name=recipe.name,
        total_feedback=total_feedback,
        liked_count=liked_count,
        neutral_count=neutral_count,
        disliked_count=disliked_count,
        acceptance_score=acceptance_score,
    )