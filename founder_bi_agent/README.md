# Monday Founder BI Agent (Strict 2-Board Scope)

This implementation is locked to these boards only:
- `Deal funnel Data`
- `Work_Order_Tracker Data`

No other monday boards are included in query analysis.

## What Is Implemented

- Live monday API integration at query time (no preloaded cache).
- Strict board resolution by exact board name (or explicit board ID env vars).
- LangGraph nodal workflow with steps:
  - intent routing
  - clarification check
  - schema discovery (live)
  - data fetch (live)
  - normalization
  - quality profiling
  - SQL planning
  - SQL guardrails
  - SQL execution
  - insight writing
  - visualization planning
- Tool/API traces exposed in state for UI display.
- Streamlit conversational frontend with:
  - answer
  - SQL used
  - result table
  - chart
  - quality caveats
  - tool/API trace timeline

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables (copy from `.env.example`):
```bash
MONDAY_API_TOKEN=...
MONDAY_MODE=graphql
MONDAY_DEALS_BOARD_NAME=Deal funnel Data
MONDAY_WORK_ORDERS_BOARD_NAME=Work_Order_Tracker Data
# optional hard lock by ID
MONDAY_DEALS_BOARD_ID=5027339053
MONDAY_WORK_ORDERS_BOARD_ID=5027339041

# optional Gemini usage
LLM_PROVIDER=gemini
GOOGLE_API_KEY=...
LLM_SQL_MODEL=gemini-2.0-flash

# optional LangSmith
LANGSMITH_API_KEY=...
LANGSMITH_PROJECT=monday-bi-agent
LANGSMITH_TRACING=true
```

## Run One Query (CLI)

```bash
python -m founder_bi_agent.scripts.run_query_once "How is our pipeline by sector this quarter?"
```

## Run Manual Backend Debug Batch (No Frontend)

```bash
python -m founder_bi_agent.scripts.manual_pipeline_debug
```

This executes a set of simple queries, prints compact diagnostics, and writes:
- `manual_debug_detailed_<timestamp>.json`
- `manual_debug_summary_<timestamp>.json`
in `founder_bi_agent/artifacts/`.

## Run Frontend

```bash
streamlit run founder_bi_agent/frontend/app.py
```

## Run React Frontend + FastAPI Backend (Integrated)

Backend:
```bash
python -m uvicorn founder_bi_agent.backend.api:app --host 127.0.0.1 --port 8010
```

Frontend:
```bash
cd founder_bi_agent/frontend
npm install
set VITE_BACKEND_URL=http://127.0.0.1:8010
npm run dev
```

## Session History (Redis)

- Backend stores conversation history per `session_id`.
- If Redis is available (`REDIS_URL`), history is persisted in Redis.
- If Redis is unavailable, backend falls back to in-memory store.
- API endpoints:
  - `POST /query` with `session_id`
  - `GET /history/{session_id}`

## Troubleshooting

If frontend shows:  
`I encountered a backend processing error while running live tools. Please retry.`

Check:
1. Backend is up: `http://127.0.0.1:8010/health`
2. Frontend proxy path works: `http://127.0.0.1:3000/api/health`
3. monday token is set in `.env` (`MONDAY_API_TOKEN` or `MONDAY_COM_API_KEY`)

Check backend logs for exact failure point:
```bash
python -m uvicorn founder_bi_agent.backend.api:app --host 127.0.0.1 --port 8010 --log-level debug
```
The API now logs:
- query start metadata
- query completion timing + row/traces count
- full exception details on failures

## vLLM (Docker, Faster Local Inference)

Start vLLM server:
```bash
docker compose -f docker-compose.vllm.yml up -d
```

Set backend env:
```bash
LLM_PROVIDER=vllm
LLM_BASE_URL=http://127.0.0.1:8001/v1
LLM_API_KEY=EMPTY
LLM_SQL_MODEL=Qwen/Qwen2.5-1.5B-Instruct
```

Then restart backend.

## Key Files

- Graph workflow: `founder_bi_agent/backend/graph/workflow.py`
- Graph nodes: `founder_bi_agent/backend/graph/nodes.py`
- monday strict tools: `founder_bi_agent/backend/tools/monday_bi_tools.py`
- monday live API client: `founder_bi_agent/backend/mcp/monday_live.py`
- query service: `founder_bi_agent/backend/service.py`
- UI: `founder_bi_agent/frontend/app.py`
