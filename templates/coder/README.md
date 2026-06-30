# Coder Template

A Python agent for automating [Coder](https://coder.com) workspace management with 1Claw MCP for secrets.

## Quick start

```bash
1claw spawn coder
```

Or with your own API key:

```bash
1claw spawn coder --llm-api-key sk-...
```

## What's included

- **agent.py** — Coder workspace automation agent with workspace listing
- **Flask server** on port 3000 with `/chat` and `/health` endpoints
- **Shroud integration** — LLM calls are routed through Shroud for inspection
- **MCP server** — started automatically for tool access to 1Claw vault

## Customizing

Edit `agent.py` to add Coder API actions: create workspaces, start/stop
builds, manage templates, or automate dev environments. Store
`CODER_URL` and `CODER_SESSION_TOKEN` in your 1Claw vault.

## LLM authentication

The template supports three methods (configured at spawn time):

1. **BYOK** — `1claw spawn coder --llm-api-key sk-...`
2. **Token Billing** — enable in Dashboard, no key needed
3. **Anthropic WIF** — OIDC federation for Anthropic models
