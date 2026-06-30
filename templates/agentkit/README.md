# Coinbase AgentKit Template

A Python agent using [Coinbase AgentKit](https://github.com/coinbase/agentkit) for onchain operations with 1Claw key management.

## Quick start

```bash
1claw spawn agentkit
```

Or with your own API key:

```bash
1claw spawn agentkit --llm-api-key sk-...
```

## What's included

- **agent.py** — AgentKit-powered LangGraph agent with onchain tools
- **Flask server** on port 3000 with `/chat` and `/health` endpoints
- **Shroud integration** — LLM calls are routed through Shroud for inspection
- **MCP server** — started automatically for tool access to 1Claw vault

## Customizing

Edit `agent.py` to configure AgentKit actions (deploy tokens, transfer,
check balances, etc.). Set CDP API credentials via the 1Claw vault for
Coinbase Developer Platform integration.

## LLM authentication

The template supports three methods (configured at spawn time):

1. **BYOK** — `1claw spawn agentkit --llm-api-key sk-...`
2. **Token Billing** — enable in Dashboard, no key needed
3. **Anthropic WIF** — OIDC federation for Anthropic models
