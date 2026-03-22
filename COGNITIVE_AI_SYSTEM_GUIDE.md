# 15-Step Cognitive AI Agent System Implementation

## Overview

This document describes the complete architecture and implementation of a real-time, observable AI reasoning system integrated into your Monday.com BI Agent. The system provides:

- **Real-time Node Execution Visualization** - Watch reasoning unfold in real-time via WebSocket
- **Complete Data Lineage Tracking** - See exactly how data transforms through 16 nodes
- **Session Management** - Persistent storage with Redis caching and PostgreSQL
- **Interactive Node Graph** - React Flow visualization with animation
- **Trace Logging** - Comprehensive execution traces with timing and errors

## Architecture

### Backend Stack

```
FastAPI ──┬─→ WebSocket Server (Real-time Events)
          ├─→ LangGraph (16-node DAG)
          ├─→ ChromaDB (Vector Memory)
          ├─→ DuckDB (Analytics)
          ├─→ Redis (Session Cache)
          └─→ PostgreSQL (History)
```

### Frontend Stack

```
React ──┬─→ WebSocket Client (Event Listener)
        ├─→ React Flow (Node Graph UI)
        ├─→ D3.js (Data Lineage Visualization)
        ├─→ Framer Motion (Animations)
        └─→ Tailwind CSS (Styling)
```

## Core Components

### 1. Backend Infrastructure

#### `backend/core/logger.py` - Enhanced Trace Logger
- Tracks node execution events (start, end, error)
- Emits events via WebSocket in real-time
- Sanitizes data for safe logging
- Provides comprehensive trace summaries

**Key Classes:**
- `EnhancedTraceLogger` - Main logging system
- `NodeEvent` - Represents a single node execution event
- `ResultTracker` - Tracks data transformations

**Usage:**
```python
logger = EnhancedTraceLogger(session_id, ws_broadcast=broadcast_fn)
await logger.emit_node_start("memory_retriever", input_data={...})
# ... node execution ...
await logger.emit_node_end("memory_retriever", output_data={...})
```

#### `backend/core/session_manager.py` - Session Management
- Creates and manages user sessions
- Maintains conversation history
- Tracks node execution traces
- Redis (fast) + PostgreSQL (persistent) dual-layer storage

**Key Classes:**
- `SessionManager` - Session lifecycle management

**Usage:**
```python
manager = SessionManager(redis_client, db_connection)
session = manager.create_session(user_id="user123")
manager.add_message(session_id, role="user", content="Q: ...")
```

#### `backend/core/data_lineage.py` - Data Lineage Tracking
- Tracks individual data pieces through the graph
- Records transformations between nodes
- Supports data type categorization (QUESTION, SCHEMA, SQL_QUERY, etc.)
- Enables tracing specific data paths

**Key Classes:**
- `DataLineageTracker` - Main lineage tracking
- `DataNode` - Represents data piece
- `DataTransformation` - Represents transformation

**Usage:**
```python
lineage = DataLineageTracker(session_id)
data_id = lineage.track_data_input("node1", DataType.QUESTION, {...})
lineage.track_transformation("node1", "node2", [data_id], [out_id])
graph = lineage.get_data_lineage_graph()
```

#### `backend/api/ws.py` - WebSocket Streaming API
- Maintains WebSocket connections per session
- Routes incoming messages to handlers
- Broadcasts execution events to connected clients
- Provides REST endpoints for trace/history access

**Endpoints:**
- `WS /ws/execute/{session_id}` - Real-time execution streaming
- `POST /sessions/create` - Create new session
- `GET /sessions/{session_id}/trace` - Get execution trace
- `GET /sessions/{session_id}/history` - Get conversation history
- `POST /sessions/{session_id}/message` - Add message

**Message Types:**
```json
// Client → Server
{"type": "execute", "query": "...", "context": {...}}
{"type": "ping"}
{"type": "get_trace"}
{"type": "cancel"}

// Server → Client
{"type": "node_start", "node_name": "...", "data": {...}}
{"type": "node_end", "node_name": "...", "execution_time_ms": 123}
{"type": "node_error", "node_name": "...", "error": "..."}
{"type": "data_flow", "from": "node1", "to": "node2", "data_count": 5}
{"type": "execution_complete"}
```

#### `backend/core/graph_streaming.py` - Streaming Integration
- Bridges async WebSocket with sync LangGraph
- `StreamingGraphWrapper` - Instrument graph execution
- `NodeTrackingDecorator` - Add tracing to individual nodes
- Helper functions for creating traced nodes

### 2. Frontend Components

#### `frontend/src/hooks/useWebSocket.ts` - WebSocket Hook
- Manages WebSocket connection lifecycle
- Dispatches events to specialized handlers
- Provides convenience methods for common operations

**API:**
```typescript
const {
  connected,
  error,
  connect,
  disconnect,
  executeQuery,
  getTrace,
  cancel
} = useWebSocket({
  sessionId,
  onNodeStart: (event) => {},
  onNodeEnd: (event) => {},
  onNodeError: (event) => {},
  onDataFlow: (event) => {},
  onError: (error) => {}
});
```

#### `frontend/src/components/NodeGraphVisualization.tsx`
- Interactive node graph display
- Real-time status updates with animations
- Color-coded execution states (idle, running, completed, failed, skipped)
- Click nodes for details
- Statistics dashboard

**Props:**
```typescript
interface NodeGraphProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
  onNodeClick?: (nodeId: string) => void;
  onReset?: () => void;
  isExecuting?: boolean;
}
```

#### `frontend/src/components/DataLineageVisualization.tsx`
- Data flow visualization
- Tracks data pieces and transformations
- Data type color coding
- Transformation timeline
- Path highlighting on selection

**Props:**
```typescript
interface DataLineageProps {
  nodes: DataFlowNode[];
  edges: DataFlowEdge[];
  onNodeClick?: (nodeId: string) => void;
  title?: string;
}
```

#### `frontend/src/components/SessionHistoryViewer.tsx`
- Expandable conversation history
- Node execution traces with details
- Error messages and data input/output
- Exec timing information
- Export/clear functions

**Props:**
```typescript
interface SessionHistoryProps {
  messages: Message[];
  traces: NodeTrace[];
  sessionId: string;
  onExport?: () => void;
  onClear?: () => void;
}
```

## Integration Steps

### Step 1: Update FastAPI Main

```python
# founder_bi_agent/backend/main.py

from founder_bi_agent.backend.api.ws import router as ws_router, manager
from founder_bi_agent.backend.core.session_manager import SessionManager
import redis

# Initialize dependencies
redis_client = redis.Redis(host='localhost', port=6379, db=0)
# db_connection setup...

# Create session manager
session_manager = SessionManager(redis_client, db_connection)

# Attach to WebSocket module
import founder_bi_agent.backend.api.ws as ws_module
ws_module.session_manager = session_manager

# Include WebSocket routes
app.include_router(ws_router)
```

### Step 2: Instrument Existing Nodes

Replace your node functions with traced versions:

```python
# founder_bi_agent/backend/graph/nodes.py

from founder_bi_agent.backend.core.graph_streaming import NodeTrackingDecorator
from founder_bi_agent.backend.core.logger import EnhancedTraceLogger
from founder_bi_agent.backend.core.data_lineage import DataLineageTracker

class FounderBINodes:
    def __init__(self, settings, trace_logger=None, lineage_tracker=None):
        # ... existing init ...
        self.trace_logger = trace_logger
        self.lineage_tracker = lineage_tracker
    
    async def memory_retriever(self, state):
        if self.trace_logger:
            await self.trace_logger.emit_node_start("memory_retriever")
        
        # ... existing logic ...
        
        if self.trace_logger:
            await self.trace_logger.emit_node_end("memory_retriever", output_data={...})
        
        return updated_state
```

### Step 3: Create a Streaming Wrapper

```python
# In your route handler or graph execution:

from founder_bi_agent.backend.core.graph_streaming import StreamingGraphWrapper

# When handling WebSocket execution:
trace_logger = manager.get_trace_logger(session_id)
lineage_tracker = DataLineageTracker(session_id)

wrapper = StreamingGraphWrapper(
    graph_instance,
    trace_logger,
    lineage_tracker
)

result = await wrapper.invoke(initial_state)
```

### Step 4: Connect Frontend

```typescript
// frontend/src/App.tsx or similar

import { useWebSocket } from './hooks/useWebSocket';
import { NodeGraphVisualization } from './components/NodeGraphVisualization';
import DataLineageVisualization from './components/DataLineageVisualization';
import SessionHistoryViewer from './components/SessionHistoryViewer';

export function GraphDashboard() {
  const [sessionId] = useState(() => generateUUID());
  const [graphNodes, setGraphNodes] = useState<GraphNode[]>([]);
  const [traces, setTraces] = useState<NodeTrace[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);

  const { connected, executeQuery } = useWebSocket({
    sessionId,
    onNodeStart: (event) => {
      setGraphNodes(prev => [
        ...prev,
        {
          id: event.node_name,
          label: event.node_name,
          status: 'running'
        }
      ]);
    },
    onNodeEnd: (event) => {
      setGraphNodes(prev => 
        prev.map(n => 
          n.id === event.node_name
            ? { ...n, status: 'completed', executionTime: event.execution_time_ms }
            : n
        )
      );
    }
  });

  return (
    <div className="grid grid-cols-3 gap-4">
      <div className="col-span-2">
        <NodeGraphVisualization nodes={graphNodes} edges={[]} />
      </div>
      <div>
        <DataLineageVisualization nodes={[]} edges={[]} />
      </div>
      <div className="col-span-3">
        <SessionHistoryViewer 
          messages={messages}
          traces={traces}
          sessionId={sessionId}
        />
      </div>
    </div>
  );
}
```

## 16-Node Pipeline

Your existing graph already implements a sophisticated 16-node pipeline:

1. **Memory Retriever** - Fetch relevant context from history
2. **Intent Router** - Classify user intent
3. **Clarifier** - Request clarification if needed
4. **Executive Planner** - Plan data analysis approach
5. **Web Researcher** (conditional) - Research web if needed
6. **Schema Discovery** - Fetch data schema from Monday.com
7. **Data Fetch Live** - Retrieve live data
8. **Normalize Data** - Clean and normalize data
9. **Quality Profiler** - Profile data quality
10. **Text2SQL Planner** - Generate SQL queries
11. **SQL Guardrail** - Validate SQL safety
12. **SQL Execute** - Execute validated query
13. **Data Summarizer** - Summarize results
14. **Insight Writer** - Generate insights
15. **Viz Builder** - Build visualizations
16. **Reflection Judge** - Validate and reflect on output

## Real-time Events Flow

```
User sends query
     ↓
WebSocket receives {type: "execute", query: "..."}
     ↓
handle_graph_execution() called
     ↓
trace_logger.emit_node_start("memory_retriever") → broadcast to clients
     ↓
Worker process runs: memory_retriever(state)
     ↓
trace_logger.emit_node_end("memory_retriever") → broadcast to clients
     ↓
Browser updates: NodeGraph state="completed", executionTime=45ms
     ↓
... repeat for each node ...
     ↓
trace_logger.emit_execution_complete() → broadcast to clients
     ↓
Browser shows complete execution graph with timing
```

## Data Lineage Example

```
Question
  ↓ [track_data_input]
Intent Router → Context
  ↓ [track_transformation: classify]
Schema Discovery → Board Map
  ↓ [track_transformation: discover]
Data Fetch Live → Raw Tables
  ↓ [track_transformation: fetch]
Normalize Data → Clean Tables
  ↓ [track_transformation: normalize]
Text2SQL Planner → SQL Query
  ↓ [track_transformation: generate_sql]
SQL Execute → Result Set
  ↓ [track_transformation: execute_sql]
Data Summarizer → Summary
  ↓ [track_transformation: summarize]
Insight Writer → Answer
  ↓ [track_data_output]
```

## Performance Considerations

- **WebSocket**: Broadcasts only to connected clients for the session
- **Redis**: 24-hour TTL for session data with automatic cleanup
- **Trace Events**: Async emission doesn't block node execution
- **Large Data**: Sanitized in logs (depth limit, key limit)
- **Database**: Async operations for history persistence

## Testing

```bash
# Test WebSocket connection
wscat -c ws://localhost:8000/ws/execute/test-session-id

# Send execution message
{"type": "execute", "query": "What is our revenue?"}

# Expected stream of events
{"type": "node_start", "node_name": "memory_retriever", ...}
{"type": "node_end", "node_name": "memory_retriever", ...}
# ... more nodes ...
{"type": "execution_complete"}
```

## Files Created/Modified

### New Files
- `backend/core/logger.py` - Trace logger
- `backend/core/session_manager.py` - Session management
- `backend/core/data_lineage.py` - Data lineage tracking
- `backend/core/graph_streaming.py` - Streaming integration
- `backend/api/ws.py` - WebSocket endpoint
- `frontend/src/hooks/useWebSocket.ts` - WebSocket hook
- `frontend/src/components/NodeGraphVisualization.tsx` - Node graph UI
- `frontend/src/components/DataLineageVisualization.tsx` - Data lineage UI
- `frontend/src/components/SessionHistoryViewer.tsx` - History viewer

### Modified Files
- `backend/main.py` - Add WebSocket routes (requires integration step 1)
- `backend/graph/nodes.py` - Add tracing (requires integration step 2)

## Next Steps

1. **Install Dependencies** (if needed):
   ```bash
   pip install redis websockets
   npm install
   ```

2. **Configure Redis**:
   - Install Redis locally or use Docker
   - Update connection string in `session_manager.py`

3. **Test WebSocket**:
   - Start backend: `uvicorn founder_bi_agent.backend.main:app --reload`
   - Open frontend in browser
   - Check browser console for WebSocket connection

4. **Add Tracing to Nodes**:
   - Gradually instrument nodes with `emit_node_start/end`
   - Test with single node first

5. **Deploy**:
   - Server: `gunicorn` with `uvicorn.workers.UvicornWorker`
   - Frontend: build and serve static assets
   - Redis: Managed service (AWS ElastiCache, Azure Cache, etc.)
   - Database: Managed service (AWS RDS, Azure DB, etc.)

## Troubleshooting

- **WebSocket connection fails**: Check CORS settings and websocket route prefix
- **No events received**: Verify trace_logger is properly initialized
- **Memory leaks**: Ensure sessions are properly closed with `session_manager.close_session()`
- **Performance issues**: Check Redis/database latency, add indexes on session_id
