from datetime import UTC, date, datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class AutoMealPlanEvent(Base):
    __tablename__ = "auto_meal_plan_events"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    run_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    household_id: Mapped[int] = mapped_column(ForeignKey("households.id"), nullable=False)

    event_kind: Mapped[str] = mapped_column(String(20), nullable=False)
    engine_version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="heuristic_v1",
    )

    request_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    request_end_date: Mapped[date] = mapped_column(Date, nullable=False)
    request_meal_types: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    skip_existing: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    plan_date: Mapped[date] = mapped_column(Date, nullable=False)
    meal_type: Mapped[str] = mapped_column(String(50), nullable=False)

    suggestion_action: Mapped[str] = mapped_column(String(50), nullable=False)
    execution_status: Mapped[str | None] = mapped_column(String(50), nullable=True)

    suggested_recipe_id: Mapped[int | None] = mapped_column(
        ForeignKey("recipes.id"),
        nullable=True,
    )
    final_recipe_id: Mapped[int | None] = mapped_column(
        ForeignKey("recipes.id"),
        nullable=True,
    )
    meal_plan_item_id: Mapped[int | None] = mapped_column(
        ForeignKey("meal_plan_items.id"),
        nullable=True,
    )

    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    average_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    ratings_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reasons: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC),
    )