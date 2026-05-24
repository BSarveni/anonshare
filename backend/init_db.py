"""Run migrations companion: ensure tables exist and optionally seed bootstrap admin."""

import asyncio
import logging
import os

from dotenv import load_dotenv
from sqlalchemy import select

load_dotenv()

logger = logging.getLogger(__name__)


async def seed_admin() -> None:
    admin_password = os.getenv("ADMIN_PASSWORD", "").strip()
    if not admin_password:
        return

    from auth import hash_password
    from database import async_session_factory
    from models import User

    async with async_session_factory() as db:
        result = await db.execute(select(User).where(User.is_admin.is_(True)))
        if result.scalar_one_or_none():
            logger.info("Admin user already exists; skipping seed")
            return

        admin = User(
            pseudonym="AdminBootstrap",
            password_hash=hash_password(admin_password),
            is_admin=True,
        )
        db.add(admin)
        await db.commit()
        logger.info("Bootstrap admin created with pseudonym: AdminBootstrap")


async def main() -> None:
    from database import init_db

    await init_db()
    await seed_admin()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
