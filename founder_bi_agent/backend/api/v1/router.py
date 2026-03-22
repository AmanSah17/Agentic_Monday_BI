from fastapi import APIRouter
from founder_bi_agent.backend.api.v1.endpoints import chat, analytics, health

router = APIRouter()

# Chat endpoints (prefix handled here or in endpoints)
router.include_router(chat.router, tags=["chat"])
router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
router.include_router(health.router, prefix="/health", tags=["health"])
