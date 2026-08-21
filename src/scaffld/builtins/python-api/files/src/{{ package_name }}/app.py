"""FastAPI application for {{ project_name }}."""

from __future__ import annotations

from fastapi import FastAPI

from . import __version__

app = FastAPI(title="{{ project_name }}", version=__version__)


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok"}


@app.get("/greet/{name}")
def greet(name: str) -> dict[str, str]:
    """Greet ``name``."""
    return {"message": f"Hello, {name}!"}
