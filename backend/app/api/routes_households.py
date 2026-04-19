from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from backend.app.db.session import get_db
from backend.app.models.family_member import FamilyMember
from backend.app.models.household import Household
from backend.app.models.meal_feedback import MealFeedback
from backend.app.models.meal_plan_item import MealPlanItem
from backend.app.models.recipe_preference import RecipePreference
from backend.app.schemas.family_member import FamilyMemberCreate, FamilyMemberRead
from backend.app.schemas.household import HouseholdCreate, HouseholdRead, HouseholdDetail
from backend.app.schemas.household_manage import HouseholdUpdate, FamilyMemberUpdate

router = APIRouter(prefix="/households", tags=["households"])


@router.get("/", response_model=list[HouseholdRead])
def list_households(db: Session = Depends(get_db)):
    households = db.query(Household).order_by(Household.name.asc()).all()
    return households


@router.post("/", response_model=HouseholdRead, status_code=201)
def create_household(data: HouseholdCreate, db: Session = Depends(get_db)):
    name_clean = data.name.strip()

    if not name_clean:
        raise HTTPException(status_code=400, detail="O nome do agregado é obrigatório.")

    existing = db.query(Household).filter(Household.name == name_clean).first()
    if existing:
        raise HTTPException(status_code=400, detail="Esse agregado já existe.")

    household = Household(name=name_clean)
    db.add(household)
    db.commit()
    db.refresh(household)

    return household


@router.patch("/{household_id}", response_model=HouseholdRead)
def update_household(
    household_id: int,
    data: HouseholdUpdate,
    db: Session = Depends(get_db),
):
    household = db.query(Household).filter(Household.id == household_id).first()
    if not household:
        raise HTTPException(status_code=404, detail="Agregado não encontrado.")

    if data.name is not None:
        name_clean = data.name.strip()
        if not name_clean:
            raise HTTPException(status_code=400, detail="O nome do agregado é obrigatório.")

        existing = (
            db.query(Household)
            .filter(Household.name == name_clean, Household.id != household_id)
            .first()
        )
        if existing:
            raise HTTPException(status_code=400, detail="Esse agregado já existe.")

        household.name = name_clean

    db.commit()
    db.refresh(household)

    return household


@router.delete("/{household_id}")
def delete_household(
    household_id: int,
    db: Session = Depends(get_db),
):
    household = db.query(Household).filter(Household.id == household_id).first()
    if not household:
        raise HTTPException(status_code=404, detail="Agregado não encontrado.")

    has_members = (
        db.query(FamilyMember)
        .filter(FamilyMember.household_id == household_id)
        .first()
    )
    if has_members:
        raise HTTPException(
            status_code=400,
            detail="Não é possível apagar um agregado que ainda tem membros.",
        )

    has_meal_plan = (
        db.query(MealPlanItem)
        .filter(MealPlanItem.household_id == household_id)
        .first()
    )
    if has_meal_plan:
        raise HTTPException(
            status_code=400,
            detail="Não é possível apagar um agregado que ainda tem refeições planeadas.",
        )

    has_preferences = (
        db.query(RecipePreference)
        .filter(RecipePreference.household_id == household_id)
        .first()
    )
    if has_preferences:
        raise HTTPException(
            status_code=400,
            detail="Não é possível apagar um agregado que ainda tem avaliações de receitas.",
        )

    db.delete(household)
    db.commit()

    return {"message": "Agregado apagado com sucesso."}


@router.get("/{household_id}", response_model=HouseholdDetail)
def get_household(household_id: int, db: Session = Depends(get_db)):
    household = (
        db.query(Household)
        .options(joinedload(Household.members))
        .filter(Household.id == household_id)
        .first()
    )

    if not household:
        raise HTTPException(status_code=404, detail="Agregado não encontrado.")

    return household


@router.get("/{household_id}/members", response_model=list[FamilyMemberRead])
def list_household_members(household_id: int, db: Session = Depends(get_db)):
    household = db.query(Household).filter(Household.id == household_id).first()
    if not household:
        raise HTTPException(status_code=404, detail="Agregado não encontrado.")

    members = (
        db.query(FamilyMember)
        .filter(FamilyMember.household_id == household_id)
        .order_by(FamilyMember.name.asc())
        .all()
    )
    return members


@router.post("/{household_id}/members", response_model=FamilyMemberRead, status_code=201)
def create_household_member(
    household_id: int,
    data: FamilyMemberCreate,
    db: Session = Depends(get_db),
):
    household = db.query(Household).filter(Household.id == household_id).first()
    if not household:
        raise HTTPException(status_code=404, detail="Agregado não encontrado.")

    name_clean = data.name.strip()
    if not name_clean:
        raise HTTPException(status_code=400, detail="O nome do membro é obrigatório.")

    existing = (
        db.query(FamilyMember)
        .filter(
            FamilyMember.household_id == household_id,
            FamilyMember.name == name_clean,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Esse membro já existe neste agregado.",
        )

    member = FamilyMember(
        name=name_clean,
        household_id=household_id,
    )

    db.add(member)
    db.commit()
    db.refresh(member)

    return member


@router.patch("/{household_id}/members/{member_id}", response_model=FamilyMemberRead)
def update_household_member(
    household_id: int,
    member_id: int,
    data: FamilyMemberUpdate,
    db: Session = Depends(get_db),
):
    household = db.query(Household).filter(Household.id == household_id).first()
    if not household:
        raise HTTPException(status_code=404, detail="Agregado não encontrado.")

    member = (
        db.query(FamilyMember)
        .filter(
            FamilyMember.id == member_id,
            FamilyMember.household_id == household_id,
        )
        .first()
    )
    if not member:
        raise HTTPException(status_code=404, detail="Membro não encontrado.")

    if data.name is not None:
        name_clean = data.name.strip()
        if not name_clean:
            raise HTTPException(status_code=400, detail="O nome do membro é obrigatório.")

        existing = (
            db.query(FamilyMember)
            .filter(
                FamilyMember.household_id == household_id,
                FamilyMember.name == name_clean,
                FamilyMember.id != member_id,
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Esse membro já existe neste agregado.",
            )

        member.name = name_clean

    db.commit()
    db.refresh(member)

    return member


@router.delete("/{household_id}/members/{member_id}")
def delete_household_member(
    household_id: int,
    member_id: int,
    db: Session = Depends(get_db),
):
    household = db.query(Household).filter(Household.id == household_id).first()
    if not household:
        raise HTTPException(status_code=404, detail="Agregado não encontrado.")

    member = (
        db.query(FamilyMember)
        .filter(
            FamilyMember.id == member_id,
            FamilyMember.household_id == household_id,
        )
        .first()
    )
    if not member:
        raise HTTPException(status_code=404, detail="Membro não encontrado.")

    has_feedback = (
        db.query(MealFeedback)
        .filter(MealFeedback.family_member_id == member_id)
        .first()
    )
    if has_feedback:
        raise HTTPException(
            status_code=400,
            detail="Não é possível apagar um membro que já tem feedback associado.",
        )

    has_preferences = (
        db.query(RecipePreference)
        .filter(RecipePreference.family_member_id == member_id)
        .first()
    )
    if has_preferences:
        raise HTTPException(
            status_code=400,
            detail="Não é possível apagar um membro que já tem avaliações de receitas associadas.",
        )

    db.delete(member)
    db.commit()

    return {"message": "Membro apagado com sucesso."}