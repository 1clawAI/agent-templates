# 1Claw Agent Templates

Public template registry for [`1claw spawn`](https://docs.1claw.xyz/docs/guides/cli#agent-templates-spawn) — framework-specific Docker agents pre-wired with 1Claw MCP and Shroud.

Each template includes a **Dockerfile**, starter agent code, and an **entrypoint** that mounts the host daemon socket. The container **never sees raw API keys**; credentials are injected at runtime by the 1Claw daemon on the host.

**Full contributor guide (docs):** [docs.1claw.xyz — Add an agent template](https://docs.1claw.xyz/docs/guides/agent-templates)

---

## Use a template

Install the CLI, then spawn:

```bash
npm install -g @1claw/cli   # or: brew install 1clawAI/tap/oneclaw

1claw spawn langchain --agent-key ocv_YOUR_KEY
1claw spawn --list
1claw spawn --refresh     # pull latest templates from this repo
```

See the [CLI guide](https://docs.1claw.xyz/docs/guides/cli#agent-templates-spawn) for LLM options (BYOK, Token Billing, offline mode).

### Shipped templates

**Python:**

| Template | Framework | Status |
|----------|-----------|--------|
| `langchain` | LangChain / LangGraph | ✅ |
| `crewai` | CrewAI | ✅ |
| `openai-agents` | OpenAI Agents SDK | ✅ |
| `agentkit` | Coinbase AgentKit | ✅ |
| `smolagents` | HuggingFace smolagents | ✅ |
| `llamaindex` | LlamaIndex | ✅ |
| `pydantic-ai` | Pydantic AI | ✅ |
| `agno` | Agno | ✅ |
| `coder` | Coder | ✅ |

**TypeScript:**

| Template | Framework | Status |
|----------|-----------|--------|
| `typescript-sdk` | @1claw/sdk + AI SDK | ✅ |
| `mastra` | Mastra | ✅ |
| `elizaos` | ElizaOS | ✅ |

---

## Contribute a template

We welcome community PRs for new frameworks and improvements to existing templates.

### Before you start

- Pick a **unique directory name** (lowercase, hyphens): e.g. `pydantic-ai`, `my-framework`.
- Copy an existing template as a starting point:
  - **Python:** `templates/langchain/`
  - **TypeScript:** `templates/typescript-sdk/` or `templates/mastra/`
- Read the [docs contributor guide](https://docs.1claw.xyz/docs/guides/agent-templates) for the full walkthrough.

### Step-by-step

1. **Fork** [1clawAI/agent-templates](https://github.com/1clawAI/agent-templates) and clone your fork.

2. **Create** `templates/<name>/` with these files:

   | File | Required |
   |------|----------|
   | `template.yaml` | Manifest (`name` must match directory) |
   | `Dockerfile` | Builds a runnable image |
   | `entrypoint.sh` | Starts MCP + agent; wires Shroud when enabled |
   | Starter code | e.g. `agent.py` or `agent.ts` |
   | `README.md` | Framework-specific notes |
   | `requirements.txt` | Python deps (Python templates) |
   | `package.json` | Node deps (TypeScript templates) |

3. **Register** the template in [`registry.yaml`](./registry.yaml):

   ```yaml
   - name: my-framework          # must match templates/my-framework/
     display_name: "My Framework"
     version: 1.0.0
     language: python             # python | node
     description: "One-line summary for 1claw spawn --list"
   ```

4. **Test locally:**

   ```bash
   cd templates/my-framework
   docker build -t test-my-framework .
   docker run --rm -p 3000:3000 test-my-framework
   curl http://localhost:3000/health
   ```

   Optionally test end-to-end with the CLI (from a monorepo checkout with this repo at `packages/agent-templates`):

   ```bash
   1claw spawn my-framework --agent-key ocv_YOUR_KEY
   ```

5. **Open a pull request** against `main`. CI will:
   - Validate `template.yaml` (required fields, name match, language)
   - Confirm the template is listed in `registry.yaml`
   - Scan for accidental secrets (`sk-…`, `ocv_…`, etc.)
   - Run `docker build` smoke tests (see [validate.yml](./.github/workflows/validate.yml))

6. **After merge**, templates appear for everyone via `1claw spawn --refresh` (or on the next CLI release that bundles this repo).

### Rules (must follow)

- **No secrets in the repo.** Never commit API keys, agent keys, or real vault IDs.
- **Daemon socket, not env secrets.** Templates must work with `ONECLAW_DAEMON_SOCKET=/run/1claw/daemon.sock`; do not `ENV` or `COPY` credentials.
- **Health endpoint.** Expose `/health` (or declare another path in `template.yaml`) on port `3000` by default.
- **LLM via Shroud.** Route provider calls through Shroud when `ONECLAW_LLM_VIA_SHROUD=true` (see `entrypoint.sh` in existing templates).

### Deep reference

- **[CONTRIBUTING.md](./CONTRIBUTING.md)** — manifest schema, Dockerfile guidelines, entrypoint pattern
- **[Docs: Add an agent template](https://docs.1claw.xyz/docs/guides/agent-templates)** — step-by-step guide with examples
- **[CLI spawn docs](https://docs.1claw.xyz/docs/guides/cli#agent-templates-spawn)** — user-facing `1claw spawn` reference

### Questions?

Open a [GitHub Discussion](https://github.com/1clawAI/agent-templates/discussions) or issue. For security concerns, email ops@1claw.xyz.

---

## Repository layout

```
agent-templates/
├── registry.yaml           # Index consumed by 1claw spawn --list
├── templates/
│   ├── langchain/          # One directory per framework
│   │   ├── template.yaml
│   │   ├── Dockerfile
│   │   ├── entrypoint.sh
│   │   └── ...
│   └── ...
├── CONTRIBUTING.md         # Technical schema & patterns
└── .github/workflows/      # CI validation
```

## License

MIT — see [LICENSE](./LICENSE).
