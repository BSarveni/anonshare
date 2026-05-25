import random
import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from database import get_db
from models import User

settings = get_settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

ACCESS_TOKEN_EXPIRE_HOURS = 24

ADJECTIVES = [
    "Swift",
    "Silent",
    "Bold",
    "Clever",
    "Mystic",
    "Brave",
    "Calm",
    "Daring",
    "Eager",
    "Fierce",
    "Gentle",
    "Hidden",
    "Iron",
    "Jolly",
    "Keen",
    "Lucky",
    "Mighty",
    "Noble",
    "Quick",
    "Royal",
    "Sharp",
    "True",
    "Vivid",
    "Wild",
    "Young",
    "Zen",
    "Amber",
    "Bright",
    "Cosmic",
    "Dusk",
]

ANIMALS = [
    "Otter",
    "Falcon",
    "Wolf",
    "Tiger",
    "Eagle",
    "Fox",
    "Bear",
    "Hawk",
    "Lynx",
    "Panda",
    "Raven",
    "Seal",
    "Stag",
    "Viper",
    "Whale",
    "Badger",
    "Crane",
    "Drake",
    "Finch",
    "Heron",
    "Koala",
    "Moose",
    "Newt",
    "Owl",
    "Puma",
    "Quail",
    "Robin",
    "Shark",
    "Toad",
    "Urchin",
    "Yak",
]


def generate_pseudonym() -> str:
    """Build a pseudonym like SwiftOtter_4821 from adjective + animal + 4-digit number."""
    adjective = random.choice(ADJECTIVES)
    animal = random.choice(ANIMALS)
    number = random.randint(1000, 9999)
    return f"{adjective}{animal}_{number}"


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    payload = {"sub": user_id, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def verify_token(token: str) -> str:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        return str(user_id)
    except JWTError:
        raise credentials_exception from None


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    user_id_str = verify_token(token)
    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    result = await db.execute(select(User).where(User.id == user_uuid))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user.is_banned:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is banned",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def admin_required(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


# Backward-compatible alias for existing routes
get_current_admin = admin_required
