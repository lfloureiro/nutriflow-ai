from pydantic import BaseModel, Field


class HouseholdUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)


class FamilyMemberUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)