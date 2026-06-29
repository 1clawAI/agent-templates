# 1Claw Agent Templates

Framework-specific starter templates for [`1claw spawn`](https://docs.1claw.xyz/docs/guides/cli#agent-templates-spawn).

Each template ships a Dockerfile, starter agent code, and an entrypoint pre-wired with 1Claw MCP and Shroud LLM routing. The container never sees your API key — credentials are injected by the host daemon.

## Quick start

```bash
1claw spawn langchain --agent-key ocv_YOUR_KEY
1claw spawn --list
```

## Available templates

See [`registry.yaml`](./registry.yaml) for the full index.

| Template | Framework | Language |
|----------|-----------|----------|
| `langchain` | LangChain / LangGraph | Python |
| `crewai` | CrewAI | Python |
| `openai-agents` | OpenAI Agents SDK | Python |
| `typescript-sdk` | @1claw/sdk + Vercel AI SDK | TypeScript |
| `mastra` | Mastra | TypeScript |
| `elizaos` | ElizaOS | TypeScript |

## Contributing

We welcome community templates! See [CONTRIBUTING.md](./CONTRIBUTING.md) for the manifest schema, Dockerfile requirements, and CI validation rules.

## License

MIT — see [LICENSE](./LICENSE) if present, or the 1Claw CLI package.
