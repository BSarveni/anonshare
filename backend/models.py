import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pseudonym: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    posts_per_hour: Mapped[float] = mapped_column(Float, default=0.0, server_default="0")
    messages_per_hour: Mapped[float] = mapped_column(Float, default=0.0, server_default="0")
    report_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    posts: Mapped[list["Post"]] = relationship(back_populates="user")
    groups_created: Mapped[list["Group"]] = relationship(back_populates="creator")
    group_memberships: Mapped[list["GroupMember"]] = relationship(back_populates="user")
    messages: Mapped[list["Message"]] = relationship(back_populates="user")
    flagged_events: Mapped[list["FlaggedEvent"]] = relationship(back_populates="user")


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    image_url: Mapped[str] = mapped_column(String(512))
    caption: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_flagged: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="posts")


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(128), index=True)
    created_by: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    creator: Mapped["User"] = relationship(back_populates="groups_created")
    members: Mapped[list["GroupMember"]] = relationship(back_populates="group", cascade="all, delete-orphan")
    messages: Mapped[list["Message"]] = relationship(back_populates="group", cascade="all, delete-orphan")


class GroupMember(Base):
    __tablename__ = "group_members"

    group_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )

    group: Mapped["Group"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship(back_populates="group_memberships")


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("groups.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    content: Mapped[str] = mapped_column(Text)
    is_flagged: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    group: Mapped["Group"] = relationship(back_populates="messages")
    user: Mapped["User"] = relationship(back_populates="messages")


class FlaggedEvent(Base):
    __tablename__ = "flagged_events"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    event_type: Mapped[str] = mapped_column(String(32))  # "anomaly" | "content"
    detail: Mapped[str] = mapped_column(Text)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="flagged_events")
