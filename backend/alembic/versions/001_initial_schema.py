"""Initial schema

Revision ID: 001_initial
Revises:
Create Date: 2026-05-24

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("pseudonym", sa.String(length=64), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_admin", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("is_banned", sa.Boolean(), server_default="false", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("posts_per_hour", sa.Float(), server_default="0", nullable=False),
        sa.Column("messages_per_hour", sa.Float(), server_default="0", nullable=False),
        sa.Column("report_count", sa.Integer(), server_default="0", nullable=False),
    )
    op.create_index("ix_users_pseudonym", "users", ["pseudonym"], unique=True)

    op.create_table(
        "groups",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_groups_name", "groups", ["name"])
    op.create_index("ix_groups_created_by", "groups", ["created_by"])

    op.create_table(
        "posts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("image_url", sa.String(length=512), nullable=False),
        sa.Column("caption", sa.Text(), nullable=True),
        sa.Column("is_flagged", sa.Boolean(), server_default="false", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_posts_user_id", "posts", ["user_id"])

    op.create_table(
        "group_members",
        sa.Column("group_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("group_id", "user_id"),
    )

    op.create_table(
        "messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("group_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("is_flagged", sa.Boolean(), server_default="false", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_messages_group_id", "messages", ["group_id"])
    op.create_index("ix_messages_user_id", "messages", ["user_id"])

    op.create_table(
        "flagged_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(length=32), nullable=False),
        sa.Column("detail", sa.Text(), nullable=False),
        sa.Column("resolved", sa.Boolean(), server_default="false", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_flagged_events_user_id", "flagged_events", ["user_id"])


def downgrade() -> None:
    op.drop_table("flagged_events")
    op.drop_table("messages")
    op.drop_table("group_members")
    op.drop_table("posts")
    op.drop_table("groups")
    op.drop_table("users")
