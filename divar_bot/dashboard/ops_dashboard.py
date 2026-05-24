"""Lightweight operations dashboard for Afra Divar Bot.

This dashboard is intentionally operational and temporary. It is not the final
AfraKala assistant web app, CRM, or business control panel. Its role is to expose
runtime status until the main Afra assistant web application is ready.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable, Mapping, Optional


SnapshotProvider = Callable[[], Mapping[str, Any]]


@dataclass(frozen=True)
class DashboardSettings:
    """Dashboard server settings."""

    host: str = "0.0.0.0"
    port: int = 8090
    title: str = "Afra Divar Bot Operations"


class OperationsDashboard:
    """Small HTML dashboard for local and temporary operational visibility."""

    def __init__(self, settings: Optional[DashboardSettings] = None, snapshot_provider: Optional[SnapshotProvider] = None) -> None:
        self.settings = settings or DashboardSettings()
        self.snapshot_provider = snapshot_provider or (lambda: {})
        self._server: Optional[ThreadingHTTPServer] = None

    def start(self) -> None:
        """Start dashboard HTTP server."""

        provider = self.snapshot_provider
        title = self.settings.title

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:  # noqa: N802
                if self.path == "/":
                    self._write_html(self._html())
                    return
                if self.path == "/api/snapshot":
                    self._write_json(dict(provider()))
                    return
                self.send_response(404)
                self.end_headers()

            def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
                return

            def _write_json(self, payload: Mapping[str, Any]) -> None:
                body = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def _write_html(self, body_text: str) -> None:
                body = body_text.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def _html(self) -> str:
                return f"""
<!doctype html>
<html lang=\"fa\" dir=\"rtl\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>{title}</title>
  <style>
    body {{ margin:0; font-family:Tahoma,Arial; background:#0f172a; color:#e5e7eb; }}
    main {{ padding:28px; max-width:1100px; margin:auto; }}
    .card {{ background:#111827; border:1px solid rgba(255,255,255,.08); border-radius:18px; padding:18px; margin:12px 0; }}
    pre {{ direction:ltr; text-align:left; white-space:pre-wrap; background:#020617; padding:16px; border-radius:12px; }}
    .badge {{ display:inline-block; padding:6px 10px; border-radius:999px; background:#064e3b; color:#bbf7d0; }}
  </style>
</head>
<body>
  <main>
    <h1>{title}</h1>
    <p class=\"badge\">Temporary Operations Panel</p>
    <div class=\"card\">
      <h2>Runtime Snapshot</h2>
      <pre id=\"snapshot\">loading...</pre>
    </div>
  </main>
  <script>
    async function loadSnapshot() {{
      const response = await fetch('/api/snapshot');
      const data = await response.json();
      document.getElementById('snapshot').textContent = JSON.stringify(data, null, 2);
    }}
    loadSnapshot();
    setInterval(loadSnapshot, 5000);
  </script>
</body>
</html>
"""

        self._server = ThreadingHTTPServer((self.settings.host, self.settings.port), Handler)
        self._server.serve_forever()

    def stop(self) -> None:
        """Stop dashboard HTTP server."""

        if self._server:
            self._server.shutdown()
            self._server.server_close()
            self._server = None
