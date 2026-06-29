# 1Claw Mastra Agent Template

TypeScript-first AI agent using [Mastra](https://mastra.ai) + Vercel AI SDK with 1Claw secrets and signing.

## Quick start

```bash
1claw spawn mastra --agent-key ocv_YOUR_KEY
```

## What's included

- `agent.ts` — Mastra agent with AI SDK tool calling, Shroud LLM routing, and `/chat` + `/health` endpoints
- `Dockerfile` — Node 22 slim image with `@1claw/mcp` for vault access
- `entrypoint.sh` — Daemon socket detection, Shroud wiring, MCP server startup

## LLM authentication

The container never sees your LLM API key. Credentials are injected by the host daemon and routed through Shroud.

```bash
# Bring your own key (stored in vault, routed through Shroud)
1claw spawn mastra --agent-key ocv_YOUR_KEY --llm-api-key sk-...

# Use 1Claw Token Billing (no provider key needed)
1claw spawn mastra --agent-key ocv_YOUR_KEY
```

## Customization

Edit `agent.ts` to add tools, change the system prompt, or integrate with Mastra workflows.
