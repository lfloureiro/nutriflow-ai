from datetime import datetime

from pydantic import BaseModel, Field


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
    family_member: dict

    class Config:
        from_attributes = True


class RecipePreferenceSummaryRead(BaseModel):
    household_id: int
    recipe_id: int
    recipe_name: str
    ratings_count: int
    average_rating: float
    ratings: list[RecipePreferenceRead]