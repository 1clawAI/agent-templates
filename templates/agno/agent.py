"""
Agno multi-modal agent pre-wired with 1Claw MCP for secrets and signing.

LLM calls are routed through Shroud when ONECLAW_LLM_VIA_SHROUD is set.
The container never sees raw API keys — they are injected by the host daemon.
"""

import os
from flask import Flask, request, jsonify
from agno.agent import Agent
from agno.models.openai import OpenAILike

app = Flask(__name__)

SHROUD_URL = os.environ.get("ONECLAW_SHROUD_URL", "https://shroud.1claw.xyz")
LLM_VIA_SHROUD = os.environ.get("ONECLAW_LLM_VIA_SHROUD", "").lower() == "true"
MODEL = os.environ.get("ONECLAW_SHROUD_MODEL", "gpt-4o-mini")


def create_agent() -> Agent | None:
    """Build the Agno agent. Returns None if no LLM."""
    if not LLM_VIA_SHROUD:
        return None

    model = OpenAILike(
        id=MODEL,
        api_key="shroud-injected",
        base_url=f"{SHROUD_URL}/v1",
    )

    return Agent(
        model=model,
        description="A helpful AI agent running inside a secure 1Claw container.",
        instructions=[
            "You have access to tools for greeting and inspecting the environment.",
        ],
        markdown=True,
    )


agent = create_agent()


@app.route("/health")
def health():
    return jsonify({"status": "ok", "framework": "agno", "llm_wired": LLM_VIA_SHROUD})


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"error": "No message provided"}), 400

    if not agent:
        return jsonify({
            "response": "No LLM configured. Use --llm-api-key or enable Token Billing.",
            "framework": "agno",
        })

    try:
        response = agent.run(message)
        output = response.content if hasattr(response, "content") else str(response)
        return jsonify({"response": output, "framework": "agno"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/")
def index():
    return """<!DOCTYPE html>
<html><head><title>1Claw Agno Agent</title></head>
<body style="font-family:system-ui;max-width:600px;margin:40px auto;padding:0 20px">
<h1>1Claw Agno Agent</h1>
<p>Send messages via <code>POST /chat</code> with <code>{"message": "..."}</code></p>
<p>Health: <a href="/health">/health</a></p>
<p style="color:#666;font-size:0.9em">
Credentials stay in the host daemon — this container never sees secret values.
</p></body></html>"""


if __name__ == "__main__":
    port = int(os.environ.get("CHAT_UI_PORT", "3000"))
    print(f"Agno agent listening on http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port)
