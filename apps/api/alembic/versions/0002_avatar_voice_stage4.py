"""Add Stage 4 avatar and voice fields.

Revision ID: 0002_avatar_voice_stage4
Revises: 0001_initial
Create Date: 2026-05-03
"""
from alembic import op
import sqlalchemy as sa


revision = "0002_avatar_voice_stage4"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


uuid_type = sa.Uuid(as_uuid=True)


def upgrade() -> None:
    with op.batch_alter_table("avatars") as batch_op:
        batch_op.add_column(sa.Column("parent_id", uuid_type, nullable=True))
        batch_op.add_column(sa.Column("original_image_key", sa.Text(), nullable=True))
        batch_op.add_column(
            sa.Column("consent_status", sa.Boolean(), nullable=False, server_default=sa.false())
        )
        batch_op.add_column(sa.Column("consent_timestamp", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(
            sa.Column(
                "approved_for_child_use",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )
        batch_op.add_column(sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(
            sa.Column("signed_urls_revoked_at", sa.DateTime(timezone=True), nullable=True)
        )
        batch_op.alter_column("helper_profile_id", existing_type=uuid_type, nullable=True)
        batch_op.create_foreign_key(
            op.f("fk_avatars_parent_id_parents"),
            "parents",
            ["parent_id"],
            ["id"],
            ondelete="CASCADE",
        )
        batch_op.create_index(op.f("ix_avatars_parent_id"), ["parent_id"], unique=False)

    with op.batch_alter_table("avatars") as batch_op:
        batch_op.alter_column("consent_status", server_default=None)
        batch_op.alter_column("approved_for_child_use", server_default=None)

    with op.batch_alter_table("voices") as batch_op:
        batch_op.add_column(sa.Column("parent_id", uuid_type, nullable=True))
        batch_op.add_column(
            sa.Column("consent_status", sa.Boolean(), nullable=False, server_default=sa.false())
        )
        batch_op.add_column(sa.Column("consent_timestamp", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("consent_recording_key", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("sample_recording_key", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("preview_audio_key", sa.Text(), nullable=True))
        batch_op.add_column(
            sa.Column(
                "approved_for_child_use",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )
        batch_op.add_column(sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.alter_column("helper_profile_id", existing_type=uuid_type, nullable=True)
        batch_op.create_foreign_key(
            op.f("fk_voices_parent_id_parents"),
            "parents",
            ["parent_id"],
            ["id"],
            ondelete="CASCADE",
        )
        batch_op.create_index(op.f("ix_voices_parent_id"), ["parent_id"], unique=False)

    with op.batch_alter_table("voices") as batch_op:
        batch_op.alter_column("consent_status", server_default=None)
        batch_op.alter_column("approved_for_child_use", server_default=None)


def downgrade() -> None:
    with op.batch_alter_table("voices") as batch_op:
        batch_op.drop_index(op.f("ix_voices_parent_id"))
        batch_op.drop_constraint(op.f("fk_voices_parent_id_parents"), type_="foreignkey")
        batch_op.alter_column("helper_profile_id", existing_type=uuid_type, nullable=False)
        batch_op.drop_column("deleted_at")
        batch_op.drop_column("approved_at")
        batch_op.drop_column("approved_for_child_use")
        batch_op.drop_column("preview_audio_key")
        batch_op.drop_column("sample_recording_key")
        batch_op.drop_column("consent_recording_key")
        batch_op.drop_column("consent_timestamp")
        batch_op.drop_column("consent_status")
        batch_op.drop_column("parent_id")

    with op.batch_alter_table("avatars") as batch_op:
        batch_op.drop_index(op.f("ix_avatars_parent_id"))
        batch_op.drop_constraint(op.f("fk_avatars_parent_id_parents"), type_="foreignkey")
        batch_op.alter_column("helper_profile_id", existing_type=uuid_type, nullable=False)
        batch_op.drop_column("signed_urls_revoked_at")
        batch_op.drop_column("deleted_at")
        batch_op.drop_column("approved_at")
        batch_op.drop_column("approved_for_child_use")
        batch_op.drop_column("consent_timestamp")
        batch_op.drop_column("consent_status")
        batch_op.drop_column("original_image_key")
        batch_op.drop_column("parent_id")
