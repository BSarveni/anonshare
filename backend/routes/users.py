from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth import create_access_token, generate_pseudonym, get_current_user, hash_password, verify_password
from database import get_db
from models import User
from schemas import LoginRequest, MeResponse, RegisterRequest, RegisterResponse, TokenResponse

router = APIRouter()


async def _unique_pseudonym(db: AsyncSession, max_attempts: int = 20) -> str:
    for _ in range(max_attempts):
        pseudonym = generate_pseudonym()
        existing = await db.execute(select(User).where(User.pseudonym == pseudonym))
        if existing.scalar_one_or_none() is None:
            return pseudonym
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Could not generate a unique pseudonym",
    )


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    pseudonym = await _unique_pseudonym(db)
    user = User(
        pseudonym=pseudonym,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    token = create_access_token(str(user.id))
    return RegisterResponse(pseudonym=user.pseudonym, access_token=token)


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(User).where(User.pseudonym == payload.pseudonym))
    user = result.scalar_one_or_none()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect pseudonym or password",
        )
    if user.is_banned:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is banned",
        )
    return TokenResponse(access_token=create_access_token(str(user.id)))


@router.get("/me", response_model=MeResponse)
async def me(current_user: Annotated[User, Depends(get_current_user)]):
    return MeResponse(
        id=current_user.id,
        pseudonym=current_user.pseudonym,
        is_admin=current_user.is_admin,
        created_at=current_user.created_at,
    )
