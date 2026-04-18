from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RecipePreferenceFamilyMemberRead(BaseModel):
    id: int
    name: str
    household_id: int

    model_config = ConfigDict(from_attributes=True)


class RecipePreferenceUpsert(BaseModel):
    rating: int = Field(..., ge=0, le=5)
    note: str | None = Field(default=None, max_length=500)


class RecipePreferenceRead(BaseModel):
    id: int
    household_id: int
    recipe_id: int
    rating: int
    note: str | None
    updated_at: datetime
    family_member: RecipePreferenceFamilyMemberRead

    model_config = ConfigDict(from_attributes=True)


class RecipePreferenceSummaryRead(BaseModel):
    household_id: int
    recipe_id: int
    recipe_name: str
    ratings_count: int
    average_rating: float
    ratings: list[RecipePreferenceRead]

    model_config = ConfigDict(from_attributes=True)