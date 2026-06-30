"""
Coder workspace automation agent pre-wired with 1Claw MCP for secrets.

Manages Coder workspaces via the Coder API. LLM calls are routed through
Shroud when ONECLAW_LLM_VIA_SHROUD is set. The container never sees raw
API keys — they are injected by the host daemon.
"""

import os
import asyncio
import httpx
from flask import Flask, request, jsonify
from agents import Agent, Runner, function_tool

app = Flask(__name__)

SHROUD_URL = os.environ.get("ONECLAW_SHROUD_URL", "https://shroud.1claw.xyz")
LLM_VIA_SHROUD = os.environ.get("ONECLAW_LLM_VIA_SHROUD", "").lower() == "true"
MODEL = os.environ.get("ONECLAW_SHROUD_MODEL", "gpt-4o-mini")
CODER_URL = os.environ.get("CODER_URL", "")
CODER_TOKEN = os.environ.get("CODER_SESSION_TOKEN", "")


@function_tool
def list_workspaces() -> str:
    """List all Coder workspaces accessible to the agent."""
    if not CODER_URL or not CODER_TOKEN:
        return "CODER_URL and CODER_SESSION_TOKEN not configured. Set them via 1Claw vault."
    try:
        r = httpx.get(
            f"{CODER_URL}/api/v2/workspaces",
            headers={"Coder-Session-Token": CODER_TOKEN},
            timeout=10,
        )
        r.raise_for_status()
        workspaces = r.json().get("workspaces", [])
        if not workspaces:
            return "No workspaces found."
        return "\n".join(
            f"  {w['name']} ({w.get('latest_build', {}).get('status', 'unknown')})"
            for w in workspaces
        )
    except Exception as e:
        return f"Error listing workspaces: {e}"


@function_tool
def list_env_vars() -> str:
    """List 1Claw-related environment variables (values redacted)."""
    prefix = "ONECLAW_"
    vars_list = [k for k in sorted(os.environ) if k.startswith(prefix)]
    return "\n".join(f"  {k}=***" for k in vars_list) if vars_list else "No ONECLAW_* vars set."


def create_agent() -> Agent | None:
    """Build the Coder automation agent. Returns None if no LLM."""
    if not LLM_VIA_SHROUD:
        return None

    os.environ["OPENAI_BASE_URL"] = f"{SHROUD_URL}/v1"
    os.environ["OPENAI_API_KEY"] = "shroud-injected"

    return Agent(
        name="1Claw Coder Agent",
        instructions=(
            "You are a workspace automation agent running inside 1Claw. "
            "You can list and manage Coder workspaces. Coder credentials "
            "are injected via the 1Claw daemon — never ask the user for tokens."
        ),
        tools=[list_workspaces, list_env_vars],
        model=MODEL,
    )


agent = create_agent()


@app.route("/health")
def health():
    return jsonify({"status": "ok", "framework": "coder", "llm_wired": LLM_VIA_SHROUD})


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"error": "No message provided"}), 400

    if not agent:
        return jsonify({
            "response": "No LLM configured. Use --llm-api-key or enable Token Billing.",
            "framework": "coder",
        })

    try:
        result = asyncio.run(Runner.run(agent, message))
        return jsonify({"response": result.final_output, "framework": "coder"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/")
def index():
    return """<!DOCTYPE html>
<html><head><title>1Claw Coder Agent</title></head>
<body style="font-family:system-ui;max-width:600px;margin:40px auto;padding:0 20px">
<h1>1Claw Coder Workspace Agent</h1>
<p>Send messages via <code>POST /chat</code> with <code>{"message": "..."}</code></p>
<p>Health: <a href="/health">/health</a></p>
<p style="color:#666;font-size:0.9em">
Credentials stay in the host daemon — this container never sees secret values.
</p></body></html>"""


if __name__ == "__main__":
    port = int(os.environ.get("CHAT_UI_PORT", "3000"))
    print(f"Coder agent listening on http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port)
