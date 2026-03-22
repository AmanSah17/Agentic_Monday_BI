"""Enhanced Trace Logger with Real-time Event Streaming"""
from datetime import datetime
from typing import Any, Optional, Dict
from enum import Enum
import json
from dataclasses import dataclass, asdict


class NodeStatus(str, Enum):
    """Node execution status"""
    IDLE = "idle"
    STARTING = "starting"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class NodeEvent:
    """Represents a node execution event"""
    event_type: str  # "node_start", "node_end", "node_error", "data_flow"
    node_name: str
    timestamp: str
    status: NodeStatus
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_time_ms: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, filtering None values"""
        data = asdict(self)
        return {k: v for k, v in data.items() if v is not None}


class ResultTracker:
    """Tracks data lineage and transformations"""
    def __init__(self):
        self.lineage: Dict[str, Any] = {}
        self.transformations: list = []

    def add_transformation(
        self,
        source_node: str,
        target_node: str,
        source_data: Any,
        target_data: Any,
        transformation_desc: str = ""
    ):
        """Track data transformation between nodes"""
        self.transformations.append({
            "ts": datetime.utcnow().isoformat() + "Z",
            "from": source_node,
            "to": target_node,
            "source_keys": self._extract_keys(source_data),
            "target_keys": self._extract_keys(target_data),
            "description": transformation_desc,
        })

    @staticmethod
    def _extract_keys(data: Any) -> list:
        """Extract top-level keys from dictionary"""
        if isinstance(data, dict):
            return list(data.keys())
        return []

    def get_lineage_graph(self) -> Dict[str, Any]:
        """Get the data flow graph"""
        return {
            "transformations": self.transformations,
            "node_count": len(set(
                t["from"] for t in self.transformations
            ) | set(t["to"] for t in self.transformations)),
        }


class EnhancedTraceLogger:
    """Central logging system for nodes with WebSocket event emission"""

    def __init__(self, session_id: str, ws_broadcast=None):
        self.session_id = session_id
        self.events: list[NodeEvent] = []
        self.result_tracker = ResultTracker()
        self.ws_broadcast = ws_broadcast  # WebSocket broadcaster
        self.active_nodes: Dict[str, float] = {}  # Track start times

    async def emit_node_start(
        self,
        node_name: str,
        input_data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Emit node start event"""
        event = NodeEvent(
            event_type="node_start",
            node_name=node_name,
            timestamp=datetime.utcnow().isoformat() + "Z",
            status=NodeStatus.STARTING,
            input_data=self._sanitize_data(input_data),
            metadata=metadata,
        )
        self.events.append(event)
        self.active_nodes[node_name] = datetime.utcnow().timestamp()

        if self.ws_broadcast:
            await self.ws_broadcast(
                self.session_id,
                {
                    "type": "node_start",
                    "node_name": node_name,
                    "timestamp": event.timestamp,
                    "data": event.to_dict(),
                }
            )

    async def emit_node_end(
        self,
        node_name: str,
        output_data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Emit node completion event"""
        execution_time = None
        if node_name in self.active_nodes:
            execution_time = (
                datetime.utcnow().timestamp() - self.active_nodes[node_name]
            ) * 1000

        event = NodeEvent(
            event_type="node_end",
            node_name=node_name,
            timestamp=datetime.utcnow().isoformat() + "Z",
            status=NodeStatus.COMPLETED,
            output_data=self._sanitize_data(output_data),
            execution_time_ms=execution_time,
            metadata=metadata,
        )
        self.events.append(event)

        if self.ws_broadcast:
            await self.ws_broadcast(
                self.session_id,
                {
                    "type": "node_end",
                    "node_name": node_name,
                    "execution_time_ms": execution_time,
                    "timestamp": event.timestamp,
                    "data": event.to_dict(),
                }
            )

    async def emit_node_error(
        self,
        node_name: str,
        error_message: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Emit node error event"""
        event = NodeEvent(
            event_type="node_error",
            node_name=node_name,
            timestamp=datetime.utcnow().isoformat() + "Z",
            status=NodeStatus.FAILED,
            error_message=error_message,
            metadata=metadata,
        )
        self.events.append(event)

        if self.ws_broadcast:
            await self.ws_broadcast(
                self.session_id,
                {
                    "type": "node_error",
                    "node_name": node_name,
                    "error": error_message,
                    "timestamp": event.timestamp,
                    "data": event.to_dict(),
                }
            )

    async def emit_data_flow(
        self,
        source_node: str,
        target_node: str,
        source_data: Any,
        target_data: Any,
        description: str = ""
    ):
        """Emit data lineage event"""
        self.result_tracker.add_transformation(
            source_node, target_node, source_data, target_data, description
        )

        if self.ws_broadcast:
            await self.ws_broadcast(
                self.session_id,
                {
                    "type": "data_flow",
                    "from": source_node,
                    "to": target_node,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "description": description,
                }
            )

    @staticmethod
    def _sanitize_data(data: Any, max_depth: int = 2, current_depth: int = 0) -> Any:
        """Safely serialize data for logging"""
        if current_depth >= max_depth:
            return f"<{type(data).__name__}>"

        if isinstance(data, dict):
            return {
                k: EnhancedTraceLogger._sanitize_data(v, max_depth, current_depth + 1)
                for k, v in data.items()
            }
        elif isinstance(data, (list, tuple)):
            return f"<{type(data).__name__}[{len(data)}]>"
        elif isinstance(data, (str, int, float, bool, type(None))):
            return data
        else:
            return f"<{type(data).__name__}>"

    def get_trace_summary(self) -> Dict[str, Any]:
        """Get summary of all events"""
        return {
            "session_id": self.session_id,
            "total_events": len(self.events),
            "events": [e.to_dict() for e in self.events],
            "lineage": self.result_tracker.get_lineage_graph(),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
