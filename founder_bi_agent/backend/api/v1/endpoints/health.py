from fastapi import APIRouter
from founder_bi_agent.backend.models.schemas import HealthResponse
from founder_bi_agent.backend.history_store import ConversationHistoryStore

router = APIRouter()
history_store = ConversationHistoryStore()

@router.get("", response_model=HealthResponse)
def health() -> HealthResponse:
    status = history_store.status()
    return HealthResponse(
        status="ok",
        history_backend=getattr(status, "backend", "sqlite")
    )
