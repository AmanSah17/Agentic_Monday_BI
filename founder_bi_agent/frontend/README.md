# React Frontend (Integrated with Backend Agent)

This UI is wired to the FastAPI backend (`/query`) and shows:
- chat answers
- generated SQL
- result preview table
- reasoning trace steps

It no longer calls Gemini directly from the browser.

## Run

1. Start backend:
```bash
python -m uvicorn founder_bi_agent.backend.api:app --host 127.0.0.1 --port 8010
```

2. Start frontend:
```bash
cd founder_bi_agent/frontend
npm install
set VITE_BACKEND_URL=http://127.0.0.1:8010
npm run dev
```

3. Open:
`http://127.0.0.1:3000`

Notes:
- Frontend sends a persistent `session_id` (stored in `localStorage`) with each query.
- Backend stores history in Redis when available, otherwise in memory.
- Frontend uses `/api` proxy to backend (`VITE_BACKEND_URL` or default `http://127.0.0.1:8010`).

If chat returns backend error:
1. Verify `http://127.0.0.1:3000/api/health` returns JSON.
2. Verify backend has monday token in `.env` (`MONDAY_COM_API_KEY` or `MONDAY_API_TOKEN`).
3. Open backend logs (uvicorn) and inspect `query.error` lines.
