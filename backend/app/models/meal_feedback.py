from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base


class MealFeedback(Base):
    __tablename__ = "meal_feedback"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    meal_plan_item_id: Mapped[int] = mapped_column(
        ForeignKey("meal_plan_items.id"),
        nullable=False,
    )
    family_member_id: Mapped[int] = mapped_column(
        ForeignKey("family_members.id"),
        nullable=False,
    )

    reaction: Mapped[str] = mapped_column(String(20), nullable=False)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)

    meal_plan_item = relationship("MealPlanItem", back_populates="feedback_entries")
    family_member = relationship("FamilyMember", back_populates="feedback_entries")