"""The HTTP face of the watcher: the page, its state, and its buttons.

Standard library only, so it runs from the single-file build. Bound to
127.0.0.1: this is one student's repository, not a service.

Three checks keep other websites out. The Host header must be loopback,
which stops DNS rebinding (a hostile page pointing its own domain at
127.0.0.1 to read the repo). Every POST must also carry a matching Origin,
a JSON content type, and a per-run token that only the served page knows,
which stops cross-site form posts from pressing the buttons.
"""

from __future__ import annotations

import json
import secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib import resources
from typing import Any
from urllib.parse import parse_qs, urlsplit

import yaml

from git_tutorial.web.engine import Engine

ASSETS = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
    "/app.css": ("app.css", "text/css; charset=utf-8"),
}
COMMANDS = {"/answer": "answer", "/hint": "hint", "/next": "next", "/reset": "reset",
            "/ping": "ping"}
MAX_BODY = 4096
TOKEN_SLOT = "__WT_TOKEN__"
LOOPBACK = ("127.0.0.1", "localhost")


def asset(name: str) -> bytes:
    return resources.files("git_tutorial.web").joinpath("assets", name).read_bytes()


def glossary(engine: Engine) -> bytes:
    path = engine.session.pack.root / "glossary.yaml"
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        data = {}
    return json.dumps(data).encode()


class Server(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, engine: Engine, port: int) -> None:
        self.engine = engine
        self.token = secrets.token_urlsafe(24)
        super().__init__(("127.0.0.1", port), Handler)

    @property
    def port(self) -> int:
        return int(self.server_address[1])

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.port}/"


class Handler(BaseHTTPRequestHandler):
    server: Server

    def do_GET(self) -> None:
        if not self._loopback_host():
            return
        url = urlsplit(self.path)
        if url.path in ASSETS:
            name, kind = ASSETS[url.path]
            body = asset(name)
            if name == "index.html":
                body = body.replace(TOKEN_SLOT.encode(), self.server.token.encode())
            self._send(200, body, kind)
        elif url.path == "/glossary.json":
            self._send(200, glossary(self.server.engine), "application/json")
        elif url.path == "/state":
            raw = parse_qs(url.query).get("since", ["-1"])[0]
            since = int(raw) if raw.lstrip("-").isdigit() else -1
            self._json(200, self.server.engine.wait(since))
        else:
            self._send(404, b"not found", "text/plain")

    def do_POST(self) -> None:
        if not self._loopback_host() or not self._trusted_post():
            return
        kind = COMMANDS.get(urlsplit(self.path).path)
        if kind is None:
            self._send(404, b"not found", "text/plain")
            return
        length = int(self.headers.get("Content-Length") or 0)
        if length > MAX_BODY:
            self._json(413, {"ok": False, "error": "request too large"})
            return
        try:
            data = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            self._json(400, {"ok": False, "error": "body is not JSON"})
            return
        if not isinstance(data, dict):
            self._json(400, {"ok": False, "error": "body must be a JSON object"})
            return
        result = dict(self.server.engine.submit(kind, data))
        status = int(result.pop("status", 200 if result.get("ok") else 400))
        self._json(status, {**result, "seq": self.server.engine.current["seq"]})

    # -- the checks ------------------------------------------------------------

    def _loopback_host(self) -> bool:
        host = (self.headers.get("Host") or "").rsplit(":", 1)[0]
        if host in LOOPBACK:
            return True
        self._send(403, b"forbidden", "text/plain")
        return False

    def _trusted_post(self) -> bool:
        origin = self.headers.get("Origin") or ""
        allowed = {f"http://{name}:{self.server.port}" for name in LOOPBACK}
        kind = (self.headers.get("Content-Type") or "").split(";")[0].strip()
        token = self.headers.get("X-WT-Token") or ""
        if (origin in allowed and kind == "application/json"
                and secrets.compare_digest(token, self.server.token)):
            return True
        self._send(403, b"forbidden", "text/plain")
        return False

    # -- responses -------------------------------------------------------------

    def _json(self, code: int, payload: dict[str, Any]) -> None:
        self._send(code, json.dumps(payload).encode(), "application/json")

    def _send(self, code: int, body: bytes, kind: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        pass  # the terminal belongs to the student, not to an access log


def serve(engine: Engine, *, port: int = 0) -> Server:
    return Server(engine, port)
