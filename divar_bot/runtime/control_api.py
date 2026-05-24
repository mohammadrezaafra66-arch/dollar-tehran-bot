"""Runtime control API for pause/resume operations.

This API is intentionally minimal and operational. It allows operators or future
control planes to pause and resume job intake without killing workers.
"""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Optional


@dataclass
class RuntimeControlState:
    """Mutable runtime control state."""

    paused: bool = False

    def snapshot(self) -> Dict[str, Any]:
        return {"paused": self.paused}


class RuntimeControlApi:
    """Simple operational HTTP API for runtime pause/resume."""

    def __init__(self, host: str = "0.0.0.0", port: int = 8091) -> None:
        self.host = host
        self.port = port
        self.state = RuntimeControlState()
        self._server: Optional[ThreadingHTTPServer] = None
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Start control API server."""

        state = self.state

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:  # noqa: N802
                if self.path == "/runtime/state":
                    self._json(200, state.snapshot())
                    return
                self._json(404, {"error": "not_found"})

            def do_POST(self) -> None:  # noqa: N802
                if self.path == "/runtime/pause":
                    state.paused = True
                    self._json(200, state.snapshot())
                    return

                if self.path == "/runtime/resume":
                    state.paused = False
                    self._json(200, state.snapshot())
                    return

                self._json(404, {"error": "not_found"})

            def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
                return

            def _json(self, status: int, payload: Dict[str, Any]) -> None:
                body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        self._server = ThreadingHTTPServer((self.host, self.port), Handler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop API server."""

        if self._server:
            self._server.shutdown()
            self._server.server_close()
            self._server = None
