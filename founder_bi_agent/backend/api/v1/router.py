from fastapi import APIRouter
from founder_bi_agent.backend.api.v1.endpoints import chat, analytics, health, user

router = APIRouter()

# Authentication and User management
router.include_router(user.router, prefix="/user", tags=["user"])

# Chat endpoints
router.include_router(chat.router, prefix="/chat", tags=["chat"])
router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
router.include_router(health.router, prefix="/health", tags=["health"])
