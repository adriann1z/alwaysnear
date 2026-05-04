"""Add LiveAvatar fields to avatars.

Revision ID: 0005_liveavatar_fields
Revises: 0004_alert_tracking_fields
Create Date: 2026-05-04
"""
from alembic import op
import sqlalchemy as sa


revision = "0005_liveavatar_fields"
down_revision = "0004_alert_tracking_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("avatars") as batch_op:
        batch_op.add_column(sa.Column("liveavatar_avatar_id", sa.String(length=255), nullable=True))
        batch_op.add_column(
            sa.Column(
                "liveavatar_status",
                sa.String(length=32),
                nullable=False,
                server_default="not_configured",
            )
        )
        batch_op.add_column(sa.Column("liveavatar_session_id", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("liveavatar_embed_url", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("liveavatar_last_started_at", sa.DateTime(timezone=True), nullable=True))

    with op.batch_alter_table("avatars") as batch_op:
        batch_op.alter_column("liveavatar_status", server_default=None)


def downgrade() -> None:
    with op.batch_alter_table("avatars") as batch_op:
        batch_op.drop_column("liveavatar_last_started_at")
        batch_op.drop_column("liveavatar_embed_url")
        batch_op.drop_column("liveavatar_session_id")
        batch_op.drop_column("liveavatar_status")
        batch_op.drop_column("liveavatar_avatar_id")
