"""create shopping list item states

Revision ID: 7b4d3e2f1a9c
Revises: 2c91c7d4a8f1
Create Date: 2026-04-19 12:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7b4d3e2f1a9c"
down_revision: Union[str, Sequence[str], None] = "2c91c7d4a8f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "shopping_list_item_states",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("household_id", sa.Integer(), nullable=False),
        sa.Column("ingredient_id", sa.Integer(), nullable=False),
        sa.Column("unit", sa.String(length=50), nullable=False, server_default=""),
        sa.Column("in_cart", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["household_id"], ["households.id"]),
        sa.ForeignKeyConstraint(["ingredient_id"], ["ingredients.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "household_id",
            "ingredient_id",
            "unit",
            name="uq_shopping_list_item_states_household_ingredient_unit",
        ),
    )
    op.create_index(
        op.f("ix_shopping_list_item_states_id"),
        "shopping_list_item_states",
        ["id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_shopping_list_item_states_id"),
        table_name="shopping_list_item_states",
    )
    op.drop_table("shopping_list_item_states")