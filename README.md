# Agentic Monday BI: AI-Native Revenue & Operations Intelligence

Welcome to **Agentic Monday BI**—a proprietary, enterprise-grade cognitive architecture designed specifically for C-Level Executives (CEOs, CTOs, COOs, and Founders). It bridges the gap between raw, siloed CRM data (in Monday.com) and instant, conversational strategic intelligence.

By utilizing high-speed **Agentic Orchestration** and localized embedded databases, Agentic Monday BI turns a static dashboard into an autonomous data analyst capable of answering complex business questions in under 10 seconds.

---

## 🚀 The Core Problem It Solves

Historically, if a CEO needed to know *"What is the exact pipeline value of deals closing this quarter broken down by sector?"*, the workflow looked like this:
1. Ping a Data Analyst or RevOps Manager.
2. Wait hours (or days) for a custom SQL query or Tableau dashboard to be built.
3. Receive a static chart that inevitably requires follow-up questions ("Wait, what if we exclude paused deals?").
4. Repeat the cycle.

**Agentic Monday BI fundamentally eliminates the "Data Request Queue".**

It allows business leaders to ask hyper-specific, multi-dimensional queries in plain English through a chat interface. The system autonomously reads live Monday.com schemas, writes the SQL defensively, executes it locally, and generates both the chart constraints and a human-readable professional summary instantly.

---

## 💼 Executive Use Cases

This engine is optimized for high-impact decision-makers navigating complex datasets (e.g., Sales Funnels and Work Order Operations).

### For the Chief Executive Officer (CEO)
- **Instant Pipeline Visibility:** *"Show me the total value of all 'In Progress' deals categorized by Service Type."*
  - *Value:* Zero lag time between a board-level question and absolute data clarity.
- **Conversion Analytics:** *"What is the ratio of 'Closed Won' to 'Lost'?"*
  - *Value:* Understand market traction natively without navigating complex CRM logic.

### For the Chief Operating Officer (COO)
- **Bottleneck Detection:** *"How many work orders have been stuck in the 'Planning' phase for over 30 days?"*
  - *Value:* Identify operational slow-downs and delivery risks instantly before they impact quarterly revenue recognition.
- **Capacity Forecasting:** *"Break down our current open work orders by their current status and link them to the allocated project values."*
  - *Value:* Immediate operational snapshot for resource allocation.

### For the Chief Technology Officer (CTO)
- **Secure, Autonomous Infrastructure:** 
  - *Value:* The system pulls live data into an ephemeral, in-memory **DuckDB** instance. Source systems (Monday.com) are completely protected from data-mutation (Read-Only SQL Enforcement), preventing hallucinated deletions.
- **Multi-Model Extensibility:** 
  - *Value:* Architecture is aggressively vendor-agnostic. Deployed natively with **Groq (Llama-3.3-70b)** for lightning-fast ~800 tokens/second reasoning, while maintaining silent fallbacks to `Gemini` or `Qwen` if upstream quotas fail (429/404 handling).
- **Comprehensive Tracing:** 
  - *Value:* A strictly typed **SQLite** logging engine caches both conversational memory and pipeline traces (prompt schemas, fallback triggers, parsing errors) ensuring 100% audibility of AI actions internally.

---

## 🧠 How the Agentic Orchestration Works

Unlike simple "RAG" (Retrieval-Augmented Generation) which just searches text documents, this is a **Node-based Cognitive Graph** (powered by LangGraph):

1. **Intent Router (LLM):** The system first evaluates the semantic intent of the executive's question (`pipeline_health` vs `general_bi`) to heavily scope the context window.
2. **Clarifier Agent (LLM):** If a question is dangerously vague (e.g., *"How did we do?"*), the Clarifier intercepts execution and asks the executive to specify dimensions (like timeframes) to prevent hallucinated assumptions.
3. **Data Fetcher (API):** Concurrently loads live schema maps directly from Monday.com via multi-threading.
4. **NLP-to-SQL Planner (LLM):** A dedicated coding model (like `Qwen-2.5-Coder` or `Llama-3`) dynamically writes hyper-accurate DuckDB SQL against the exact column structures pulled seconds earlier.
5. **Execution Engine (DuckDB):** The SQL runs cleanly in RAM. Pydantic-validated guardrails automatically reject any `DROP`, `DELETE`, or `UPDATE` queries.
6. **Insight Writer (LLM):** The raw statistical outputs are passed back to the Foundation model which generates a concise, professional executive summary, while the React UI dynamically auto-generates visual plots.

---

## 🛠 Getting Started

### 1. Requirements
Ensure Python `3.10+` and Node.js are available in your ecosystem.

```bash
git clone git@github.com:AmanSah17/Agentic_Monday_BI.git
cd Agentic_Monday_BI
```

### 2. Connect Your Enterprise Securely
Duplicate `.env.example` into a local `.env`. Ensure you provide your authentication tokens for Monday and your preferred LLM gateway (Groq, Gemini, or SiliconFlow). This repo rigorously `.gitignore`s your `.env` to prevent credential leakage.

```env
MONDAY_COM_API_KEY="your-monday-token"
GROQ_API_KEY="gsk_your-groq-token"
LLM_PROVIDER="groq"
```

### 3. Initialize the Backend Services
Activate your isolated Python environment, install `requirements.txt`, and deploy the asynchronous FastAPI layer.

```bash
pip install -r requirements.txt
python -m uvicorn founder_bi_agent.backend.api:app --host 127.0.0.1 --port 8010
```

### 4. Deploy the Executive Dashboard
In a secondary terminal, spin up the React (Vite) frontend.

```bash
cd founder_bi_agent/frontend
npm install
npm run dev
```

The system is now live at `http://localhost:3000`. Simply engage with the interface to command your data.
