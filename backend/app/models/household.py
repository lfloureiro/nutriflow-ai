from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base


class Household(Base):
    __tablename__ = "households"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)

    members = relationship(
        "FamilyMember",
        back_populates="household",
        cascade="all, delete-orphan",
    )

    meal_plan_items = relationship(
        "MealPlanItem",
        back_populates="household",
        cascade="all, delete-orphan",
    )

    recipe_preferences = relationship(
        "RecipePreference",
        back_populates="household",
        cascade="all, delete-orphan",
    )