from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base


class RecipePreference(Base):
    __tablename__ = "recipe_preferences"
    __table_args__ = (
        UniqueConstraint(
            "household_id",
            "family_member_id",
            "recipe_id",
            name="uq_recipe_preferences_household_member_recipe",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    household_id: Mapped[int] = mapped_column(ForeignKey("households.id"), nullable=False)
    family_member_id: Mapped[int] = mapped_column(ForeignKey("family_members.id"), nullable=False)
    recipe_id: Mapped[int] = mapped_column(ForeignKey("recipes.id"), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    household = relationship("Household")
    family_member = relationship("FamilyMember")
    recipe = relationship("Recipe")