# Agno Template

A Python agent using [Agno](https://docs.agno.com) — a multi-modal agent framework — with 1Claw MCP for secrets management.

## Quick start

```bash
1claw spawn agno
```

Or with your own API key:

```bash
1claw spawn agno --llm-api-key sk-...
```

## What's included

- **agent.py** — Agno agent with OpenAI-compatible model routing
- **Flask server** on port 3000 with `/chat` and `/health` endpoints
- **Shroud integration** — LLM calls are routed through Shroud for inspection
- **MCP server** — started automatically for tool access to 1Claw vault

## Customizing

Edit `agent.py` to add tools, configure knowledge bases, or enable
multi-modal capabilities (vision, audio). Agno supports teams of agents,
structured output, and memory.

## LLM authentication

The template supports three methods (configured at spawn time):

1. **BYOK** — `1claw spawn agno --llm-api-key sk-...`
2. **Token Billing** — enable in Dashboard, no key needed
3. **Anthropic WIF** — OIDC federation for Anthropic models
