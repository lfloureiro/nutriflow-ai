from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from backend.app.db.session import get_db
from backend.app.models.family_member import FamilyMember
from backend.app.models.household import Household
from backend.app.models.recipe import Recipe
from backend.app.models.recipe_preference import RecipePreference
from backend.app.schemas.recipe_preference import (
    RecipePreferenceRead,
    RecipePreferenceSummaryRead,
    RecipePreferenceUpsert,
)
from backend.app.services.recipe_preference_scoring import (
    build_recipe_preference_score_summary,
)

router = APIRouter(prefix="/recipe-preferences", tags=["recipe-preferences"])


def _validate_household_member_and_recipe(
    db: Session,
    household_id: int,
    member_id: int,
    recipe_id: int,
) -> tuple[Household, FamilyMember, Recipe]:
    household = db.query(Household).filter(Household.id == household_id).first()
    if not household:
        raise HTTPException(status_code=404, detail="Agregado não encontrado.")

    member = db.query(FamilyMember).filter(FamilyMember.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Membro da família não encontrado.")

    if member.household_id != household_id:
        raise HTTPException(
            status_code=400,
            detail="O membro não pertence ao agregado selecionado.",
        )

    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Receita não encontrada.")

    return household, member, recipe


def _build_recipe_preference_summary_read(
    *,
    household_id: int,
    recipe: Recipe,
    preferences: list[RecipePreference],
) -> RecipePreferenceSummaryRead:
    score_summary = build_recipe_preference_score_summary(preferences)

    return RecipePreferenceSummaryRead(
        household_id=household_id,
        recipe_id=recipe.id,
        recipe_name=recipe.name,
        ratings_count=score_summary.ratings_count,
        average_rating=score_summary.effective_rating,
        simple_average_rating=score_summary.average_rating,
        median_rating=score_summary.median_rating,
        lowest_rating=score_summary.lowest_rating,
        highest_rating=score_summary.highest_rating,
        base_rating=score_summary.base_rating,
        disagreement_penalty=score_summary.disagreement_penalty,
        disagreement_spread=score_summary.disagreement_spread,
        conflict_flag=score_summary.conflict_flag,
        ratings=preferences,
    )


@router.get(
    "/households/{household_id}/recipes/{recipe_id}",
    response_model=list[RecipePreferenceRead],
)
def list_recipe_preferences_for_household_recipe(
    household_id: int,
    recipe_id: int,
    db: Session = Depends(get_db),
):
    household = db.query(Household).filter(Household.id == household_id).first()
    if not household:
        raise HTTPException(status_code=404, detail="Agregado não encontrado.")

    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Receita não encontrada.")

    preferences = (
        db.query(RecipePreference)
        .options(joinedload(RecipePreference.family_member))
        .filter(
            RecipePreference.household_id == household_id,
            RecipePreference.recipe_id == recipe_id,
        )
        .order_by(RecipePreference.family_member_id.asc())
        .all()
    )

    return preferences


@router.put(
    "/households/{household_id}/recipes/{recipe_id}/members/{member_id}",
    response_model=RecipePreferenceRead,
)
def upsert_recipe_preference(
    household_id: int,
    recipe_id: int,
    member_id: int,
    data: RecipePreferenceUpsert,
    db: Session = Depends(get_db),
):
    _validate_household_member_and_recipe(db, household_id, member_id, recipe_id)

    preference = (
        db.query(RecipePreference)
        .filter(
            RecipePreference.household_id == household_id,
            RecipePreference.family_member_id == member_id,
            RecipePreference.recipe_id == recipe_id,
        )
        .first()
    )

    if preference is None:
        preference = RecipePreference(
            household_id=household_id,
            family_member_id=member_id,
            recipe_id=recipe_id,
            rating=data.rating,
            note=data.note,
            updated_at=datetime.utcnow(),
        )
        db.add(preference)
    else:
        preference.rating = data.rating
        preference.note = data.note
        preference.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(preference)

    preference = (
        db.query(RecipePreference)
        .options(joinedload(RecipePreference.family_member))
        .filter(RecipePreference.id == preference.id)
        .first()
    )

    return preference


@router.delete("/households/{household_id}/recipes/{recipe_id}/members/{member_id}")
def delete_recipe_preference(
    household_id: int,
    recipe_id: int,
    member_id: int,
    db: Session = Depends(get_db),
):
    preference = (
        db.query(RecipePreference)
        .filter(
            RecipePreference.household_id == household_id,
            RecipePreference.family_member_id == member_id,
            RecipePreference.recipe_id == recipe_id,
        )
        .first()
    )

    if not preference:
        raise HTTPException(status_code=404, detail="Avaliação não encontrada.")

    db.delete(preference)
    db.commit()

    return {"message": "Avaliação apagada com sucesso."}


@router.get(
    "/households/{household_id}/recipes/{recipe_id}/summary",
    response_model=RecipePreferenceSummaryRead,
)
def get_recipe_preference_summary(
    household_id: int,
    recipe_id: int,
    db: Session = Depends(get_db),
):
    household = db.query(Household).filter(Household.id == household_id).first()
    if not household:
        raise HTTPException(status_code=404, detail="Agregado não encontrado.")

    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Receita não encontrada.")

    preferences = (
        db.query(RecipePreference)
        .options(joinedload(RecipePreference.family_member))
        .filter(
            RecipePreference.household_id == household_id,
            RecipePreference.recipe_id == recipe_id,
        )
        .order_by(RecipePreference.family_member_id.asc())
        .all()
    )

    return _build_recipe_preference_summary_read(
        household_id=household_id,
        recipe=recipe,
        preferences=preferences,
    )


@router.get(
    "/households/{household_id}/summaries",
    response_model=list[RecipePreferenceSummaryRead],
)
def list_household_recipe_summaries(
    household_id: int,
    db: Session = Depends(get_db),
):
    household = db.query(Household).filter(Household.id == household_id).first()
    if not household:
        raise HTTPException(status_code=404, detail="Agregado não encontrado.")

    recipes = db.query(Recipe).order_by(Recipe.name.asc()).all()

    result: list[RecipePreferenceSummaryRead] = []

    for recipe in recipes:
        preferences = (
            db.query(RecipePreference)
            .options(joinedload(RecipePreference.family_member))
            .filter(
                RecipePreference.household_id == household_id,
                RecipePreference.recipe_id == recipe.id,
            )
            .order_by(RecipePreference.family_member_id.asc())
            .all()
        )

        result.append(
            _build_recipe_preference_summary_read(
                household_id=household_id,
                recipe=recipe,
                preferences=preferences,
            )
        )

    return result