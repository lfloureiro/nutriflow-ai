"""recipe preferences

Revision ID: 18f7a4e2c1b0
Revises: 00e323d68e36
Create Date: 2026-04-18 12:30:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "18f7a4e2c1b0"
down_revision: Union[str, Sequence[str], None] = "00e323d68e36"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "recipe_preferences",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("household_id", sa.Integer(), nullable=False),
        sa.Column("family_member_id", sa.Integer(), nullable=False),
        sa.Column("recipe_id", sa.Integer(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["family_member_id"], ["family_members.id"]),
        sa.ForeignKeyConstraint(["household_id"], ["households.id"]),
        sa.ForeignKeyConstraint(["recipe_id"], ["recipes.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "household_id",
            "family_member_id",
            "recipe_id",
            name="uq_recipe_preferences_household_member_recipe",
        ),
    )
    op.create_index(
        op.f("ix_recipe_preferences_id"),
        "recipe_preferences",
        ["id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_recipe_preferences_id"), table_name="recipe_preferences")
    op.drop_table("recipe_preferences")