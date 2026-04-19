"""meal plan household scope

Revision ID: 2c91c7d4a8f1
Revises: 18f7a4e2c1b0
Create Date: 2026-04-18 14:10:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text


revision: str = "2c91c7d4a8f1"
down_revision: Union[str, Sequence[str], None] = "18f7a4e2c1b0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    existing_columns = {col["name"] for col in inspector.get_columns("meal_plan_items")}

    if "household_id" not in existing_columns:
        with op.batch_alter_table("meal_plan_items") as batch_op:
            batch_op.add_column(sa.Column("household_id", sa.Integer(), nullable=True))

    meal_plan_count = bind.execute(text("SELECT COUNT(*) FROM meal_plan_items")).scalar() or 0
    household_count = bind.execute(text("SELECT COUNT(*) FROM households")).scalar() or 0

    if meal_plan_count > 0 and household_count == 0:
        raise RuntimeError(
            "Existem registos em meal_plan_items mas não existem agregados em households. "
            "Cria pelo menos um agregado antes de aplicar esta migration."
        )

    if household_count > 0:
        bind.execute(
            text(
                """
                UPDATE meal_plan_items
                SET household_id = (
                    SELECT id
                    FROM households
                    ORDER BY id
                    LIMIT 1
                )
                WHERE household_id IS NULL
                """
            )
        )

    inspector = inspect(bind)
    existing_fks = {
        fk["name"] for fk in inspector.get_foreign_keys("meal_plan_items") if fk.get("name")
    }

    with op.batch_alter_table("meal_plan_items") as batch_op:
        if "fk_meal_plan_items_household_id" not in existing_fks:
            batch_op.create_foreign_key(
                "fk_meal_plan_items_household_id",
                "households",
                ["household_id"],
                ["id"],
            )

        batch_op.alter_column(
            "household_id",
            existing_type=sa.Integer(),
            nullable=False,
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    existing_columns = {col["name"] for col in inspector.get_columns("meal_plan_items")}
    existing_fks = {
        fk["name"] for fk in inspector.get_foreign_keys("meal_plan_items") if fk.get("name")
    }

    with op.batch_alter_table("meal_plan_items") as batch_op:
        if "fk_meal_plan_items_household_id" in existing_fks:
            batch_op.drop_constraint("fk_meal_plan_items_household_id", type_="foreignkey")

        if "household_id" in existing_columns:
            batch_op.drop_column("household_id")
