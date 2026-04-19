"""recipe metadata for auto planning

Revision ID: c3d9a1f4b2e7
Revises: 7b4d3e2f1a9c
Create Date: 2026-04-19 18:30:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = "c3d9a1f4b2e7"
down_revision: Union[str, Sequence[str], None] = "7b4d3e2f1a9c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_columns = {col["name"] for col in inspector.get_columns("recipes")}

    with op.batch_alter_table("recipes") as batch_op:
        if "categoria_alimentar" not in existing_columns:
            batch_op.add_column(sa.Column("categoria_alimentar", sa.String(length=50), nullable=True))

        if "proteina_principal" not in existing_columns:
            batch_op.add_column(sa.Column("proteina_principal", sa.String(length=50), nullable=True))

        if "adequado_refeicao" not in existing_columns:
            batch_op.add_column(sa.Column("adequado_refeicao", sa.String(length=20), nullable=True))

        if "auto_plan_enabled" not in existing_columns:
            batch_op.add_column(
                sa.Column(
                    "auto_plan_enabled",
                    sa.Boolean(),
                    nullable=False,
                    server_default=sa.true(),
                )
            )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_columns = {col["name"] for col in inspector.get_columns("recipes")}

    with op.batch_alter_table("recipes") as batch_op:
        if "auto_plan_enabled" in existing_columns:
            batch_op.drop_column("auto_plan_enabled")

        if "adequado_refeicao" in existing_columns:
            batch_op.drop_column("adequado_refeicao")

        if "proteina_principal" in existing_columns:
            batch_op.drop_column("proteina_principal")

        if "categoria_alimentar" in existing_columns:
            batch_op.drop_column("categoria_alimentar")