from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base


class FamilyMember(Base):
    __tablename__ = "family_members"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    household_id: Mapped[int] = mapped_column(ForeignKey("households.id"), nullable=False)

    household = relationship("Household", back_populates="members")
    feedback_entries = relationship(
        "MealFeedback",
        back_populates="family_member",
        cascade="all, delete-orphan",
    )
    recipe_preferences = relationship(
        "RecipePreference",
        back_populates="family_member",
        cascade="all, delete-orphan",
    )