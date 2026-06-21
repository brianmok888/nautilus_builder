"""FastAPI middleware configuration."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from packages.auth.request_id import RequestIdMiddleware


def add_cors_middleware(app: "FastAPI", origins: list[str]) -> None:
    """Add CORS middleware with explicit origins."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def add_request_id_middleware(app: "FastAPI") -> None:
    """Add request ID middleware."""
    app.add_middleware(RequestIdMiddleware)
