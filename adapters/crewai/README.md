# 1Claw CrewAI Storage Adapter

CrewAI storage backend backed by [1Claw Agent Memory](https://docs.1claw.xyz/docs/guides/agent-memory).

## Installation

```bash
pip install crewai requests
```

Copy `storage.py` into your project or install from the templates package.

## Usage

```python
from oneclaw_crewai import OneclawStorage, OneclawSemanticStorage
from crewai import Agent, Crew, Task

# Durable storage for crew state
storage = OneclawStorage(
    namespace="crew-research",
    sidecar_url="http://localhost:8080",
    tier="durable",
)

# Store and retrieve data
storage.save("last_run", {"status": "success", "findings": 42})
result = storage.load("last_run")  # {"status": "success", "findings": 42}

# Semantic search (requires semantic tier)
semantic = OneclawSemanticStorage(namespace="knowledge-base")
semantic.save("finding-1", "The API rate limit is 1000 requests per minute")
results = semantic.search("rate limiting", top_k=3)

# Use with CrewAI agents
agent = Agent(
    role="Data Analyst",
    memory=True,
    # Pass storage instance via your crew configuration
)
```

## Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `namespace` | `"crewai"` | Memory namespace for grouping entries |
| `sidecar_url` | `"http://localhost:8080"` | 1Claw sidecar API base URL |
| `tier` | `"durable"` | Memory tier: `scratch`, `durable`, or `semantic` |
| `ttl_seconds` | `None` | Optional TTL for scratch tier entries |

## API

| Method | Description |
|--------|-------------|
| `save(key, value)` | Store a value (auto-serializes dicts/lists) |
| `load(key)` | Load a value (auto-deserializes JSON) |
| `search(query, top_k)` | Semantic search (semantic tier only) |
| `delete(key)` | Delete a single entry |
| `list_keys()` | List all keys in the namespace |
| `clear()` | Delete all entries |

## Testing

```bash
pytest test_storage.py
```
