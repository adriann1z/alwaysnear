"""Add comfort mode review statuses.

Revision ID: 0003_comfort_mode_statuses
Revises: 0002_avatar_voice_stage4
Create Date: 2026-05-03
"""
from alembic import op
import sqlalchemy as sa


revision = "0003_comfort_mode_statuses"
down_revision = "0002_avatar_voice_stage4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("comfort_modes") as batch_op:
        batch_op.add_column(
            sa.Column(
                "safety_status",
                sa.String(length=32),
                nullable=False,
                server_default="pending",
            )
        )
        batch_op.add_column(
            sa.Column(
                "parent_approval_status",
                sa.String(length=32),
                nullable=False,
                server_default="pending",
            )
        )

    with op.batch_alter_table("comfort_modes") as batch_op:
        batch_op.alter_column("safety_status", server_default=None)
        batch_op.alter_column("parent_approval_status", server_default=None)


def downgrade() -> None:
    with op.batch_alter_table("comfort_modes") as batch_op:
        batch_op.drop_column("parent_approval_status")
        batch_op.drop_column("safety_status")
