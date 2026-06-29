# Contributing a Template

Thanks for contributing to 1Claw agent templates! This guide explains how to
add a new framework integration.

## Quick start

1. Fork this repo.
2. Create a directory under `templates/<your-framework>/`.
3. Add the required files (see below).
4. Open a pull request — CI validates the manifest and runs a Docker build smoke test.

## Required files

Every template directory must contain:

| File | Purpose |
|------|---------|
| `template.yaml` | Manifest describing the template (see schema below) |
| `Dockerfile` | Docker image definition; must accept the daemon socket mount |
| `entrypoint.sh` | Container entrypoint; should start the MCP server + your agent |
| Starter code | e.g. `agent.py`, `agent.ts`, `main.py` — a working hello-world agent |
| `README.md` | Framework-specific setup notes |

For Python templates, include a `requirements.txt`. For Node templates, include
a `package.json`.

## Template manifest schema (`template.yaml`)

```yaml
name: my-framework            # Must match directory name
display_name: "My Framework"  # Human-readable name
version: 1.0.0
description: "One-line description of what this template does"
author: Your Name
language: python               # python | node
homepage: https://example.com  # Framework homepage

docker:
  base_image: python:3.12-slim
  context_files:
    - Dockerfile
    - requirements.txt
    - agent.py
    - entrypoint.sh
  env:
    ONECLAW_FRAMEWORK: my-framework
  health_endpoint: /health
  health_port: 3000

post_spawn_message: |
  Edit agent.py to customize your agent.
  Your 1Claw MCP server is available at the daemon socket.
```

### Required fields

- `name` — must match the directory name exactly
- `display_name` — shown in `1claw spawn --list`
- `version` — semver
- `description` — one line, shown in the template catalog
- `author` — your name or org
- `language` — `python` or `node`
- `docker.base_image` — the base Docker image
- `docker.context_files` — files copied into the build context

### Optional fields

- `homepage` — link to the framework docs
- `docker.env` — default env vars baked into the image
- `docker.health_endpoint` — health check path (default: `/health`)
- `docker.health_port` — health check port (default: `3000`)
- `post_spawn_message` — printed after a successful `1claw spawn`

## Dockerfile guidelines

Your Dockerfile should:

1. **Accept a daemon socket mount.** The 1Claw daemon injects credentials via a
   Unix socket at `/run/1claw/daemon.sock`. Your entrypoint should check for it.

2. **Never bake secrets into the image.** API keys and credentials are injected
   at runtime by the daemon.

3. **Expose port 3000** (or whatever `health_port` you declare) for the health
   check.

4. **Install the 1Claw MCP server** if your agent needs tool access:
   ```dockerfile
   RUN pip install 1claw-mcp || npm install -g @1claw/mcp@latest
   ```

5. **Use `tini` as the init process** for proper signal handling:
   ```dockerfile
   RUN apt-get update && apt-get install -y tini
   ENTRYPOINT ["tini", "--"]
   ```

## Entrypoint pattern

Use this shared pattern for LLM routing through Shroud:

```bash
#!/bin/sh
set -e

DAEMON_SOCKET="${ONECLAW_DAEMON_SOCKET:-/run/1claw/daemon.sock}"

if [ -S "$DAEMON_SOCKET" ]; then
    echo "1Claw daemon socket detected at $DAEMON_SOCKET"
else
    echo "WARNING: No daemon socket at $DAEMON_SOCKET"
fi

# Route LLM calls through Shroud (transparent to application code)
if [ "$ONECLAW_LLM_VIA_SHROUD" = "true" ]; then
    export OPENAI_BASE_URL="${ONECLAW_SHROUD_URL}/v1"
fi

# Start MCP server in background (best-effort)
if command -v 1claw-mcp >/dev/null 2>&1; then
    ONECLAW_LOCAL_VAULT=true ONECLAW_DAEMON_SOCKET="$DAEMON_SOCKET" \
        1claw-mcp --local 2>/tmp/mcp.log &
fi

# Start your agent
exec python agent.py  # or node agent.ts, etc.
```

## Testing your template

Before submitting:

```bash
# Build the image
docker build -t test-template templates/my-framework/

# Run with a mock daemon socket
docker run --rm -p 3000:3000 test-template

# Verify health
curl http://localhost:3000/health
```

## CI validation

The CI workflow checks:

1. `template.yaml` matches the schema (required fields, valid language)
2. `docker build` succeeds for each template
3. No secrets or credentials in template files
4. Template `name` matches the directory name
5. The template is listed in `registry.yaml`

## Code of conduct

Be respectful and constructive. We welcome contributions from everyone.
