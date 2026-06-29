# 1Claw TypeScript SDK Agent Template

Plain TypeScript agent using [@1claw/sdk](https://www.npmjs.com/package/@1claw/sdk) for vault access, multi-chain signing, and Vercel AI SDK for LLM interaction through Shroud.

## Quick start

```bash
1claw spawn typescript-sdk --agent-key ocv_YOUR_KEY
```

## What's included

- `agent.ts` — TypeScript agent with `@1claw/sdk` client, AI SDK tool calling, and `/chat` + `/health` endpoints
- `Dockerfile` — Node 22 slim image with `@1claw/mcp` for vault access
- `entrypoint.sh` — Daemon socket detection, Shroud wiring, MCP server startup

## LLM authentication

```bash
# Bring your own key (stored in vault, routed through Shroud)
1claw spawn typescript-sdk --agent-key ocv_YOUR_KEY --llm-api-key sk-...

# Use 1Claw Token Billing (no provider key needed)
1claw spawn typescript-sdk --agent-key ocv_YOUR_KEY
```

## Customization

Edit `agent.ts` to add tools, integrate with your own services, or use additional @1claw/sdk features like `signIntent()`, `submitTransaction()`, or `leaseBankrKey()`.
