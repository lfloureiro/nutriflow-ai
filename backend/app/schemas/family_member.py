from pydantic import BaseModel, ConfigDict


class FamilyMemberCreate(BaseModel):
    name: str


class FamilyMemberRead(BaseModel):
    id: int
    name: str
    household_id: int

    model_config = ConfigDict(from_attributes=True)