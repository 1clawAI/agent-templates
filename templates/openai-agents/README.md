# OpenAI Agents SDK Template

A Python agent using the [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/)
with 1Claw MCP for secrets management and on-chain signing.

## Quick start

```bash
1claw spawn openai-agents
```

Or with your own API key:

```bash
1claw spawn openai-agents --llm-api-key sk-...
```

## What's included

- **agent.py** — Starter agent with function tools (hello_world, list_env_vars)
- **Flask server** on port 3000 with `/chat` and `/health` endpoints
- **Shroud integration** — LLM calls are routed through Shroud for inspection
- **MCP server** — started automatically for tool access to 1Claw vault

## Customizing

Edit `agent.py` to add your own `@function_tool` tools, change the agent
instructions, or add handoffs between agents. The agent uses the OpenAI
Agents SDK with the base URL pointed at Shroud.
