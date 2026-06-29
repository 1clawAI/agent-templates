# CrewAI Template

A multi-agent crew using [CrewAI](https://crewai.com) with 1Claw MCP for
secrets management and on-chain signing.

## Quick start

```bash
1claw spawn crewai
```

Or with your own API key:

```bash
1claw spawn crewai --llm-api-key sk-...
```

## What's included

- **agent.py** — Starter crew with Researcher and Writer agents
- **Flask server** on port 3000 with `/chat` and `/health` endpoints
- **Shroud integration** — LLM calls are routed through Shroud for inspection
- **MCP server** — started automatically for tool access to 1Claw vault

## Customizing

Edit `agent.py` to add your own agents, tools, and tasks. The crew uses
CrewAI's `LLM` class pointed at Shroud, which handles provider routing
transparently.
