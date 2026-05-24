import asyncio
import logging
import uuid

import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from ai.anomaly import FEATURE_NAMES, analyze_features, retrain_model, user_feature_vector
from ai.content import ContentModerator
from config import get_settings
from models import FlaggedEvent, Message, Post, User
from tasks.celery_app import celery_app

logger = logging.getLogger(__name__)
settings = get_settings()
moderator = ContentModerator()

engine = create_async_engine(settings.database_url)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def _fetch_all_user_features(db: AsyncSession) -> tuple[np.ndarray, list[uuid.UUID]]:
    result = await db.execute(select(User))
    users = result.scalars().all()
    if not users:
        return np.empty((0, len(FEATURE_NAMES))), []

    rows = [
        user_feature_vector(u.posts_per_hour, u.messages_per_hour, u.report_count) for u in users
    ]
    user_ids = [u.id for u in users]
    return np.array(rows, dtype=float), user_ids


async def _create_anomaly_flag(
    db: AsyncSession,
    user_id: uuid.UUID,
    detail: str,
    *,
    post: Post | None = None,
    message: Message | None = None,
) -> FlaggedEvent:
    if post is not None:
        post.is_flagged = True
    if message is not None:
        message.is_flagged = True

    event = FlaggedEvent(
        user_id=user_id,
        event_type="anomaly",
        detail=detail,
    )
    db.add(event)
    await db.flush()
    return event


async def _create_content_flag(
    db: AsyncSession,
    user_id: uuid.UUID,
    detail: str,
    *,
    post: Post | None = None,
    message: Message | None = None,
) -> FlaggedEvent:
    if post is not None:
        post.is_flagged = True
    if message is not None:
        message.is_flagged = True

    event = FlaggedEvent(
        user_id=user_id,
        event_type="content",
        detail=detail,
        resolved=False,
    )
    db.add(event)
    await db.flush()
    return event


async def _check_user_anomaly(db: AsyncSession, user: User) -> dict:
    features = user_feature_vector(user.posts_per_hour, user.messages_per_hour, user.report_count)
    return analyze_features(features)


async def _retrain_anomaly_model() -> dict:
    async with SessionLocal() as db:
        matrix, user_ids = await _fetch_all_user_features(db)
        model = retrain_model(matrix)
        await db.commit()
        return {
            "trained": model is not None,
            "sample_count": len(user_ids),
            "feature_names": list(FEATURE_NAMES),
        }


async def _process_post_moderation(post_id: str) -> dict:
    post_uuid = uuid.UUID(post_id)
    async with SessionLocal() as db:
        post = await db.get(Post, post_uuid)
        if not post:
            return {"status": "skipped", "reason": "post not found"}

        user = await db.get(User, post.user_id)
        if not user:
            return {"status": "skipped", "reason": "user not found"}

        if post.caption is not None:
            content_result = moderator.moderate(post.caption)
            if not content_result.allowed:
                await _create_content_flag(
                    db,
                    user.id,
                    f"Toxicity detected: {content_result.reason or 'content moderation triggered'}",
                    post=post,
                )

        analysis = await _check_user_anomaly(db, user)
        if not analysis["is_anomaly"]:
            await db.commit()
            return {"status": "ok", "flagged": False, "anomaly_score": analysis["anomaly_score"]}

        await _create_anomaly_flag(
            db,
            user.id,
            f"Post {post_id}: {analysis['reason']}",
            post=post,
        )
        await db.commit()
        return {
            "status": "flagged",
            "flagged": True,
            "anomaly_score": analysis["anomaly_score"],
            "reason": analysis["reason"],
        }


async def _process_message_moderation(message_id: str, user_id: str) -> dict:
    message_uuid = uuid.UUID(message_id)
    user_uuid = uuid.UUID(user_id)
    async with SessionLocal() as db:
        message = await db.get(Message, message_uuid)
        if not message:
            return {"status": "skipped", "reason": "message not found"}

        user = await db.get(User, user_uuid)
        if not user:
            return {"status": "skipped", "reason": "user not found"}

        content_result = moderator.moderate(message.content)
        if not content_result.allowed:
            await _create_content_flag(
                db,
                user.id,
                f"Toxicity detected: {content_result.reason or 'content moderation triggered'}",
                message=message,
            )

        analysis = await _check_user_anomaly(db, user)
        if not analysis["is_anomaly"]:
            await db.commit()
            return {"status": "ok", "flagged": False, "anomaly_score": analysis["anomaly_score"]}

        await _create_anomaly_flag(
            db,
            user.id,
            f"Message {message_id}: {analysis['reason']}",
            message=message,
        )
        await db.commit()
        return {
            "status": "flagged",
            "flagged": True,
            "anomaly_score": analysis["anomaly_score"],
            "reason": analysis["reason"],
        }


@celery_app.task(name="tasks.retrain_anomaly_model")
def retrain_anomaly_model() -> dict:
    """Fetch user behavior stats, retrain IsolationForest, and save model."""
    return asyncio.run(_retrain_anomaly_model())


@celery_app.task(name="tasks.process_post_moderation")
def process_post_moderation(post_id: str) -> dict:
    """Run anomaly check on post author; create FlaggedEvent if anomalous."""
    return asyncio.run(_process_post_moderation(post_id))


@celery_app.task(name="tasks.process_message_moderation")
def process_message_moderation(message_id: str, user_id: str) -> dict:
    """Run anomaly check on message author; create FlaggedEvent if anomalous."""
    return asyncio.run(_process_message_moderation(message_id, user_id))
