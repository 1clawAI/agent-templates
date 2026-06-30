# HuggingFace smolagents Template

A Python agent using [smolagents](https://huggingface.co/docs/smolagents) — HuggingFace's lightweight agent framework — with 1Claw MCP for secrets management.

## Quick start

```bash
1claw spawn smolagents
```

Or with your own API key:

```bash
1claw spawn smolagents --llm-api-key sk-...
```

## What's included

- **agent.py** — CodeAgent with example tools (hello_world, list_env_vars)
- **Flask server** on port 3000 with `/chat` and `/health` endpoints
- **Shroud integration** — LLM calls are routed through Shroud for inspection
- **MCP server** — started automatically for tool access to 1Claw vault

## Customizing

Edit `agent.py` to add custom tools, switch to `ToolCallingAgent`, or
use HuggingFace Hub models directly. smolagents supports both code-based
and tool-calling agent patterns.

## LLM authentication

The template supports three methods (configured at spawn time):

1. **BYOK** — `1claw spawn smolagents --llm-api-key sk-...`
2. **Token Billing** — enable in Dashboard, no key needed
3. **Anthropic WIF** — OIDC federation for Anthropic models
