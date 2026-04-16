from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from backend.app.db.session import get_db
from backend.app.models.family_member import FamilyMember
from backend.app.models.household import Household
from backend.app.schemas.family_member import FamilyMemberCreate, FamilyMemberRead
from backend.app.schemas.household import HouseholdCreate, HouseholdRead, HouseholdDetail

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