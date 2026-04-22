"""auto meal plan events

Revision ID: 5f2b6c7d8e9f
Revises: c3d9a1f4b2e7
Create Date: 2026-04-24 12:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "5f2b6c7d8e9f"
down_revision: Union[str, Sequence[str], None] = "c3d9a1f4b2e7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "auto_meal_plan_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("run_id", sa.String(length=36), nullable=False),
        sa.Column("household_id", sa.Integer(), nullable=False),
        sa.Column("event_kind", sa.String(length=20), nullable=False),
        sa.Column("engine_version", sa.String(length=50), nullable=False),
        sa.Column("request_start_date", sa.Date(), nullable=False),
        sa.Column("request_end_date", sa.Date(), nullable=False),
        sa.Column("request_meal_types", sa.JSON(), nullable=False),
        sa.Column("skip_existing", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("plan_date", sa.Date(), nullable=False),
        sa.Column("meal_type", sa.String(length=50), nullable=False),
        sa.Column("suggestion_action", sa.String(length=50), nullable=False),
        sa.Column("execution_status", sa.String(length=50), nullable=True),
        sa.Column("suggested_recipe_id", sa.Integer(), nullable=True),
        sa.Column("final_recipe_id", sa.Integer(), nullable=True),
        sa.Column("meal_plan_item_id", sa.Integer(), nullable=True),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("average_rating", sa.Float(), nullable=True),
        sa.Column("ratings_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reasons", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["final_recipe_id"], ["recipes.id"]),
        sa.ForeignKeyConstraint(["household_id"], ["households.id"]),
        sa.ForeignKeyConstraint(["meal_plan_item_id"], ["meal_plan_items.id"]),
        sa.ForeignKeyConstraint(["suggested_recipe_id"], ["recipes.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_auto_meal_plan_events_id"),
        "auto_meal_plan_events",
        ["id"],
        unique=False,
    )
    op.create_index(
        "ix_auto_meal_plan_events_run_id",
        "auto_meal_plan_events",
        ["run_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_auto_meal_plan_events_run_id", table_name="auto_meal_plan_events")
    op.drop_index(op.f("ix_auto_meal_plan_events_id"), table_name="auto_meal_plan_events")
    op.drop_table("auto_meal_plan_events")