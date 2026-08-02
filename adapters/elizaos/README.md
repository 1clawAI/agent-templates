# 1Claw ElizaOS Memory Adapter

ElizaOS `MemoryAdapter` implementation backed by [1Claw Agent Memory](https://docs.1claw.xyz/docs/guides/agent-memory).

## Installation

```bash
npm install @elizaos/core
```

Copy `adapter.ts` into your project or reference from the templates package.

## Usage

```typescript
import { OneclawMemoryAdapter, OneclawScratchAdapter, OneclawSemanticAdapter } from "./adapter";

// Durable memory (persists across sessions)
const memory = new OneclawMemoryAdapter({
  namespace: "eliza-agent",
  sidecarUrl: "http://localhost:8080",
  tier: "durable",
});

// Store and retrieve
await memory.set("user-context", { name: "Alice", preferences: ["dark-mode"] });
const ctx = await memory.get("user-context");
// { name: "Alice", preferences: ["dark-mode"] }

// Scratch memory (auto-expires)
const scratch = new OneclawScratchAdapter({
  namespace: "temp-work",
  ttlSeconds: 1800, // 30 minutes
});

// Semantic search
const semantic = new OneclawSemanticAdapter({ namespace: "knowledge" });
await semantic.set("fact-1", "1Claw uses AES-256-GCM envelope encryption");
const results = await semantic.search("encryption method", 5);

// List and clear
const keys = await memory.list();
await memory.clear();
```

## Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `namespace` | `"elizaos"` | Memory namespace for grouping entries |
| `sidecarUrl` | `"http://localhost:8080"` | 1Claw sidecar API base URL |
| `tier` | `"durable"` | Memory tier: `scratch`, `durable`, or `semantic` |
| `ttlSeconds` | `undefined` | TTL for scratch tier entries (seconds) |

## Adapter Variants

| Class | Tier | Use Case |
|-------|------|----------|
| `OneclawMemoryAdapter` | configurable | General-purpose memory |
| `OneclawScratchAdapter` | scratch | Ephemeral working memory |
| `OneclawSemanticAdapter` | semantic | Vector-indexed search |

## Testing

```bash
npx vitest run adapter.test.ts
```
