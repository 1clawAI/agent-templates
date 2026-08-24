#!/usr/bin/env python3
"""
Minimal browser chat UI for `1claw spawn` templates.

Listens on CHAT_UI_PORT (default 3000). Forwards chat to the framework agent on
AGENT_INTERNAL_PORT (default 3001) when available, otherwise falls back to Shroud
via the host daemon /proxy (credentials never enter the container).
"""

from __future__ import annotations

import json
import os
import socket
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

PORT = int(os.environ.get("CHAT_UI_PORT", "3000"))
AGENT_PORT = int(os.environ.get("AGENT_INTERNAL_PORT", "3001"))
SOCKET_PATH = os.environ.get("ONECLAW_DAEMON_SOCKET", "/run/1claw/daemon.sock")
SECRET_PREFIX = os.environ.get("ONECLAW_SECRET_PREFIX", "")
AGENT_ID = os.environ.get("ONECLAW_AGENT_ID", "")
FRAMEWORK = os.environ.get("ONECLAW_FRAMEWORK", "agent")
MODE = os.environ.get(
    "ONECLAW_MODE",
    "local" if os.environ.get("ONECLAW_LOCAL_VAULT") == "true" else "cloud",
)

LLM_VIA_SHROUD = os.environ.get("ONECLAW_LLM_VIA_SHROUD", "").lower() == "true"
SHROUD_URL = (os.environ.get("ONECLAW_SHROUD_URL") or "https://shroud.1claw.xyz").rstrip("/")
SHROUD_SECRET = os.environ.get("ONECLAW_SHROUD_SECRET", "")
SHROUD_API_KEY_SECRET = os.environ.get("ONECLAW_SHROUD_API_KEY_SECRET", "")
SHROUD_PROVIDER = os.environ.get("ONECLAW_SHROUD_PROVIDER", "openai")
SHROUD_MODEL = os.environ.get("ONECLAW_SHROUD_MODEL", "gpt-4o-mini")
SYSTEM_PROMPT = os.environ.get(
    "ONECLAW_SHROUD_SYSTEM_PROMPT",
    "You are a helpful AI agent running inside a 1Claw secure container. "
    "Your credentials are held by the host daemon and never exposed to you.",
)

HISTORY_MAX = 20
_conversation: list[dict[str, str]] = []
_lock = threading.Lock()

_INDEX_HTML = Path(__file__).with_name("index.html")
if _INDEX_HTML.is_file():
    INDEX_HTML = _INDEX_HTML.read_text(encoding="utf-8")
else:
    INDEX_HTML = "<h1>1Claw Agent</h1>"


def _daemon_request(method: str, path: str, body: dict[str, Any] | None = None) -> tuple[int, dict[str, Any] | None]:
    payload = json.dumps(body).encode("utf-8") if body is not None else None
    headers = [
        f"{method} {path} HTTP/1.1",
        "Host: localhost",
        "Content-Type: application/json",
        "Connection: close",
    ]
    if SECRET_PREFIX:
        headers.append(f"X-Secret-Prefix: {SECRET_PREFIX}")
    if payload is not None:
        headers.append(f"Content-Length: {len(payload)}")
    headers.append("")
    headers.append("")
    raw = "\r\n".join(headers).encode("utf-8") + (payload or b"")

    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.settimeout(120)
    try:
        sock.connect(SOCKET_PATH)
        sock.sendall(raw)
        chunks: list[bytes] = []
        while True:
            part = sock.recv(65536)
            if not part:
                break
            chunks.append(part)
    finally:
        sock.close()

    text = b"".join(chunks).decode("utf-8", errors="replace")
    if "\r\n\r\n" not in text:
        return 0, None
    _, body_text = text.split("\r\n\r\n", 1)
    status_line = text.split("\r\n", 1)[0]
    try:
        status = int(status_line.split()[1])
    except (IndexError, ValueError):
        status = 0
    try:
        parsed = json.loads(body_text) if body_text.strip() else None
    except json.JSONDecodeError:
        parsed = {"raw": body_text}
    return status, parsed


def _daemon_reachable() -> bool:
    try:
        status, _ = _daemon_request("GET", "/health")
        return status == 200
    except OSError:
        return False


def _shroud_chat(user_text: str) -> tuple[bool, str]:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}, *_conversation, {"role": "user", "content": user_text}]
    proxy_body: dict[str, Any] = {
        "secretName": SHROUD_SECRET,
        "url": f"{SHROUD_URL}/v1/chat/completions",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
            "X-Shroud-Provider": SHROUD_PROVIDER,
        },
        "body": json.dumps({"model": SHROUD_MODEL, "messages": messages}),
    }
    if SHROUD_API_KEY_SECRET:
        proxy_body["injectSecrets"] = [SHROUD_API_KEY_SECRET]

    status, body = _daemon_request("POST", "/proxy", proxy_body)
    if status != 200 or not body:
        detail = (body or {}).get("error") if body else "unknown daemon error"
        return False, f"Daemon refused the LLM call ({status}): {detail}"

    upstream_status = body.get("status", 502)
    raw_upstream = body.get("body", "")
    try:
        upstream = json.loads(raw_upstream) if isinstance(raw_upstream, str) else raw_upstream
    except json.JSONDecodeError:
        upstream = {"raw": raw_upstream}

    if upstream_status != 200:
        err = upstream.get("error") if isinstance(upstream, dict) else upstream
        if isinstance(err, dict):
            msg = err.get("message") or str(err)
        else:
            msg = str(err or upstream)
        return False, f"Shroud/upstream returned {upstream_status}: {msg}"

    content = (
        upstream.get("choices", [{}])[0]
        .get("message", {})
        .get("content")
        if isinstance(upstream, dict)
        else None
    )
    if not content:
        return False, f"No content in model response: {str(upstream)[:400]}"
    return True, str(content)


def _agent_chat(user_text: str) -> dict[str, Any] | None:
    req = Request(
        f"http://127.0.0.1:{AGENT_PORT}/chat",
        data=json.dumps({"message": user_text}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, OSError):
        return None

    if isinstance(data, dict) and data.get("response"):
        return {
            "reply": str(data["response"]),
            "tool": data.get("framework") or FRAMEWORK,
        }
    if isinstance(data, dict) and data.get("error"):
        return {"reply": str(data["error"]), "tool": "agent_error"}
    return None


def handle_chat(message: str) -> dict[str, Any]:
    text = (message or "").strip()

    if text in ("", "/help"):
        llm_line = (
            f"LLM is wired via Shroud ({SHROUD_PROVIDER}/{SHROUD_MODEL}) — type a message to chat.\n"
            if LLM_VIA_SHROUD and SHROUD_SECRET
            else "Framework agent on port "
            f"{AGENT_PORT} handles chat when running; Shroud fallback uses the daemon.\n"
        )
        return {
            "reply": (
                f"1Claw {FRAMEWORK} agent ready.\n"
                f"{llm_line}"
                "Commands:\n"
                "  /secrets — list secret names available via the daemon\n"
                "  /info    — show runtime info\n"
                "Secret values never enter this container."
            ),
            "tool": None,
        }

    if text == "/info":
        llm = f" · llm=shroud:{SHROUD_PROVIDER}/{SHROUD_MODEL}" if LLM_VIA_SHROUD else " · llm=agent"
        return {
            "reply": (
                f"Agent {AGENT_ID or '(local)'} · framework={FRAMEWORK} · "
                f"vault={MODE} · chat_ui=:{PORT} · agent=:{AGENT_PORT}{llm}"
            ),
            "tool": "info",
        }

    if text == "/secrets":
        path = f"/secrets?prefix={SECRET_PREFIX}" if SECRET_PREFIX else "/secrets"
        try:
            status, body = _daemon_request("GET", path)
            if status != 200:
                return {"reply": f"Daemon returned {status}", "tool": "list_secrets"}
            names = [s.get("name", "") for s in (body or {}).get("secrets", [])]
            names = [n for n in names if n]
            reply = (
                "Available secrets:\n" + "\n".join(f"  • {n}" for n in names)
                if names
                else "No secrets available to this agent."
            )
            return {"reply": reply, "tool": "list_secrets"}
        except OSError as exc:
            return {"reply": f"Could not reach daemon: {exc}", "tool": "list_secrets"}

    agent_out = _agent_chat(text)
    if agent_out is not None:
        return agent_out

    if LLM_VIA_SHROUD and SHROUD_SECRET:
        try:
            ok, reply = _shroud_chat(text)
            if ok:
                with _lock:
                    _conversation.append({"role": "user", "content": text})
                    _conversation.append({"role": "assistant", "content": reply})
                    while len(_conversation) > HISTORY_MAX:
                        _conversation.pop(0)
            return {"reply": reply, "tool": "shroud_llm"}
        except OSError as exc:
            return {"reply": f"Could not reach the daemon for LLM call: {exc}", "tool": "shroud_llm"}

    return {
        "reply": (
            "No LLM configured. Re-run spawn with --agent-key ocv_... "
            "and optional --llm-api-key. The host daemon injects Shroud credentials."
        ),
        "tool": None,
    }


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stderr.write(f"[spawn-chat-ui] {self.address_string()} - {fmt % args}\n")

    def _json(self, status: int, obj: dict[str, Any]) -> None:
        body = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        path = self.path.split("?", 1)[0]
        if path == "/health":
            self._json(
                200,
                {
                    "status": "ok",
                    "framework": FRAMEWORK,
                    "agent_port": AGENT_PORT,
                    "llm_wired": LLM_VIA_SHROUD and bool(SHROUD_SECRET),
                },
            )
            return
        if path == "/api/info":
            self._json(
                200,
                {
                    "agentId": AGENT_ID or None,
                    "framework": FRAMEWORK,
                    "runtime": "docker",
                    "mode": MODE,
                    "agentPort": AGENT_PORT,
                    "llm": (
                        {
                            "via": "shroud",
                            "provider": SHROUD_PROVIDER,
                            "model": SHROUD_MODEL,
                        }
                        if LLM_VIA_SHROUD
                        else None
                    ),
                    "daemonReachable": _daemon_reachable(),
                },
            )
            return
        if path in ("/", "/index.html"):
            html = INDEX_HTML.replace("__FRAMEWORK__", FRAMEWORK)
            body = html.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self._json(404, {"error": "not found"})

    def do_POST(self) -> None:
        path = self.path.split("?", 1)[0]
        if path != "/api/chat":
            self._json(404, {"error": "not found"})
            return
        length = int(self.headers.get("Content-Length", "0"))
        if length > 1024 * 1024:
            self._json(413, {"error": "body too large"})
            return
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
        except json.JSONDecodeError:
            self._json(400, {"error": "invalid JSON"})
            return
        result = handle_chat(str(payload.get("message", "")))
        self._json(200, result)


def main() -> None:
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(
        f"[spawn-chat-ui] listening on :{PORT} "
        f"(framework={FRAMEWORK}, agent=:{AGENT_PORT}, mode={MODE})",
        flush=True,
    )
    server.serve_forever()


if __name__ == "__main__":
    main()
