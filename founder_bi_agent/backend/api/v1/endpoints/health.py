from fastapi import APIRouter
from founder_bi_agent.backend.models.schemas import HealthResponse
from founder_bi_agent.backend.service import FounderBIService

router = APIRouter()
service = FounderBIService()
history_store = service.history

@router.get("", response_model=HealthResponse)
def health() -> HealthResponse:
    status = history_store.status()
    return HealthResponse(
        status="ok",
        history_backend=getattr(status, "backend", "sqlite")
    )
