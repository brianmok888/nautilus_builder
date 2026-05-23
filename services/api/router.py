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
        params: dict[str, str] = {}
        if handler is None:
            handler, params = self._match_parameterized_route(method, path)
        if handler is None:
            return ApiResponse({"error": "not_found", "path": path}, status_code=404)

        if method.upper() == "POST" and params:
            result = handler(**params, payload=payload or {})
        elif method.upper() == "POST":
            result = handler(payload or {})
        elif params:
            result = handler(**params)
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

    def _match_parameterized_route(self, method: str, path: str) -> tuple[RouteHandler | None, dict[str, str]]:
        normalized_path = self._normalize_path(path)
        path_parts = normalized_path.strip("/").split("/")
        for (route_method, route_path), handler in self._routes.items():
            if route_method != method.upper():
                continue
            route_parts = route_path.strip("/").split("/")
            if len(route_parts) != len(path_parts):
                continue
            params: dict[str, str] = {}
            matched = True
            for route_part, path_part in zip(route_parts, path_parts):
                if route_part.startswith("{") and route_part.endswith("}"):
                    params[route_part[1:-1]] = path_part
                elif route_part != path_part:
                    matched = False
                    break
            if matched:
                return handler, params
        return None, {}
