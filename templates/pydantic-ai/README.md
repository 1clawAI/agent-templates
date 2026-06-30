# Pydantic AI Template

A Python agent using [Pydantic AI](https://ai.pydantic.dev) for type-safe, structured agent interactions with 1Claw MCP.

## Quick start

```bash
1claw spawn pydantic-ai
```

Or with your own API key:

```bash
1claw spawn pydantic-ai --llm-api-key sk-...
```

## What's included

- **agent.py** — Pydantic AI agent with typed tools and dependency injection
- **Flask server** on port 3000 with `/chat` and `/health` endpoints
- **Shroud integration** — LLM calls are routed through Shroud for inspection
- **MCP server** — started automatically for tool access to 1Claw vault

## Customizing

Edit `agent.py` to define typed result models, add tools with
`RunContext` dependency injection, or use structured output validation.
Pydantic AI enforces type safety on tool inputs/outputs and agent results.

## LLM authentication

The template supports three methods (configured at spawn time):

1. **BYOK** — `1claw spawn pydantic-ai --llm-api-key sk-...`
2. **Token Billing** — enable in Dashboard, no key needed
3. **Anthropic WIF** — OIDC federation for Anthropic models
