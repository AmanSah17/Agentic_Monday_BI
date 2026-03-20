# Agentic Monday BI

Agentic Monday BI is a localized, live-updating intelligence agent layered over an organization's internal Monday.com CRM boards. Leveraging a specialized LangGraph cognitive architecture, the system provides executives and founders with deep insights, specific analytics, and auto-generated data visualizations entirely using natural language commands.

## Architecture Highlights
- **Specialized Multi-Model Routing**: Implements dynamic separation of concerns between natural language models.
  - **SQL Planner (DuckDB + Qwen/Gemini)**: Reads Monday board schemas dynamically and executes statistical queries to acquire exact metrics safely inside an in-memory embedded DB layer.
  - **Reasoning Foundation (GLM-4 / Gemini)**: Reads conversation history to automatically ask clarification questions for vague timeframes and intelligently writes humanized strategic insights on rows retrieved by the SQL planner.
  - **Automated Fallback Cascade**: If the primary models hit a `429 Quota Exhaustion` or `404 Not Found` API exception, the architecture seamlessly auto-cascades through multiple pre-configured models (like `gemini-1.5-flash`, `gemini-pro`, etc.) until it finds an available instance.
- **Visual Intelligence**: Embeds JSON-based `chart_specs` auto-generated alongside the final insights to seamlessly map line/bar/pie tracking graphs dynamically in the React interface without human coding.
- **Thread Diagnostics (SQLite)**: Full session storage. An integrated SQLite engine meticulously logs conversation memory dynamically, and additionally intercepts application and prompt errors securely down to exact traces avoiding 500 crashes and storing diagnostic timelines locally.
- **FastMCP Protocol Integration**: Easily attach the data backend via Model Context Protocol tools.

## Tech Stack
- **Backend Model Tools**: LangGraph, FastAPI, FastMCP, DuckDB.
- **Memory Storage**: SQLite, (Redis-compatible).
- **LLM APIs**: Google Gemini (Pro, Flash), ZhipuAI (GLM-4.5-Air), Qwen (Coder 2.5), SiliconFlow.
- **Frontend App**: React (Vite / TS), Material UI.

## Getting Started

### 1. Prerequisites
You need both Python `3.10+` and Node.js installed.

```bash
git clone git@github.com:AmanSah17/Agentic_Monday_BI.git
cd Agentic_Monday_BI
```

### 2. Secrets & Configuration
Make sure you never push API credentials to git. The `.gitignore` manages this natively. Add your secure tokens inside a root `.env` file:

```env
MONDAY_COM_API_KEY="your-monday-token"
SILICON_FLOW_API_KEY="your-silicon-token-optional"
GOOGLE_API_KEY="your-google-ai-studio-token"
LLM_PROVIDER="gemini"
```

### 3. Start the Backend API
Load your virtual environment and run the Uvicorn webserver instance.
```bash
# Windows
.\torch_gpu\Scripts\activate
# Start Server
python -m uvicorn founder_bi_agent.backend.api:app --host 127.0.0.1 --port 8010
```

### 4. Start the React Frontend UI
Open a separate terminal to build the interface.
```bash
cd founder_bi_agent/frontend
npm install
npm run dev
```

The interface will be live immediately at `http://127.0.0.1:3000` waiting for commands.
