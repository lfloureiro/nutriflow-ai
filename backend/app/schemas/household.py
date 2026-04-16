from pydantic import BaseModel, ConfigDict

from backend.app.schemas.family_member import FamilyMemberRead


class HouseholdCreate(BaseModel):
    name: str


class HouseholdRead(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class HouseholdDetail(HouseholdRead):
    members: list[FamilyMemberRead] = []