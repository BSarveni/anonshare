import asyncio
import logging
import os
import uuid
from contextlib import asynccontextmanager

import cloudinary
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from database import engine, init_db
import models  # noqa: F401 — register ORM tables
from routes import api_router
from websocket import handle_group_chat

settings = get_settings()
logger = logging.getLogger(__name__)


def configure_cloudinary() -> None:
    if settings.cloudinary_cloud_name:
        cloudinary.config(
            cloud_name=settings.cloudinary_cloud_name,
            api_key=settings.cloudinary_api_key,
            api_secret=settings.cloudinary_api_secret,
        )


async def init_database(max_retries: int = 15, delay_seconds: float = 2.0) -> None:
    """Wait for PostgreSQL (e.g. after `docker compose up db redis -d`)."""
    last_error: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            await init_db()
            logger.info("Database connected and tables ready")
            return
        except (OSError, ConnectionRefusedError, Exception) as exc:
            last_error = exc
            if attempt < max_retries:
                logger.warning(
                    "Database not ready (attempt %s/%s): %s — retrying in %ss",
                    attempt,
                    max_retries,
                    exc,
                    delay_seconds,
                )
                await asyncio.sleep(delay_seconds)
    raise RuntimeError(
        "Could not connect to PostgreSQL. Start it first:\n"
        "  cd anonshare && docker compose up db redis -d\n"
        f"Last error: {last_error}"
    ) from last_error


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_cloudinary()
    await init_database()
    yield
    await engine.dispose()


app = FastAPI(title="AnonShare API", version="1.0.0", lifespan=lifespan)

origins = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix="/api")


@app.websocket("/ws/{group_id}")
async def group_chat_websocket(websocket: WebSocket, group_id: uuid.UUID):
    await handle_group_chat(websocket, group_id)


@app.get("/health")
async def health():
    return {"status": "ok"}
