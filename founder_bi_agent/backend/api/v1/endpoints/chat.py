import uuid
import time
import logging
from fastapi import APIRouter, HTTPException, Depends
from founder_bi_agent.backend.models.schemas import QueryRequest, QueryResponse
from founder_bi_agent.backend.history_store import ConversationHistoryStore
from founder_bi_agent.backend.vector_memory import VectorMemoryStore
from founder_bi_agent.backend.service import FounderBIService
from founder_bi_agent.backend.core.utils import sanitize_for_json
from founder_bi_agent.backend.api.v1.endpoints.user import get_current_user

router = APIRouter()
logger = logging.getLogger("founder_bi_chat")

_service_instance = None
_vector_store_instance = None

def get_service():
    global _service_instance
    if _service_instance is None:
        from founder_bi_agent.backend.service import FounderBIService
        _service_instance = FounderBIService()
    return _service_instance

def get_vector_store():
    global _vector_store_instance
    if _vector_store_instance is None:
        svc = get_service()
        _vector_store_instance = VectorMemoryStore(svc.settings)
    return _vector_store_instance

@router.get("/history/{session_id}")
def get_history(
    session_id: str, 
    current_user: dict = Depends(get_current_user),
    service: FounderBIService = Depends(get_service)
):
    history_store = service.history
    history = history_store.get_history(session_id, user_id=current_user["id"])
    status = history_store.status()
    return {
        "session_id": session_id,
        "history": history,
        "history_length": len(history),
        "history_backend": status.backend,
    }

@router.post("/query", response_model=QueryResponse)
def query(
    payload: QueryRequest, 
    current_user: dict = Depends(get_current_user),
    service: FounderBIService = Depends(get_service),
    vector_store: VectorMemoryStore = Depends(get_vector_store)
) -> QueryResponse:
    started = time.perf_counter()
    session_id = payload.session_id or str(uuid.uuid4())
    user_id = current_user["id"]
    
    history_store = service.history
    cached_history = history_store.get_history(session_id, user_id=user_id)

    incoming = [
        {"role": str(t.get("role", "")), "content": str(t.get("content", ""))}
        for t in payload.conversation_history
    ]
    merged_history = cached_history if cached_history else incoming

    logger.info(
        "query.start user_id=%s session_id=%s question_len=%s",
        user_id,
        session_id,
        len(payload.question)
    )
    try:
        # Pass user_id to service if needed
        result = service.run_query(
            question=payload.question,
            session_id=session_id,
            conversation_history=merged_history,
        )
    except Exception as exc:
        logger.exception("query.error session_id=%s", session_id)
        raise HTTPException(status_code=500, detail=str(exc))

    safe_result = sanitize_for_json(result)
    
    assistant_text = safe_result.get("answer") or safe_result.get("clarification_question") or ""
    updated_history = history_store.append_turns(
        session_id,
        [
            {"role": "user", "content": payload.question},
            {"role": "assistant", "content": assistant_text},
        ],
        user_id=user_id
    )
    
    summary = safe_result.get("last_result_summary", "")
    vector_store.add_interaction(session_id, payload.question, f"{assistant_text}\n\n[Summary]:\n{summary}")
    
    status = history_store.status()
    return QueryResponse(
        session_id=session_id,
        conversation_history_length=len(updated_history),
        history_backend=status.backend,
        **safe_result,
    )
