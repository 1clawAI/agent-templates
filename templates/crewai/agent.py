"""
CrewAI multi-agent crew pre-wired with 1Claw MCP for secrets and signing.

LLM calls are routed through Shroud when ONECLAW_LLM_VIA_SHROUD is set.
The container never sees raw API keys — they are injected by the host daemon.
"""

import os
from flask import Flask, request, jsonify
from crewai import Agent, Task, Crew, LLM

app = Flask(__name__)

SHROUD_URL = os.environ.get("ONECLAW_SHROUD_URL", "https://shroud.1claw.xyz")
LLM_VIA_SHROUD = os.environ.get("ONECLAW_LLM_VIA_SHROUD", "").lower() == "true"
PROVIDER = os.environ.get("ONECLAW_SHROUD_PROVIDER", "openai")
MODEL = os.environ.get("ONECLAW_SHROUD_MODEL", "gpt-4o-mini")


def create_crew() -> Crew | None:
    """Build a CrewAI crew. Returns None if no LLM is configured."""
    if not LLM_VIA_SHROUD:
        return None

    llm = LLM(
        model=f"{PROVIDER}/{MODEL}",
        base_url=f"{SHROUD_URL}/v1",
        api_key="shroud-injected",
    )

    researcher = Agent(
        role="Researcher",
        goal="Find accurate and relevant information",
        backstory="You are a skilled researcher who excels at finding and synthesizing information.",
        llm=llm,
        verbose=False,
    )

    writer = Agent(
        role="Writer",
        goal="Create clear, concise, and engaging content",
        backstory="You are a talented writer who turns research into readable content.",
        llm=llm,
        verbose=False,
    )

    return Crew(agents=[researcher, writer], verbose=False), researcher, writer


crew_result = create_crew()
crew = crew_result[0] if crew_result else None
researcher = crew_result[1] if crew_result else None
writer = crew_result[2] if crew_result else None


@app.route("/health")
def health():
    return jsonify({"status": "ok", "framework": "crewai", "llm_wired": LLM_VIA_SHROUD})


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"error": "No message provided"}), 400

    if not crew:
        return jsonify({
            "response": "No LLM configured. Use --llm-api-key or enable Token Billing.",
            "framework": "crewai",
        })

    try:
        research_task = Task(
            description=f"Research the following topic: {message}",
            expected_output="A concise summary of key findings.",
            agent=researcher,
        )

        write_task = Task(
            description="Write a clear response based on the research findings.",
            expected_output="A well-written, informative response.",
            agent=writer,
        )

        result = crew.kickoff(tasks=[research_task, write_task])
        return jsonify({"response": str(result), "framework": "crewai"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/")
def index():
    return """<!DOCTYPE html>
<html><head><title>1Claw CrewAI Agent</title></head>
<body style="font-family:system-ui;max-width:600px;margin:40px auto;padding:0 20px">
<h1>1Claw CrewAI Agent</h1>
<p>Send messages via <code>POST /chat</code> with <code>{"message": "..."}</code></p>
<p>Health: <a href="/health">/health</a></p>
<p style="color:#666;font-size:0.9em">
Credentials stay in the host daemon — this container never sees secret values.
</p></body></html>"""


if __name__ == "__main__":
    port = int(os.environ.get("CHAT_UI_PORT", "3000"))
    print(f"CrewAI agent listening on http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port)
