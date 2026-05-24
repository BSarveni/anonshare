import json
import uuid
from datetime import datetime

from fastapi import HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth import verify_token
from database import async_session_factory
from models import GroupMember, Message, User
from services.content_moderation import run_content_check

class ConnectionManager:
    """Tracks active WebSocket connections per group room."""

    def __init__(self) -> None:
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id: str) -> None:
        await websocket.accept()
        self.active_connections.setdefault(room_id, []).append(websocket)

    def disconnect(self, websocket: WebSocket, room_id: str) -> None:
        if room_id not in self.active_connections:
            return
        self.active_connections[room_id] = [
            ws for ws in self.active_connections[room_id] if ws is not websocket
        ]
        if not self.active_connections[room_id]:
            del self.active_connections[room_id]

    async def broadcast(self, message: dict, room_id: str) -> None:
        dead: list[WebSocket] = []
        for ws in self.active_connections.get(room_id, []):
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws, room_id)


manager = ConnectionManager()


def _message_payload(content: str, pseudonym: str, created_at: datetime) -> dict:
    return {
        "type": "message",
        "content": content,
        "pseudonym": pseudonym,
        "timestamp": created_at.isoformat(),
    }


async def _authenticate_member(group_id: uuid.UUID, token: str | None) -> User | None:
    if not token:
        return None
    try:
        user_id_str = verify_token(token)
        user_uuid = uuid.UUID(user_id_str)
    except (HTTPException, ValueError):
        return None

    async with async_session_factory() as db:
        user = await db.get(User, user_uuid)
        if user is None or user.is_banned:
            return None
        member = await db.execute(
            select(GroupMember).where(
                GroupMember.group_id == group_id,
                GroupMember.user_id == user_uuid,
            )
        )
        if member.scalar_one_or_none() is None:
            return None
        return user


async def _persist_message(
    db: AsyncSession,
    *,
    group_id: uuid.UUID,
    user: User,
    content: str,
) -> Message:
    message = Message(
        group_id=group_id,
        user_id=user.id,
        content=content,
        is_flagged=False,
    )
    db.add(message)
    await db.flush()
    await db.commit()
    await db.refresh(message)
    return message


async def handle_group_chat(websocket: WebSocket, group_id: uuid.UUID) -> None:
    token = websocket.query_params.get("token")
    user = await _authenticate_member(group_id, token)
    if user is None:
        await websocket.close(code=1008)
        return

    room_id = str(group_id)
    await manager.connect(websocket, room_id)

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json(
                    {"type": "error", "content": "Invalid JSON payload"}
                )
                continue

            content = (data.get("content") or "").strip()
            if not content:
                await websocket.send_json(
                    {"type": "error", "content": "Message content is required"}
                )
                continue

            moderation = run_content_check(content)
            if not moderation.allowed:
                await websocket.send_json(
                    {
                        "type": "error",
                        "content": moderation.reason
                        or "Message rejected: harmful content detected",
                    }
                )
                continue

            async with async_session_factory() as db:
                message = await _persist_message(
                    db, group_id=group_id, user=user, content=content
                )

            payload = _message_payload(content, user.pseudonym, message.created_at)
            await manager.broadcast(payload, room_id)
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)


async def broadcast_group_message(
    group_id: uuid.UUID,
    content: str,
    pseudonym: str,
    created_at: datetime,
) -> None:
    """Broadcast from HTTP handlers (e.g. POST /groups/{id}/message)."""
    payload = _message_payload(content, pseudonym, created_at)
    await manager.broadcast(payload, str(group_id))
