"""Add alert tracking fields.

Revision ID: 0004_alert_tracking_fields
Revises: 0003_comfort_mode_statuses
Create Date: 2026-05-03
"""
from alembic import op
import sqlalchemy as sa


revision = "0004_alert_tracking_fields"
down_revision = "0003_comfort_mode_statuses"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("alerts") as batch_op:
        batch_op.add_column(sa.Column("mode", sa.String(length=80), nullable=True))
        batch_op.add_column(sa.Column("trigger_summary", sa.String(length=255), nullable=True))
        batch_op.add_column(
            sa.Column(
                "parent_notified",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )
        batch_op.add_column(
            sa.Column(
                "parent_viewed",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )

    with op.batch_alter_table("alerts") as batch_op:
        batch_op.alter_column("parent_notified", server_default=None)
        batch_op.alter_column("parent_viewed", server_default=None)


def downgrade() -> None:
    with op.batch_alter_table("alerts") as batch_op:
        batch_op.drop_column("parent_viewed")
        batch_op.drop_column("parent_notified")
        batch_op.drop_column("trigger_summary")
        batch_op.drop_column("mode")
