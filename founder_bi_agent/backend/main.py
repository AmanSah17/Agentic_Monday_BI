import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from founder_bi_agent.backend.api.v1.router import router as api_v1_router
from founder_bi_agent.backend.api.ws import router as ws_router, session_router, session_manager as ws_session_manager
from founder_bi_agent.backend.core.session_manager import SessionManager
from founder_bi_agent.backend.db.postgres_db import PostgresManager
from founder_bi_agent.backend.core.config import AgentSettings
import founder_bi_agent.backend.api.ws as ws_module

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB schema on startup (Disabled for local testing robustness)
    # try:
    #     settings = AgentSettings.from_env()
    #     db = PostgresManager(settings)
    #     if db._pool:
    #         db._init_schema()
    # except Exception as e:
    #     import logging
    #     logging.getLogger("uvicorn.error").error(f"Lifespan DB Init Error: {e}")
    yield

app = FastAPI(
    title="Founder BI Unified API",
    description="Industry-scale modular backend for Business Intelligence",
    version="2.0.0",
    lifespan=lifespan
)

# Initialize session manager and inject it into ws module
_session_manager = SessionManager()
ws_module.session_manager = _session_manager

# API Versioning and Prefixing
# We mount the V1 router both with and without version prefix for compatibility
app.include_router(api_v1_router, prefix="/api/v1")
app.include_router(api_v1_router, prefix="/api")

# WebSocket and Session Routes
# Note: ws_router already has prefix="/ws" defined internally
app.include_router(ws_router)
app.include_router(session_router)

# CORS Middleware for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Static File Serving for React Frontend (SPA Support) ---
# Resolve the frontend dist path relative to this file
backend_root = os.path.dirname(os.path.abspath(__file__))
frontend_path = os.path.join(backend_root, "..", "frontend", "dist")

if os.path.exists(frontend_path):
    # Explicitly mount assets for JS/CSS bundles
    assets_path = os.path.join(frontend_path, "assets")
    if os.path.exists(assets_path):
        app.mount("/assets", StaticFiles(directory=assets_path), name="assets")
    
    # Catch-all route for all other requests to serve the SPA
    # This should only serve the frontend for non-API paths
    @app.get("/{full_path:path}")
    async def serve_react_app(full_path: str):
        # Only serve SPA for non-API paths
        if full_path.startswith("api") or full_path.startswith("ws") or full_path.startswith("sessions"):
            # Let FastAPI handle 404 for actual API endpoints
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Endpoint not found")
        # Serve the React app for all other paths (SPA routing support)
        index_path = os.path.join(frontend_path, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        else:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Frontend not built")
else:
    @app.get("/")
    def root():
        return {"message": "Founder BI Backend Live (Frontend not found/built)"}
