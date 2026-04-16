from typing import Literal

from pydantic import BaseModel, ConfigDict

from backend.app.schemas.family_member import FamilyMemberRead


ReactionType = Literal["gostou", "neutro", "nao_gostou"]


class MealFeedbackCreate(BaseModel):
    family_member_id: int
    reaction: ReactionType
    note: str | None = None


class MealFeedbackRead(BaseModel):
    id: int
    meal_plan_item_id: int
    reaction: ReactionType
    note: str | None = None
    family_member: FamilyMemberRead

    model_config = ConfigDict(from_attributes=True)


class RecipeFeedbackSummaryRead(BaseModel):
    recipe_id: int
    recipe_name: str
    total_feedback: int
    liked_count: int
    neutral_count: int
    disliked_count: int
    acceptance_score: float