# 📈 Executive Intelligence BI Agent (V2)

A high-performance Business Intelligence and Data Science dashboard designed for founders and executives. This agent connects directly to Monday.com boards, processes massive datasets using DuckDB, and delivers interactive, actionable insights through a custom-built draggable grid interface.

---

## 🌟 V2 Interactive Dashboard
The core of this release is the **V2 Data Science Dashboard**, an interactive workspace that empowers executives to customize their view of the business.

### Key Features:
- **Draggable & Resizable Grid:** Built with a custom implementation of `react-grid-layout` and a native `ResizeObserver` engine for seamless 12-column responsive layout management.
- **Real-Time Data Sync:** Direct integration with Monday.com via a high-performance Python backend.
- **Optimized Latency:** Utilizes a single consolidated API endpoint (`/analytics/dashboard-all`) powered by `DuckDB` on the backend to reduce multi-chart load times from minutes to under 14 seconds.

---

## 🔬 Data Science Insights
Seven deep-dive analytical modules providing high-resolution visibility into operations and sales.

1.  **Revenue Leakage Waterfall:** Tracks value drop-off from `Quoted Amount (GST Incl)` to `Billed Amount` and finally `Actually Collected` per sector.
2.  **Execution Velocity (Bottleneck Analysis):** Calculates the delta between `Probable Start Dates` and `Actual Billing Months` to identify systematic delays in project execution.
3.  **Predictive Pipeline Matrix:** Real-time modeling of `Deal Status` aligned against mathematical `Closure Probability` to forecast true revenue.
4.  **Owner Performance Matrix:** Scatters team members based on their `Active Pipeline Value` and modeled `Win Probability`.
5.  **Client Concentration (Pareto):** Distribution of pipeline value across clients to identify key account dependencies.
6.  **Operational Volume vs Billed:** Critical comparison of physical operational activity against actual financial billing quantity.
7.  **Average Deal Size Analysis:** Segmentation of average deal values by product nature and deal structure.

---

## 🛠 Tech Stack

### Frontend
- **Framework:** React + Vite + TypeScript
- **Visualization:** Recharts (Sanitized for SVG precision)
- **Layout:** react-grid-layout + custom ResizeObserver
- **Animations:** Framer Motion

### Backend
- **Engine:** FastAPI (Python 3.10)
- **Database:** DuckDB (OLAP-optimized)
- **Integration:** Monday.com API (MondayBITools)

---

## 🚀 Deployment

### Local Development
1. **Backend:**
   ```bash
   cd founder_bi_agent/backend
   pip install -r requirements.txt
   python -m uvicorn api:app --reload --port 8010
   ```
2. **Frontend:**
   ```bash
   cd founder_bi_agent/frontend
   npm install
   npm run dev
   ```

### Production (Render.com)
The project is pre-configured for a unified Docker deployment via `render.yaml`.
- **Dockerized:** The `Dockerfile` handles the multi-stage build (React compile + Python environment).
- **Environment Variables:**
  - `LLM_PROVIDER`: huggingface / groq
  - `MONDAY_COM_API_KEY`: Your Monday.com developer token
  - `MONDAY_MODE`: `monday` (to use live API)

---

## 📂 Implementation Details
The dashboard's layout is dynamically managed in `AnalyticsDashboard.tsx`. Each chart represents a "Widget" that can be moved or resized. The backend logic for the new Data Science queries is rigorously defined in `statistical_queries.py` and consolidated into the `execute_dashboard_queries` service method for maximum efficiency.
