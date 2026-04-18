from datetime import date

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base


class MealPlanItem(Base):
    __tablename__ = "meal_plan_items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    household_id: Mapped[int] = mapped_column(
        ForeignKey("households.id"),
        nullable=False,
    )
    plan_date: Mapped[date] = mapped_column(Date, nullable=False)
    meal_type: Mapped[str] = mapped_column(String(50), nullable=False, default="jantar")
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    recipe_id: Mapped[int] = mapped_column(ForeignKey("recipes.id"), nullable=False)

    household = relationship("Household", back_populates="meal_plan_items")
    recipe = relationship("Recipe")
    feedback_entries = relationship(
        "MealFeedback",
        back_populates="meal_plan_item",
        cascade="all, delete-orphan",
    )