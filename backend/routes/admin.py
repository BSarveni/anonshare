import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from auth import admin_required
from database import get_db
from models import FlaggedEvent, Message, Post, User
from schemas import AdminStatsResponse, FlaggedEventResponse

router = APIRouter(dependencies=[Depends(admin_required)])


@router.get("/flags", response_model=list[FlaggedEventResponse])
async def list_flags(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(FlaggedEvent)
        .where(FlaggedEvent.resolved.is_(False))
        .options(selectinload(FlaggedEvent.user))
        .order_by(FlaggedEvent.created_at.desc())
    )
    events = result.scalars().all()
    return [
        FlaggedEventResponse(
            id=e.id,
            user_id=e.user_id,
            user_pseudonym=e.user.pseudonym,
            event_type=e.event_type,
            detail=e.detail,
            resolved=e.resolved,
            created_at=e.created_at,
        )
        for e in events
    ]


@router.post("/ban/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def ban_user(
    user_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.is_banned = True


@router.post("/resolve/{flag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def resolve_flag(
    flag_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    event = await db.get(FlaggedEvent, flag_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flag not found")
    event.resolved = True


@router.get("/stats", response_model=AdminStatsResponse)
async def admin_stats(db: Annotated[AsyncSession, Depends(get_db)]):
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    total_users = await db.scalar(select(func.count()).select_from(User)) or 0
    total_posts = await db.scalar(select(func.count()).select_from(Post)) or 0
    total_messages = await db.scalar(select(func.count()).select_from(Message)) or 0
    flags_today = (
        await db.scalar(
            select(func.count())
            .select_from(FlaggedEvent)
            .where(FlaggedEvent.created_at >= today_start)
        )
        or 0
    )

    return AdminStatsResponse(
        total_users=total_users,
        total_posts=total_posts,
        total_messages=total_messages,
        flags_today=flags_today,
    )
