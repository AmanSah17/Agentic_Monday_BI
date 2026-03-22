import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from founder_bi_agent.backend.api.v1.router import router as api_v1_router

app = FastAPI(
    title="Founder BI Unified API",
    description="Industry-scale modular backend for Business Intelligence",
    version="2.0.0"
)

# API Versioning and Prefixing
# We mount the V1 router both with and without version prefix for compatibility
app.include_router(api_v1_router, prefix="/api/v1")
app.include_router(api_v1_router, prefix="/api")

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
    
    # Catch-all route for all other GET requests to serve the SPA
    @app.get("/{full_path:path}")
    async def serve_react_app(full_path: str):
        # This catch-all serves the React index.html for any path not matched by /api
        return FileResponse(os.path.join(frontend_path, "index.html"))
else:
    @app.get("/")
    def root():
        return {"message": "Founder BI Backend Live (Frontend not found/built)"}
