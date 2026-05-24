import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from auth import get_current_user
from database import get_db
from models import Post, User
from schemas import PostResponse, PostUploadRequest
from services.content_moderation import run_content_check
from tasks.ai_tasks import process_post_moderation

router = APIRouter()


def _post_to_response(post: Post) -> PostResponse:
    return PostResponse(
        id=post.id,
        image_url=post.image_url,
        caption=post.caption,
        is_flagged=post.is_flagged,
        created_at=post.created_at,
        poster_pseudonym=post.user.pseudonym,
    )


@router.post("/upload", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def upload_post(
    payload: PostUploadRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    moderation = run_content_check(payload.caption)
    if not moderation.allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=moderation.reason or "Caption rejected by content moderation",
        )

    post = Post(
        user_id=current_user.id,
        image_url=payload.image_url,
        caption=payload.caption,
        is_flagged=False,
    )
    db.add(post)
    await db.flush()
    process_post_moderation.delay(str(post.id))

    await db.refresh(post, attribute_names=["user"])
    result = await db.execute(
        select(Post).where(Post.id == post.id).options(selectinload(Post.user))
    )
    post = result.scalar_one()
    return _post_to_response(post)


@router.get("/feed", response_model=list[PostResponse])
async def feed(
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    result = await db.execute(
        select(Post)
        .options(selectinload(Post.user))
        .where(Post.is_flagged.is_(False))
        .order_by(Post.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    posts = result.scalars().all()
    return [_post_to_response(p) for p in posts]


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    post = await db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    if post.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to delete this post")
    await db.delete(post)
