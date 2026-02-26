"""Health and version endpoints."""

import tomllib
from pathlib import Path

from fastapi import APIRouter

router = APIRouter()


@router.get("/version")
async def get_version():
    """Version endpoint for healthcheck."""
    try:
        pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
        with open(pyproject_path, "rb") as f:
            pyproject_data = tomllib.load(f)
        version = pyproject_data["project"]["version"]
    except Exception:
        version = "unknown"

    return {"version": version, "status": "ok"}


@router.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}
