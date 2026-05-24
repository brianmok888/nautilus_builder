from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from services.api.app import create_app
from services.api.router import ApiResponse


class BuilderApiHandler(BaseHTTPRequestHandler):
    app = create_app()

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
        self._send_response(self.app.get(self.path))

    def do_POST(self) -> None:  # noqa: N802 - stdlib handler API
        length = int(self.headers.get("content-length", "0"))
        raw_body = self.rfile.read(length) if length else b"{}"
        payload: dict[str, Any] = json.loads(raw_body.decode("utf-8") or "{}")
        self._send_response(self.app.post(self.path, json=payload))

    def log_message(self, format: str, *args: object) -> None:
        return

    def _send_response(self, response: ApiResponse) -> None:
        body = json.dumps(response.json(), sort_keys=True).encode("utf-8")
        self.send_response(response.status_code)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except BrokenPipeError:
            return


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the dependency-free Nautilus Builder API dev server.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8000, type=int)
    args = parser.parse_args()
    ThreadingHTTPServer((args.host, args.port), BuilderApiHandler).serve_forever()


if __name__ == "__main__":
    main()
