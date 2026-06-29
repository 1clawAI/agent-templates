# 1Claw ElizaOS Agent Template

[ElizaOS](https://elizaos.ai) character runtime with 1Claw vault-backed secrets and multi-chain signing via `@1claw/plugin-elizaos`.

## Quick start

```bash
1claw spawn elizaos --agent-key ocv_YOUR_KEY
```

## What's included

- `agent.ts` — ElizaOS agent with Shroud LLM routing and `/chat` + `/health` endpoints
- `Dockerfile` — Node 22 slim image with `@1claw/mcp` and `@1claw/plugin-elizaos`
- `entrypoint.sh` — Daemon socket detection, Shroud wiring, MCP server startup

## Plugin actions

The `@1claw/plugin-elizaos` plugin provides 8 actions:
- `GET_SECRET` / `PUT_SECRET` / `LIST_SECRETS` / `DELETE_SECRET`
- `SIGN_MESSAGE` / `SIGN_TYPED_DATA` / `SUBMIT_TRANSACTION`
- `LIST_SIGNING_KEYS`

## LLM authentication

```bash
# Bring your own key (stored in vault, routed through Shroud)
1claw spawn elizaos --agent-key ocv_YOUR_KEY --llm-api-key sk-...

# Use 1Claw Token Billing (no provider key needed)
1claw spawn elizaos --agent-key ocv_YOUR_KEY
```

## Customization

Edit `agent.ts` to define your character, add custom actions, or integrate with the full ElizaOS `AgentRuntime`.
