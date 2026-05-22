from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


RouteHandler = Callable[..., Any]


@dataclass(frozen=True)
class ApiResponse:
    payload: Any
    status_code: int = 200

    def json(self) -> Any:
        return self.payload


class ApiApp:
    def __init__(self) -> None:
        self._routes: dict[tuple[str, str], RouteHandler] = {}

    def route(self, method: str, path: str, handler: RouteHandler) -> None:
        self._routes[(method.upper(), self._normalize_path(path))] = handler

    def get(self, path: str) -> ApiResponse:
        return self._dispatch("GET", path)

    def post(self, path: str, json: dict[str, Any] | None = None) -> ApiResponse:
        return self._dispatch("POST", path, json or {})

    def _dispatch(self, method: str, path: str, payload: dict[str, Any] | None = None) -> ApiResponse:
        route_key = (method.upper(), self._normalize_path(path))
        handler = self._routes.get(route_key)
        if handler is None:
            return ApiResponse({"error": "not_found", "path": path}, status_code=404)

        if method.upper() == "POST":
            result = handler(payload or {})
        else:
            result = handler()
        if isinstance(result, ApiResponse):
            return result
        return ApiResponse(result)

    @staticmethod
    def _normalize_path(path: str) -> str:
        if not path.startswith("/"):
            path = f"/{path}"
        return path.rstrip("/") or "/"
