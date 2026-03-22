# AI Agent System - API Reference

## WebSocket API

### Connection

```
WS ws://localhost:8000/ws/execute/{session_id}
```

### Client → Server Messages

#### Execute Query

```json
{
  "type": "execute",
  "query": "What is our revenue trend?",
  "context": {
    "board_id": "12345",
    "date_range": "last_30_days"
  }
}
```

#### Get Trace Summary

```json
{
  "type": "get_trace"
}
```

#### Health Check (Ping)

```json
{
  "type": "ping"
}
```

#### Cancel Execution

```json
{
  "type": "cancel"
}
```

### Server → Client Messages

#### Execution Start

```json
{
  "type": "execution_start",
  "session_id": "session-123",
  "timestamp": "2026-03-22T10:30:00Z"
}
```

#### Node Start Event

```json
{
  "type": "node_start",
  "node_name": "memory_retriever",
  "timestamp": "2026-03-22T10:30:01Z",
  "data": {
    "event_type": "node_start",
    "node_name": "memory_retriever",
    "timestamp": "2026-03-22T10:30:01Z",
    "status": "starting",
    "input_data": {
      "question": "What is revenue?",
      "session_id": "session-123"
    },
    "metadata": {
      "model": "gemini-2.0"
    }
  }
}
```

#### Node End Event

```json
{
  "type": "node_end",
  "node_name": "memory_retriever",
  "execution_time_ms": 245,
  "timestamp": "2026-03-22T10:30:01.245Z",
  "data": {
    "event_type": "node_end",
    "node_name": "memory_retriever",
    "timestamp": "2026-03-22T10:30:01.245Z",
    "status": "completed",
    "output_data": {
      "context_length": 1250,
      "matches_found": 5
    },
    "execution_time_ms": 245
  }
}
```

#### Node Error Event

```json
{
  "type": "node_error",
  "node_name": "sql_execute",
  "error": "Query execution timeout after 30 seconds",
  "timestamp": "2026-03-22T10:30:15Z",
  "data": {
    "event_type": "node_error",
    "node_name": "sql_execute",
    "timestamp": "2026-03-22T10:30:15Z",
    "status": "failed",
    "error_message": "Query execution timeout after 30 seconds"
  }
}
```

#### Data Flow Event

```json
{
  "type": "data_flow",
  "from": "text2sql_planner",
  "to": "sql_execute",
  "timestamp": "2026-03-22T10:30:10Z",
  "description": "Passing SQL query",
  "data_count": 1
}
```

#### Trace Summary Event

```json
{
  "type": "trace_summary",
  "data": {
    "session_id": "session-123",
    "total_events": 32,
    "events": [
      {
        "event_type": "node_start",
        "node_name": "memory_retriever",
        "timestamp": "2026-03-22T10:30:01Z",
        "status": "starting"
      }
      // ... more events
    ],
    "lineage": {
      "transformations": [
        {
          "ts": "2026-03-22T10:30:01.245Z",
          "from": "memory_retriever",
          "to": "intent_router",
          "source_keys": ["question"],
          "target_keys": ["intent", "question"]
        }
      ],
      "node_count": 8
    },
    "timestamp": "2026-03-22T10:30:25Z"
  }
}
```

#### Execution Complete

```json
{
  "type": "execution_complete",
  "session_id": "session-123",
  "timestamp": "2026-03-22T10:30:30Z"
}
```

#### Execution Error

```json
{
  "type": "execution_error",
  "error": "Failed to fetch data from Monday.com",
  "timestamp": "2026-03-22T10:30:20Z"
}
```

#### Pong Response

```json
{
  "type": "pong",
  "timestamp": "2026-03-22T10:30:05Z"
}
```

## REST API

### Sessions

#### Create Session

```http
POST /sessions/create?user_id=user123
```

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "conversation_id": "conv-123",
  "created_at": "2026-03-22T10:30:00Z"
}
```

#### Get Session Trace

```http
GET /sessions/{session_id}/trace
```

**Response:**
```json
{
  "session_id": "session-123",
  "total_events": 32,
  "events": [
    {
      "event_type": "node_start",
      "node_name": "memory_retriever",
      "timestamp": "2026-03-22T10:30:01Z",
      "status": "starting",
      "input_data": {
        "question": "What is our revenue?"
      }
    },
    {
      "event_type": "node_end",
      "node_name": "memory_retriever",
      "timestamp": "2026-03-22T10:30:01.245Z",
      "status": "completed",
      "output_data": {
        "context_length": 1250
      },
      "execution_time_ms": 245
    }
  ],
  "lineage": {
    "transformations": [
      {
        "ts": "2026-03-22T10:30:01.245Z",
        "from": "memory_retriever",
        "to": "intent_router",
        "source_keys": ["question"],
        "target_keys": ["intent", "question"],
        "description": ""
      }
    ],
    "node_count": 5
  },
  "timestamp": "2026-03-22T10:30:30Z"
}
```

#### Get Session History

```http
GET /sessions/{session_id}/history?limit=50
```

**Response:**
```json
{
  "session_id": "session-123",
  "messages": [
    {
      "id": "msg-1",
      "role": "user",
      "content": "What is our revenue?",
      "timestamp": "2026-03-22T10:30:00Z",
      "metadata": {}
    },
    {
      "id": "msg-2",
      "role": "assistant",
      "content": "Based on the data, your revenue is...",
      "timestamp": "2026-03-22T10:30:25Z",
      "metadata": {
        "source_nodes": ["data_summarizer", "insight_writer"]
      }
    }
  ],
  "node_traces": [
    {
      "node_name": "memory_retriever",
      "status": "completed",
      "execution_time_ms": 245,
      "timestamp": "2026-03-22T10:30:01Z"
    }
    // ... more traces
  ]
}
```

#### Add Message to Session

```http
POST /sessions/{session_id}/message?role=user&content=New question
```

**Response:**
```json
{
  "status": "ok"
}
```

## Data Types

### NodeStatus

```
"idle" | "starting" | "running" | "completed" | "failed" | "skipped"
```

### DataType

```
"question" | "context" | "schema" | "data_table" | 
"sql_query" | "result_set" | "insight" | "chart_spec" | "answer"
```

### TransformationType

```
"filter" | "aggregate" | "join" | "select" | "data_flow" | "transform"
```

## Error Responses

### WebSocket Errors

All errors are sent as regular WebSocket messages:

```json
{
  "type": "execution_error",
  "error": "Error message description",
  "timestamp": "2026-03-22T10:30:20Z"
}
```

### REST API Errors

#### 404 Not Found

```json
{
  "detail": "Session not found"
}
```

#### 500 Server Error

```json
{
  "detail": "Session manager not initialized"
}
```

## Rate Limiting

- No rate limiting on WebSocket (per-session)
- REST endpoints: 100 requests per minute per IP
- Session creation: 10 per user per minute

## Authentication (Future)

Currently no authentication. Recommended integration:

```python
# In ws.py
@router.websocket("/execute/{session_id}")
async def websocket_endpoint(session_id: str, websocket: WebSocket, token: str = Depends(oauth2_scheme)):
    # Verify token
    user = verify_token(token)
    # ... rest of logic
```

## Performance Notes

- Average node execution: 100-500ms
- WebSocket broadcast latency: <10ms
- Session trace storage: ~100KB per hour of usage
- Lineage tracking overhead: <5% CPU

## Example Client Implementation

### JavaScript/TypeScript

```typescript
// Connect and execute query
const sessionId = generateUUID();
const ws = new WebSocket(`ws://localhost:8000/ws/execute/${sessionId}`);

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  if (message.type === 'node_start') {
    updateNodeStatus(message.node_name, 'running');
  } else if (message.type === 'node_end') {
    updateNodeStatus(message.node_name, 'completed', message.execution_time_ms);
  } else if (message.type === 'execution_complete') {
    showResults();
  }
};

// Send query
ws.send(JSON.stringify({
  type: 'execute',
  query: 'What is our revenue?'
}));
```

### Python

```python
import asyncio
import websockets
import json

async def connect_and_execute():
    session_id = "test-session"
    uri = f"ws://localhost:8000/ws/execute/{session_id}"
    
    async with websockets.connect(uri) as websocket:
        # Send query
        await websocket.send(json.dumps({
            "type": "execute",
            "query": "What is our revenue?"
        }))
        
        # Listen for events
        while True:
            message = await websocket.recv()
            event = json.loads(message)
            print(f"Event: {event['type']}")
            
            if event['type'] == 'execution_complete':
                break

asyncio.run(connect_and_execute())
```

## Testing with wscat

```bash
# Install wscat
npm install -g wscat

# Connect to WebSocket
wscat -c ws://localhost:8000/ws/execute/test-session-123

# Send first message (paste in terminal):
{"type": "execute", "query": "What is revenue?"}

# You should see node_start events stream in real-time
# { "type": "node_start", "node_name": "memory_retriever", ...}
# { "type": "node_end", "node_name": "memory_retriever", ...}
# etc.

# Send another command
{"type": "get_trace"}
```
