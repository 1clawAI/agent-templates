"""
LangChain agent pre-wired with 1Claw MCP for secrets and signing.

LLM calls are routed through Shroud when ONECLAW_LLM_VIA_SHROUD is set.
The container never sees raw API keys — they are injected by the host daemon.
"""

import os
import threading
from flask import Flask, request, jsonify
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool

app = Flask(__name__)

SHROUD_URL = os.environ.get("ONECLAW_SHROUD_URL", "https://shroud.1claw.xyz")
LLM_VIA_SHROUD = os.environ.get("ONECLAW_LLM_VIA_SHROUD", "").lower() == "true"
PROVIDER = os.environ.get("ONECLAW_SHROUD_PROVIDER", "openai")
MODEL = os.environ.get("ONECLAW_SHROUD_MODEL", "gpt-4o-mini")

conversation_history: list[dict] = []


@tool
def hello_world(name: str) -> str:
    """Say hello to someone."""
    return f"Hello, {name}! I'm a LangChain agent running inside 1Claw."


@tool
def list_env_vars() -> str:
    """List 1Claw-related environment variables (values redacted)."""
    prefix = "ONECLAW_"
    vars_list = [k for k in sorted(os.environ) if k.startswith(prefix)]
    return "\n".join(f"  {k}=***" for k in vars_list) if vars_list else "No ONECLAW_* vars set."


def create_agent() -> AgentExecutor | None:
    """Build the LangChain agent. Returns None if no LLM is configured."""
    if not LLM_VIA_SHROUD:
        return None

    llm = ChatOpenAI(
        model=MODEL,
        base_url=f"{SHROUD_URL}/v1",
        api_key="shroud-injected",
    )

    tools = [hello_world, list_env_vars]

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful AI agent running inside a secure 1Claw container. "
                   "You have access to tools for greeting and inspecting the environment."),
        ("placeholder", "{chat_history}"),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=False)


agent_executor = create_agent()


@app.route("/health")
def health():
    return jsonify({"status": "ok", "framework": "langchain", "llm_wired": LLM_VIA_SHROUD})


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"error": "No message provided"}), 400

    if not agent_executor:
        return jsonify({
            "response": "No LLM configured. Use --llm-api-key or enable Token Billing.",
            "framework": "langchain",
        })

    try:
        result = agent_executor.invoke({
            "input": message,
            "chat_history": conversation_history,
        })
        output = result.get("output", str(result))
        conversation_history.append({"role": "user", "content": message})
        conversation_history.append({"role": "assistant", "content": output})
        return jsonify({"response": output, "framework": "langchain"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/")
def index():
    return """<!DOCTYPE html>
<html><head><title>1Claw LangChain Agent</title></head>
<body style="font-family:system-ui;max-width:600px;margin:40px auto;padding:0 20px">
<h1>1Claw LangChain Agent</h1>
<p>Send messages via <code>POST /chat</code> with <code>{"message": "..."}</code></p>
<p>Health: <a href="/health">/health</a></p>
<p style="color:#666;font-size:0.9em">
Credentials stay in the host daemon — this container never sees secret values.
</p></body></html>"""


if __name__ == "__main__":
    port = int(os.environ.get("CHAT_UI_PORT", "3000"))
    print(f"LangChain agent listening on http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port)
