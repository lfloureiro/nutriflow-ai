from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base


class Recipe(Base):
    __tablename__ = "recipes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    categoria_alimentar: Mapped[str | None] = mapped_column(String(50), nullable=True)
    proteina_principal: Mapped[str | None] = mapped_column(String(50), nullable=True)
    adequado_refeicao: Mapped[str | None] = mapped_column(String(20), nullable=True)
    auto_plan_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    ingredient_links = relationship(
        "RecipeIngredient",
        back_populates="recipe",
        cascade="all, delete-orphan",
    )

    preferences = relationship(
        "RecipePreference",
        back_populates="recipe",
        cascade="all, delete-orphan",
    )