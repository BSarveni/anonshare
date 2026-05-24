import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from auth import get_current_user
from database import get_db
from models import Group, GroupMember, Message, User
from schemas import GroupCreateRequest, GroupResponse, MessageCreateRequest, MessageResponse
from services.content_moderation import run_content_check
from tasks.ai_tasks import process_message_moderation
from websocket import broadcast_group_message

router = APIRouter()


async def _require_membership(db: AsyncSession, group_id: uuid.UUID, user_id: uuid.UUID) -> Group:
    group = await db.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    member = await db.execute(
        select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == user_id,
        )
    )
    if member.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this group")
    return group


def _message_to_response(message: Message) -> MessageResponse:
    return MessageResponse(
        id=message.id,
        group_id=message.group_id,
        content=message.content,
        is_flagged=message.is_flagged,
        created_at=message.created_at,
        pseudonym=message.user.pseudonym,
    )


@router.get("/", response_model=list[GroupResponse])
async def list_my_groups(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    result = await db.execute(
        select(Group)
        .join(GroupMember, GroupMember.group_id == Group.id)
        .where(GroupMember.user_id == current_user.id)
        .order_by(Group.name)
    )
    return result.scalars().all()


@router.post("/create", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    payload: GroupCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    group = Group(name=payload.name, created_by=current_user.id)
    db.add(group)
    await db.flush()
    db.add(GroupMember(group_id=group.id, user_id=current_user.id))
    await db.refresh(group)
    return group


@router.post("/{group_id}/join", status_code=status.HTTP_204_NO_CONTENT)
async def join_group(
    group_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    group = await db.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

    existing = await db.execute(
        select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == current_user.id,
        )
    )
    if existing.scalar_one_or_none() is None:
        db.add(GroupMember(group_id=group_id, user_id=current_user.id))


@router.get("/{group_id}/messages", response_model=list[MessageResponse])
async def get_messages(
    group_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    await _require_membership(db, group_id, current_user.id)
    result = await db.execute(
        select(Message)
        .where(Message.group_id == group_id)
        .options(selectinload(Message.user))
        .order_by(Message.created_at.desc())
        .limit(50)
    )
    messages = list(reversed(result.scalars().all()))
    return [_message_to_response(m) for m in messages]


@router.post("/{group_id}/message", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    group_id: uuid.UUID,
    payload: MessageCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    await _require_membership(db, group_id, current_user.id)

    moderation = run_content_check(payload.content)
    if not moderation.allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=moderation.reason or "Message rejected by content moderation",
        )

    message = Message(
        group_id=group_id,
        user_id=current_user.id,
        content=payload.content,
        is_flagged=False,
    )
    db.add(message)
    await db.flush()
    process_message_moderation.delay(str(message.id), str(current_user.id))

    await db.refresh(message, attribute_names=["user"])
    result = await db.execute(
        select(Message).where(Message.id == message.id).options(selectinload(Message.user))
    )
    message = result.scalar_one()
    response = _message_to_response(message)

    await broadcast_group_message(
        group_id,
        message.content,
        message.user.pseudonym,
        message.created_at,
    )
    return response
