# LlamaIndex Template

A Python agent using [LlamaIndex](https://docs.llamaindex.ai) with 1Claw MCP for secrets management and on-chain signing.

## Quick start

```bash
1claw spawn llamaindex
```

Or with your own API key:

```bash
1claw spawn llamaindex --llm-api-key sk-...
```

## What's included

- **agent.py** — LlamaIndex ReActAgent with example tools (hello_world, list_env_vars)
- **Flask server** on port 3000 with `/chat` and `/health` endpoints
- **Shroud integration** — LLM calls are routed through Shroud for inspection
- **MCP server** — started automatically for tool access to 1Claw vault

## Customizing

Edit `agent.py` to add custom tools, connect data sources (documents,
APIs, databases), or switch to a different agent type. LlamaIndex
supports RAG, structured output, and multi-step reasoning.

## LLM authentication

The template supports three methods (configured at spawn time):

1. **BYOK** — `1claw spawn llamaindex --llm-api-key sk-...`
2. **Token Billing** — enable in Dashboard, no key needed
3. **Anthropic WIF** — OIDC federation for Anthropic models
