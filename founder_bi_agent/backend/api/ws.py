"""WebSocket Streaming API for Real-time Graph Execution"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Body, Query
from typing import Dict, Set, Any, Optional
import json
import logging
from datetime import datetime
from pydantic import BaseModel

from founder_bi_agent.backend.core.session_manager import SessionManager
from founder_bi_agent.backend.core.logger import EnhancedTraceLogger


logger = logging.getLogger(__name__)

# Global connection manager for broadcasting
class WebSocketConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.session_trackers: Dict[str, EnhancedTraceLogger] = {}

    async def connect(self, session_id: str, websocket: WebSocket) -> None:
        """Register WebSocket client"""
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = set()
        self.active_connections[session_id].add(websocket)
        
        # Create trace logger for this session
        self.session_trackers[session_id] = EnhancedTraceLogger(
            session_id, ws_broadcast=self.broadcast
        )
        
        logger.info(f"WebSocket connected: {session_id}")

    def disconnect(self, session_id: str, websocket: WebSocket) -> None:
        """Unregister WebSocket client"""
        if session_id in self.active_connections:
            self.active_connections[session_id].discard(websocket)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
                if session_id in self.session_trackers:
                    del self.session_trackers[session_id]

    async def broadcast(self, session_id: str, message: Dict[str, Any]) -> None:
        """Broadcast message to all clients in session"""
        if session_id not in self.active_connections:
            return

        disconnected = set()
        for client in self.active_connections[session_id]:
            try:
                await client.send_json(message)
            except Exception as e:
                logger.error(f"Error sending message: {e}")
                disconnected.add(client)

        # Clean up disconnected clients
        for client in disconnected:
            self.disconnect(session_id, client)

    def get_trace_logger(self, session_id: str) -> EnhancedTraceLogger:
        """Get trace logger for session"""
        if session_id not in self.session_trackers:
            self.session_trackers[session_id] = EnhancedTraceLogger(
                session_id, ws_broadcast=self.broadcast
            )
        return self.session_trackers[session_id]


# Global instance
manager = WebSocketConnectionManager()

# Router
router = APIRouter(prefix="/ws", tags=["websocket"])

# Debug endpoint
@router.get("/health")
async def ws_health() -> Dict[str, str]:
    """Health check for WebSocket module"""
    return {"status": "ok", "ws_module": "loaded"}

@router.websocket("/execute/{session_id}")
async def websocket_endpoint(session_id: str, websocket: WebSocket) -> None:
    """
    WebSocket endpoint for real-time graph execution
    
    Client can send:
    {
        "type": "execute",
        "query": "user question",
        "context": {...}
    }
    
    Server emits:
    {
        "type": "node_start" | "node_end" | "node_error" | "data_flow" | "result",
        "data": {...}
    }
    """
    await manager.connect(session_id, websocket)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            message_type = data.get("type", "")

            if message_type == "execute":
                # Handle graph execution (async operation)
                await handle_graph_execution(session_id, data, manager)

            elif message_type == "ping":
                # Health check
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                })

            elif message_type == "get_trace":
                # Request trace summary
                trace_logger = manager.get_trace_logger(session_id)
                summary = trace_logger.get_trace_summary()
                await websocket.send_json({
                    "type": "trace_summary",
                    "data": summary
                })

            elif message_type == "cancel":
                # Handle cancellation
                await websocket.send_json({
                    "type": "execution_cancelled",
                    "session_id": session_id,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                })

    except WebSocketDisconnect:
        manager.disconnect(session_id, websocket)
        logger.info(f"WebSocket disconnected: {session_id}")

    except Exception as e:
        logger.error(f"WebSocket error: {type(e).__name__}: {e}", exc_info=True)
        manager.disconnect(session_id, websocket)


async def handle_graph_execution(
    session_id: str, 
    data: Dict[str, Any],
    connection_manager: WebSocketConnectionManager
) -> None:
    """
    Handle graph execution request via WebSocket.
    Integrates with the existing LangGraph workflow and broadcasts
    execution events to connected clients in real-time using astream_events.
    """
    from founder_bi_agent.backend.service import FounderBIService
    import asyncio

    query = data.get("query", "")
    context = data.get("context", {})
    history = data.get("conversation_history", [])

    service = FounderBIService()
    trace_logger = connection_manager.get_trace_logger(session_id)

    initial_state = {
        "session_id": session_id,
        "question": query,
        "conversation_history": history,
        "traces": [],
    }

    try:
        # Notify client that execution started
        await connection_manager.broadcast(session_id, {
            "type": "execution_start",
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })

        # Use astream_events (v2) for granular node-level events
        async for event in service.app.astream_events(
            initial_state, 
            version="v2",
            config={"configurable": {"thread_id": session_id}}
        ):
            kind = event["event"]
            
            # Start of a node
            if kind == "on_chain_start" and event["name"] == "LangGraph":
                # Master chain start - can ignore or log
                pass
            
            elif kind == "on_chat_model_stream":
                # Optional: stream LLM tokens if needed
                pass

            elif kind == "on_node_start":
                node_name = event["name"]
                # Skip internal/start nodes if they are just overhead
                if node_name not in ["__start__", "__end__"]:
                    await trace_logger.emit_node_start(
                        node_name, 
                        input_data=event.get("data", {}).get("input")
                    )

            elif kind == "on_node_end":
                node_name = event["name"]
                if node_name not in ["__start__", "__end__"]:
                    await trace_logger.emit_node_end(
                        node_name, 
                        output_data=event.get("data", {}).get("output")
                    )

        # Notify client of completion
        await connection_manager.broadcast(session_id, {
            "type": "execution_complete",
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })

    except Exception as e:
        logger.error(f"Execution error: {type(e).__name__}: {e}", exc_info=True)
        await trace_logger.emit_node_error("system", str(e))
        await connection_manager.broadcast(session_id, {
            "type": "execution_error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })


# REST endpoints for session management
session_router = APIRouter(prefix="/sessions", tags=["sessions"])
session_manager: Optional[SessionManager] = None  # Will be initialized in main


# Request models for type safety
class MessageRequest(BaseModel):
    """Request body for adding a message to session"""
    role: str
    content: str


@session_router.post("/create")
async def create_session(user_id: str = Query("anonymous_user")) -> Dict[str, Any]:
    """Create new session - user_id as query parameter (optional, defaults to anonymous_user)"""
    if not session_manager:
        raise HTTPException(
            status_code=500, 
            detail="Session manager not initialized. Contact administrator."
        )

    try:
        session = session_manager.create_session(user_id)
        return {
            "session_id": session["session_id"],
            "conversation_id": session["conversation_id"],
            "created_at": session["created_at"],
        }
    except Exception as e:
        logger.error(f"Create session error: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")


@session_router.get("/{session_id}/trace")
async def get_session_trace(session_id: str) -> Dict[str, Any]:
    """Get execution trace for session"""
    trace_logger = manager.get_trace_logger(session_id)
    return trace_logger.get_trace_summary()


@session_router.get("/{session_id}/history")
async def get_session_history(session_id: str, limit: int = 50) -> Dict[str, Any]:
    """Get conversation history for session"""
    if not session_manager:
        raise HTTPException(
            status_code=500,
            detail="Session manager not initialized"
        )

    try:
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        return {
            "session_id": session_id,
            "messages": session.get("messages", [])[-limit:],
            "node_traces": session.get("node_traces", [])[-limit:],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get history error: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve history: {str(e)}")


@session_router.post("/{session_id}/message")
async def add_message(
    session_id: str,
    message_data: MessageRequest = Body(...)
) -> Dict[str, str]:
    """Add message to session (role and content in request body)"""
    if not session_manager:
        raise HTTPException(
            status_code=500,
            detail="Session manager not initialized"
        )

    try:
        session_manager.add_message(session_id, message_data.role, message_data.content)
        return {"status": "ok", "message": "Message added successfully"}
    except ValueError as e:
        logger.warning(f"Invalid session {session_id}: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Add message error: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to add message: {str(e)}")
