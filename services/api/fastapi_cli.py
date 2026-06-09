from __future__ import annotations

import argparse

import uvicorn


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the authenticated Nautilus Builder FastAPI server.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8000, type=int)
    args = parser.parse_args()

    uvicorn.run(
        "services.api.fastapi_app:create_fastapi_app",
        factory=True,
        host=args.host,
        port=args.port,
    )
