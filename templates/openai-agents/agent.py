"""
OpenAI Agents SDK agent pre-wired with 1Claw MCP for secrets and signing.

LLM calls are routed through Shroud when ONECLAW_LLM_VIA_SHROUD is set.
The container never sees raw API keys — they are injected by the host daemon.
"""

import os
import asyncio
from flask import Flask, request, jsonify
from agents import Agent, Runner, function_tool, ModelSettings

app = Flask(__name__)

SHROUD_URL = os.environ.get("ONECLAW_SHROUD_URL", "https://shroud.1claw.xyz")
LLM_VIA_SHROUD = os.environ.get("ONECLAW_LLM_VIA_SHROUD", "").lower() == "true"
MODEL = os.environ.get("ONECLAW_SHROUD_MODEL", "gpt-4o-mini")


@function_tool
def hello_world(name: str) -> str:
    """Say hello to someone."""
    return f"Hello, {name}! I'm an OpenAI Agents SDK agent running inside 1Claw."


@function_tool
def list_env_vars() -> str:
    """List 1Claw-related environment variables (values redacted)."""
    prefix = "ONECLAW_"
    vars_list = [k for k in sorted(os.environ) if k.startswith(prefix)]
    return "\n".join(f"  {k}=***" for k in vars_list) if vars_list else "No ONECLAW_* vars set."


def create_agent() -> Agent | None:
    """Build the OpenAI agent. Returns None if no LLM is configured."""
    if not LLM_VIA_SHROUD:
        return None

    os.environ["OPENAI_BASE_URL"] = f"{SHROUD_URL}/v1"
    os.environ["OPENAI_API_KEY"] = "shroud-injected"

    return Agent(
        name="1Claw Agent",
        instructions=(
            "You are a helpful AI agent running inside a secure 1Claw container. "
            "You have access to tools for greeting and inspecting the environment."
        ),
        tools=[hello_world, list_env_vars],
        model=MODEL,
    )


agent = create_agent()


@app.route("/health")
def health():
    return jsonify({"status": "ok", "framework": "openai-agents", "llm_wired": LLM_VIA_SHROUD})


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"error": "No message provided"}), 400

    if not agent:
        return jsonify({
            "response": "No LLM configured. Use --llm-api-key or enable Token Billing.",
            "framework": "openai-agents",
        })

    try:
        result = asyncio.run(Runner.run(agent, message))
        output = result.final_output
        return jsonify({"response": output, "framework": "openai-agents"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/")
def index():
    return """<!DOCTYPE html>
<html><head><title>1Claw OpenAI Agent</title></head>
<body style="font-family:system-ui;max-width:600px;margin:40px auto;padding:0 20px">
<h1>1Claw OpenAI Agents SDK</h1>
<p>Send messages via <code>POST /chat</code> with <code>{"message": "..."}</code></p>
<p>Health: <a href="/health">/health</a></p>
<p style="color:#666;font-size:0.9em">
Credentials stay in the host daemon — this container never sees secret values.
</p></body></html>"""


if __name__ == "__main__":
    port = int(os.environ.get("CHAT_UI_PORT", "3000"))
    print(f"OpenAI Agents SDK agent listening on http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port)
