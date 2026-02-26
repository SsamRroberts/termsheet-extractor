import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from core.config import settings
from core.log import setup_logging
from db.db import test_database_connection
from routes.extraction import router as extraction_router
from routes.health import router as health_router
from routes.products import router as products_router

setup_logging()

# Test database connection before initialising the app
test_database_connection()

fastapp = FastAPI(debug=True)

fastapp.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API routers ───────────────────────────────────────────────────────────────

fastapp.include_router(health_router, prefix="/api")
fastapp.include_router(extraction_router, prefix="/api")
fastapp.include_router(products_router, prefix="/api")

# ── Serve frontend build (must be AFTER all /api routes) ──────────────────────

frontend_dist_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist")

if os.path.exists(frontend_dist_path):
    assets_dir = os.path.join(frontend_dist_path, "assets")
    if os.path.exists(assets_dir):
        fastapp.mount(
            "/assets", StaticFiles(directory=assets_dir), name="assets"
        )


@fastapp.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """Serve the SPA for all non-API routes."""
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API endpoint not found")

    # Serve static files directly if they exist in the dist folder
    if "." in full_path:
        file_path = os.path.join(frontend_dist_path, full_path)
        if os.path.exists(file_path):
            return FileResponse(file_path)

    # For all other routes, serve index.html (SPA client-side routing)
    index_path = os.path.join(frontend_dist_path, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)

    raise HTTPException(status_code=404, detail="Frontend not found")
