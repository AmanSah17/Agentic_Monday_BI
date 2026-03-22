╔════════════════════════════════════════════════════════════════════════════════╗
║                  🚀 AI AGENT SYSTEM - LIVE & RUNNING 🚀                         ║
╚════════════════════════════════════════════════════════════════════════════════╝

┌─ SERVICES STATUS ─────────────────────────────────────────────────────────────┐
│                                                                                 │
│  ✅ BACKEND (FastAPI + LangGraph)                                             │
│     URL: http://localhost:8000                                                 │
│     WebSocket: ws://localhost:8000/ws/execute/{session_id}                    │
│     PID: 27028                                                                 │
│     Status: Running with auto-reload enabled                                  │
│                                                                                 │
│  ✅ FRONTEND (React + Vite)                                                    │
│     URL: http://localhost:3001                                                │
│     Status: Running with hot reload enabled                                   │
│                                                                                 │
│  ✅ WEBSOCKET CONNECTION                                                       │
│     Status: Working ✨                                                         │
│     Test: PASSED (pong received)                                              │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─ AVAILABLE ENDPOINTS ─────────────────────────────────────────────────────────┐
│                                                                                 │
│  REST Endpoints:                                                              │
│  • GET  /ws/health              - WebSocket module health check               │
│  • POST /sessions/create        - Create new session                          │
│  • GET  /sessions/{id}/trace    - Get execution trace                         │
│  • GET  /sessions/{id}/history  - Get conversation history                    │
│  • POST /sessions/{id}/message  - Add message to session                      │
│                                                                                 │
│  WebSocket Endpoints:                                                         │
│  • WS /ws/execute/{session_id}  - Execute query with real-time streaming      │
│                                                                                 │
│  Message Types:                                                               │
│  • {"type": "ping"}                    - Health check                          │
│  • {"type": "execute", "query": "..."}  - Run query                           │
│  • {"type": "get_trace"}               - Get traces                           │
│  • {"type": "cancel"}                  - Cancel execution                     │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─ QUICK TESTS ─────────────────────────────────────────────────────────────────┐
│                                                                                 │
│  ✅ WebSocket Connection: WORKING                                             │
│     python test_ws_temp.py                                                    │
│                                                                                 │
│  Test the API:                                                                │
│     python debug_endpoints.py                                                 │
│                                                                                 │
│  Open in Browser:                                                             │
│     → http://localhost:3001/                                                  │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─ NEXT STEPS ──────────────────────────────────────────────────────────────────┐
│                                                                                 │
│  1. Open Browser: http://localhost:3001                                       │
│                                                                                 │
│  2. Open Browser DevTools (F12) to see:                                       │
│     • WebSocket connection in Network tab                                     │
│     • Console messages and any errors                                         │
│                                                                                 │
│  3. Run a test query to see:                                                  │
│     • Node graph visualization                                                │
│     • Data lineage tracking                                                   │
│     • Execution timing                                                        │
│     • Session history                                                         │
│                                                                                 │
│  4. Monitor backend logs:                                                     │
│     • Node execution events in real-time                                      │
│     • WebSocket connections                                                   │
│     • Any errors or warnings                                                  │
│                                                                                 │
│  5. Test data lineage:                                                        │
│     • Check how data flows through nodes                                      │
│     • View transformation tracking                                            │
│     • Trace specific data paths                                               │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─ DEBUGGING COMMANDS ──────────────────────────────────────────────────────────┐
│                                                                                 │
│  View Backend Logs:                                                           │
│     Terminal ID: 17669bfe-29ba-4370-8e17-43d66241c96c                        │
│     Run: get_terminal_output(id)                                              │
│                                                                                 │
│  View Frontend Logs:                                                          │
│     Terminal ID: f0940854-1e73-4e38-8526-3cfdb306d817                        │
│     Run: get_terminal_output(id)                                              │
│                                                                                 │
│  Test WebSocket:                                                              │
│     python test_ws_temp.py                                                    │
│     (or use wscat if available)                                               │
│                                                                                 │
│  Kill Services:                                                               │
│     Backend: kill_terminal(17669bfe-29ba-4370-8e17-43d66241c96c)             │
│     Frontend: kill_terminal(f0940854-1e73-4e38-8526-3cfdb306d817)            │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘

✨ System ready! Open http://localhost:3001 in your browser to see the real-time
   AI agent execution graph with data lineage visualization.

📊 All 16 nodes are instrumented for real-time tracking:
   1. Memory Retriever → 2. Intent Router → 3. Clarifier → 4. Executive Planner
   5. Web Researcher → 6. Schema Discovery → 7. Data Fetch → 8. Normalize Data
   9. Quality Profiler → 10. Text2SQL → 11. SQL Guardrail → 12. SQL Execute
   13. Data Summarizer → 14. Insight Writer → 15. Viz Builder → 16. Reflection Judge
