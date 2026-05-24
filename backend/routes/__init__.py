from fastapi import APIRouter

from routes import admin, groups, posts, users

api_router = APIRouter()
api_router.include_router(users.router, prefix="/auth", tags=["auth"])
api_router.include_router(posts.router, prefix="/posts", tags=["posts"])
api_router.include_router(groups.router, prefix="/groups", tags=["groups"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
