import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from ai.content import ModerationResult, moderate
from models import FlaggedEvent, Message, Post


def run_content_check(text: str | None) -> ModerationResult:
    """Run moderation before saving posts or messages."""
    return moderate(text)


async def flag_content_violation(
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
    )
    db.add(event)
    await db.flush()
    return event
