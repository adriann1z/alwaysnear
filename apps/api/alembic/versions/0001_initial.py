"""Initial schema.

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-03
"""
from alembic import op
import sqlalchemy as sa


revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


uuid_type = sa.Uuid(as_uuid=True)


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "parents",
        sa.Column("user_id", uuid_type, nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("phone", sa.String(length=40), nullable=True),
        sa.Column("timezone", sa.String(length=80), nullable=False),
        sa.Column("consent_given", sa.Boolean(), nullable=False),
        sa.Column("consent_given_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("privacy_acknowledged", sa.Boolean(), nullable=False),
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_parents_user_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_parents")),
    )
    op.create_index(op.f("ix_parents_user_id"), "parents", ["user_id"], unique=True)

    op.create_table(
        "audit_logs",
        sa.Column("actor_user_id", uuid_type, nullable=True),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("entity_type", sa.String(length=80), nullable=False),
        sa.Column("entity_id", uuid_type, nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], name=op.f("fk_audit_logs_actor_user_id_users"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_audit_logs")),
    )
    op.create_index(op.f("ix_audit_logs_action"), "audit_logs", ["action"], unique=False)
    op.create_index(op.f("ix_audit_logs_actor_user_id"), "audit_logs", ["actor_user_id"], unique=False)
    op.create_index(op.f("ix_audit_logs_entity_id"), "audit_logs", ["entity_id"], unique=False)

    op.create_table(
        "children",
        sa.Column("parent_id", uuid_type, nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("nickname", sa.String(length=120), nullable=True),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("pronouns", sa.String(length=80), nullable=True),
        sa.Column("comfort_notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["parent_id"], ["parents.id"], name=op.f("fk_children_parent_id_parents"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_children")),
    )
    op.create_index(op.f("ix_children_parent_id"), "children", ["parent_id"], unique=False)

    op.create_table(
        "comfort_modes",
        sa.Column("child_id", uuid_type, nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("routine_prompt", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["child_id"], ["children.id"], name=op.f("fk_comfort_modes_child_id_children"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_comfort_modes")),
    )
    op.create_index(op.f("ix_comfort_modes_child_id"), "comfort_modes", ["child_id"], unique=False)

    op.create_table(
        "helper_profiles",
        sa.Column("parent_id", uuid_type, nullable=False),
        sa.Column("child_id", uuid_type, nullable=False),
        sa.Column("label", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paused_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["child_id"], ["children.id"], name=op.f("fk_helper_profiles_child_id_children"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_id"], ["parents.id"], name=op.f("fk_helper_profiles_parent_id_parents"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_helper_profiles")),
    )
    op.create_index(op.f("ix_helper_profiles_child_id"), "helper_profiles", ["child_id"], unique=False)
    op.create_index(op.f("ix_helper_profiles_parent_id"), "helper_profiles", ["parent_id"], unique=False)

    op.create_table(
        "avatars",
        sa.Column("helper_profile_id", uuid_type, nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=True),
        sa.Column("provider_asset_id", sa.String(length=255), nullable=True),
        sa.Column("asset_url", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["helper_profile_id"], ["helper_profiles.id"], name=op.f("fk_avatars_helper_profile_id_helper_profiles"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_avatars")),
    )
    op.create_index(op.f("ix_avatars_helper_profile_id"), "avatars", ["helper_profile_id"], unique=True)

    op.create_table(
        "conversations",
        sa.Column("child_id", uuid_type, nullable=False),
        sa.Column("helper_profile_id", uuid_type, nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["child_id"], ["children.id"], name=op.f("fk_conversations_child_id_children"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["helper_profile_id"], ["helper_profiles.id"], name=op.f("fk_conversations_helper_profile_id_helper_profiles"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_conversations")),
    )
    op.create_index(op.f("ix_conversations_child_id"), "conversations", ["child_id"], unique=False)
    op.create_index(op.f("ix_conversations_helper_profile_id"), "conversations", ["helper_profile_id"], unique=False)

    op.create_table(
        "voices",
        sa.Column("helper_profile_id", uuid_type, nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=True),
        sa.Column("provider_voice_id", sa.String(length=255), nullable=True),
        sa.Column("sample_url", sa.Text(), nullable=True),
        sa.Column("consent_record_url", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["helper_profile_id"], ["helper_profiles.id"], name=op.f("fk_voices_helper_profile_id_helper_profiles"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_voices")),
    )
    op.create_index(op.f("ix_voices_helper_profile_id"), "voices", ["helper_profile_id"], unique=True)

    op.create_table(
        "messages",
        sa.Column("conversation_id", uuid_type, nullable=False),
        sa.Column("sender_role", sa.String(length=32), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("safety_level", sa.String(length=32), nullable=True),
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], name=op.f("fk_messages_conversation_id_conversations"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_messages")),
    )
    op.create_index(op.f("ix_messages_conversation_id"), "messages", ["conversation_id"], unique=False)

    op.create_table(
        "alerts",
        sa.Column("parent_id", uuid_type, nullable=False),
        sa.Column("child_id", uuid_type, nullable=False),
        sa.Column("conversation_id", uuid_type, nullable=True),
        sa.Column("message_id", uuid_type, nullable=True),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("category", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["child_id"], ["children.id"], name=op.f("fk_alerts_child_id_children"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], name=op.f("fk_alerts_conversation_id_conversations"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"], name=op.f("fk_alerts_message_id_messages"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["parent_id"], ["parents.id"], name=op.f("fk_alerts_parent_id_parents"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_alerts")),
    )
    op.create_index(op.f("ix_alerts_child_id"), "alerts", ["child_id"], unique=False)
    op.create_index(op.f("ix_alerts_conversation_id"), "alerts", ["conversation_id"], unique=False)
    op.create_index(op.f("ix_alerts_message_id"), "alerts", ["message_id"], unique=False)
    op.create_index(op.f("ix_alerts_parent_id"), "alerts", ["parent_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_alerts_parent_id"), table_name="alerts")
    op.drop_index(op.f("ix_alerts_message_id"), table_name="alerts")
    op.drop_index(op.f("ix_alerts_conversation_id"), table_name="alerts")
    op.drop_index(op.f("ix_alerts_child_id"), table_name="alerts")
    op.drop_table("alerts")
    op.drop_index(op.f("ix_messages_conversation_id"), table_name="messages")
    op.drop_table("messages")
    op.drop_index(op.f("ix_voices_helper_profile_id"), table_name="voices")
    op.drop_table("voices")
    op.drop_index(op.f("ix_conversations_helper_profile_id"), table_name="conversations")
    op.drop_index(op.f("ix_conversations_child_id"), table_name="conversations")
    op.drop_table("conversations")
    op.drop_index(op.f("ix_avatars_helper_profile_id"), table_name="avatars")
    op.drop_table("avatars")
    op.drop_index(op.f("ix_helper_profiles_parent_id"), table_name="helper_profiles")
    op.drop_index(op.f("ix_helper_profiles_child_id"), table_name="helper_profiles")
    op.drop_table("helper_profiles")
    op.drop_index(op.f("ix_comfort_modes_child_id"), table_name="comfort_modes")
    op.drop_table("comfort_modes")
    op.drop_index(op.f("ix_children_parent_id"), table_name="children")
    op.drop_table("children")
    op.drop_index(op.f("ix_audit_logs_entity_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_actor_user_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_action"), table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index(op.f("ix_parents_user_id"), table_name="parents")
    op.drop_table("parents")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
