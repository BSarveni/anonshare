import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


def _normalize_database_url(url: str) -> str:
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    return url


class Settings:
    database_url: str = _normalize_database_url(
        os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://anonshare:anonshare@localhost:5432/anonshare",
        )
    )
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    secret_key: str = os.getenv("SECRET_KEY", "change-me")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7

    cloudinary_cloud_name: str = os.getenv("CLOUDINARY_CLOUD_NAME", "")
    cloudinary_api_key: str = os.getenv("CLOUDINARY_API_KEY", "")
    cloudinary_api_secret: str = os.getenv("CLOUDINARY_API_SECRET", "")

    @property
    def celery_broker_url(self) -> str:
        return os.getenv("CELERY_BROKER_URL", self.redis_url)

    @property
    def celery_result_backend(self) -> str:
        return os.getenv("CELERY_RESULT_BACKEND", self.redis_url)


@lru_cache
def get_settings() -> Settings:
    return Settings()
