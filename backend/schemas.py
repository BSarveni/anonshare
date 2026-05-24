import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RegisterRequest(BaseModel):
    password: str = Field(min_length=8, max_length=128)


class RegisterResponse(BaseModel):
    pseudonym: str
    access_token: str


class LoginRequest(BaseModel):
    pseudonym: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    pseudonym: str
    is_admin: bool
    created_at: datetime


class PostUploadRequest(BaseModel):
    image_url: str = Field(min_length=1, max_length=512)
    caption: str | None = Field(default=None, max_length=5000)


class PostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    image_url: str
    caption: str | None
    is_flagged: bool
    created_at: datetime
    poster_pseudonym: str


class GroupCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=128)


class GroupResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    created_at: datetime


class MessageCreateRequest(BaseModel):
    content: str = Field(min_length=1, max_length=5000)


class MessageResponse(BaseModel):
    id: uuid.UUID
    group_id: uuid.UUID
    content: str
    is_flagged: bool
    created_at: datetime
    pseudonym: str


class FlaggedEventResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    user_pseudonym: str
    event_type: str
    detail: str
    resolved: bool
    created_at: datetime


class AdminStatsResponse(BaseModel):
    total_users: int
    total_posts: int
    total_messages: int
    flags_today: int
