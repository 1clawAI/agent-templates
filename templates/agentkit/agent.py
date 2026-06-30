"""
Coinbase AgentKit agent pre-wired with 1Claw MCP for secrets and signing.

LLM calls are routed through Shroud when ONECLAW_LLM_VIA_SHROUD is set.
The container never sees raw API keys — they are injected by the host daemon.
"""

import os
from flask import Flask, request, jsonify
from langchain_openai import ChatOpenAI
from coinbase_agentkit import AgentKit, AgentKitConfig
from coinbase_agentkit_langchain import get_langchain_tools
from langgraph.prebuilt import create_react_agent

app = Flask(__name__)

SHROUD_URL = os.environ.get("ONECLAW_SHROUD_URL", "https://shroud.1claw.xyz")
LLM_VIA_SHROUD = os.environ.get("ONECLAW_LLM_VIA_SHROUD", "").lower() == "true"
MODEL = os.environ.get("ONECLAW_SHROUD_MODEL", "gpt-4o-mini")


def create_agent():
    """Build an AgentKit-powered LangGraph agent. Returns None if no LLM."""
    if not LLM_VIA_SHROUD:
        return None

    llm = ChatOpenAI(
        model=MODEL,
        base_url=f"{SHROUD_URL}/v1",
        api_key="shroud-injected",
    )

    agentkit = AgentKit(AgentKitConfig())
    tools = get_langchain_tools(agentkit)
    return create_react_agent(llm, tools=tools)


agent_executor = create_agent()


@app.route("/health")
def health():
    return jsonify({"status": "ok", "framework": "agentkit", "llm_wired": LLM_VIA_SHROUD})


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"error": "No message provided"}), 400

    if not agent_executor:
        return jsonify({
            "response": "No LLM configured. Use --llm-api-key or enable Token Billing.",
            "framework": "agentkit",
        })

    try:
        result = agent_executor.invoke({"messages": [{"role": "user", "content": message}]})
        output = result["messages"][-1].content if result.get("messages") else str(result)
        return jsonify({"response": output, "framework": "agentkit"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/")
def index():
    return """<!DOCTYPE html>
<html><head><title>1Claw AgentKit Agent</title></head>
<body style="font-family:system-ui;max-width:600px;margin:40px auto;padding:0 20px">
<h1>1Claw Coinbase AgentKit</h1>
<p>Send messages via <code>POST /chat</code> with <code>{"message": "..."}</code></p>
<p>Health: <a href="/health">/health</a></p>
<p style="color:#666;font-size:0.9em">
Credentials stay in the host daemon — this container never sees secret values.
</p></body></html>"""


if __name__ == "__main__":
    port = int(os.environ.get("CHAT_UI_PORT", "3000"))
    print(f"AgentKit agent listening on http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port)
