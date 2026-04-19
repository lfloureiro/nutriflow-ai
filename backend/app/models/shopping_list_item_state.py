from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base


class ShoppingListItemState(Base):
    __tablename__ = "shopping_list_item_states"
    __table_args__ = (
        UniqueConstraint(
            "household_id",
            "ingredient_id",
            "unit",
            name="uq_shopping_list_item_states_household_ingredient_unit",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    household_id: Mapped[int] = mapped_column(
        ForeignKey("households.id"),
        nullable=False,
    )
    ingredient_id: Mapped[int] = mapped_column(
        ForeignKey("ingredients.id"),
        nullable=False,
    )
    unit: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    in_cart: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC).replace(tzinfo=None),
    )

    household = relationship("Household")
    ingredient = relationship("Ingredient")