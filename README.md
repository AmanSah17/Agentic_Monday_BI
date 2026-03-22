# 📈 Executive Intelligence BI Agent (V3 - Agentic Edition)

A production-grade Business Intelligence platform designed for Founders and CEOs. This system leverages **LangGraph-driven agentic reasoning**, **DuckDB analytical processing**, and a **Draggable React Dashboard** to transform Monday.com data into strategic insights.

---

## 🧠 Backend Architecture: The 15-Node Reasoning Engine

The core of the system is a sophisticated **Nodal Reasoning Agent** built on LangGraph. Unlike traditional dashboards that simply dump data, this agent *thinks* through every query using a deterministic yet smart traversal.

### 1. Intent & Context Phase
- **Memory Retriever**: Scans vector memory for conversation history and user preferences.
- **Intent Router**: Classifies queries into recursive logic paths (e.g., `pipeline_health`, `operational_audit`).
- **Clarifier**: Pauses execution if the query is ambiguous, ensuring precisely filtered data.

### 2. Live Discovery Phase
- **Executive Planner**: Determines if external web research (via Tavily) is needed to supplement board data.
- **Schema Discovery**: Real-time auditing of Monday.com board structures—detecting column changes dynamically.
- **Data Normalize & Profile**: Cleans currency, sanitizes dates, and profiles data quality (missing values/anomalies).

### 3. Intelligence & Synthesis Phase
- **Text2SQL Planner**: Translates natural language into high-performance DuckDB SQL.
- **Data Summarizer**: Performs automated Pareto Analysis, Temporal Momentum tracking, and Cross-Table Yield connectivity.
- **Insight Writer**: Synthesizes SQL results and statistical profiles into a narrative business story.
- **Reflection Judge**: A self-correcting node that retries the process if the result is logically inconsistent.

---

## 🎨 Frontend Implementation: Per-Page Breakdown

The frontend is a high-performance React application optimized for "Executive Overview" and "Deep Dive" modes.

### 1. Analytics Dashboard (`/dashboard`)
- **Draggable Mesh**: 12-column responsive grid allowing complete layout customization.
- **Visual Intelligence**: 7 specialized charts (Recharts) for Revenue Leakage, Velocity Matrix, and Portfolio Risk.
- **Logic Annotations**: Every chart includes a **"Logic & Insights"** block that explains the *business meaning* behind the data, formatted for quick executive reading.
- **Horizontal Throughput**: Chart 5 (Operations Matrix) uses a specialized horizontal scrollable layout to handle 25+ detailed status categories without label collision.

### 2. AI Chat Experience (`/chat`)
- **Reasoning Trace**: A dedicated sidebar showing the agent's "Thought Process" in real-time as it traverses the 15-node backend graph.
- **Streaming Insights**: Markdown-rendered responses that incorporate data-driven recommendations and "Headline Stories."
- **Interactive Widgets**: Integrated chart rendering within the chat flow for immediate visual proof.

### 3. Navigation & Core Architecture
- **Path-Based Routing**: Native support for `/chat` and `/dashboard` allowing deep-linking and "Open in New Tab" functionality.
- **Sidebar Engine**: Anchor-based navigation with `popstate` listeners for SPA performance with multi-tab flexibility.
- **State Management**: Unified `BIState` ensuring consistency between what the agent "talks about" and what the dashboard "shows."

---

## 🛠 Tech Stack

- **Backend**: FastAPI, LangGraph, DuckDB, Google Gemini (Pro), Pydantic.
- **Frontend**: React 18, Vite, Recharts, Framer Motion, Tailwind CSS.
- **Integration**: Monday.com GraphQL API, Vector Memory (ChromaDB).

---

## 🚀 Deployment & Production

This system is optimized for **Render Cloud** using a unified Docker architecture.

### 1. Production Architecture
- **Web Service**: A Linux container running FastAPI which also serves the pre-bundled React frontend as static assets.
- **Database**: Managed PostgreSQL (`agentic_bi_prod`) for persistent history and error tracking.
- **Cache**: Managed Redis (`agentic_bi_cache`) for low-latency session memory.

### 2. Deploying to Render
1. **GitHub Connection**: Connect your repository to Render.
2. **Blueprint Implementation**: Render will automatically detect the `render.yaml` file.
3. **Environment Variables**: Ensure the following are set in the Render Dashboard:
   - `GOOGLE_API_KEY`: Your Gemini Pro API key.
   - `MONDAY_COM_API_KEY`: Your Monday.com API token.
   - `TAVILY_API_KEY`: For real-time web research tools.
   - *Optional*: `LANGSMITH_API_KEY`, `GROQ_API_KEY`, `SILICON_FLOW_API_KEY`.

### 3. Local Development (Quick Start)
1. **Backend**:
   ```bash
   python -m uvicorn founder_bi_agent.backend.main:app --port 8010 --reload
   ```
2. **Frontend**:
   ```bash
   cd founder_bi_agent/frontend && npm run dev
   ```

---

## 🛠 Tech Stack Detail

- **Reasoning**: LangGraph (15-Node DAG)
- **Database**: PostgreSQL + DuckDB (In-Memory Analytics)
- **Memory**: Redis (Cache) + ChromaDB (Vector)
- **Frontend**: React 18, Vite, Framer Motion (Node Animations)
- **API**: FastAPI (Asynchronous WebSocket Streaming)

---

## 🔒 Security & Performance
- **Connection Pooling**: PostgreSQL uses a managed pool for concurrent user support.
- **Session Isolation**: Every user session is isolated via `thread_id` in LangGraph and `session_id` in the history store.
- **Real-time Engine**: WebSocket streaming ensures sub-100ms UI updates for agent thought processes.
