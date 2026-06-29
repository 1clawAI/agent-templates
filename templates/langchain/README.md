# LangChain / LangGraph Template

A Python agent using [LangChain](https://python.langchain.com) with 1Claw MCP
for secrets management and on-chain signing.

## Quick start

```bash
1claw spawn langchain
```

Or with your own API key:

```bash
1claw spawn langchain --llm-api-key sk-...
```

## What's included

- **agent.py** — Starter LangChain agent with tool calling (hello_world, list_env_vars)
- **Flask server** on port 3000 with `/chat` and `/health` endpoints
- **Shroud integration** — LLM calls are routed through Shroud for inspection
- **MCP server** — started automatically for tool access to 1Claw vault

## Customizing

Edit `agent.py` to add your own tools, change the prompt, or swap the LLM
provider. The agent uses `ChatOpenAI` pointed at Shroud, which handles
provider routing transparently.

## LLM authentication

The template supports three methods (configured at spawn time):

1. **BYOK** — `1claw spawn langchain --llm-api-key sk-...`
2. **Token Billing** — enable in Dashboard, no key needed
3. **Anthropic WIF** — OIDC federation for Anthropic models
