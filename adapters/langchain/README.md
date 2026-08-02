# 1Claw LangChain Memory Adapter

LangChain `BaseMemory` implementation backed by [1Claw Agent Memory](https://docs.1claw.xyz/docs/guides/agent-memory).

## Installation

```bash
pip install langchain requests
```

Copy `memory.py` into your project or install from the templates package.

## Usage

```python
from oneclaw_langchain import OneclawMemory
from langchain.chains import ConversationChain
from langchain_openai import ChatOpenAI

# Durable memory (persists across sessions)
memory = OneclawMemory(
    namespace="conversations",
    sidecar_url="http://localhost:8080",
    tier="durable",
)

chain = ConversationChain(llm=ChatOpenAI(), memory=memory)
response = chain.invoke({"input": "What is 1Claw?"})

# Scratch memory (auto-expires after TTL)
from oneclaw_langchain import OneclawScratchMemory

scratch = OneclawScratchMemory(
    namespace="temp-work",
    ttl_seconds=1800,  # 30 minutes
)
```

## Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `namespace` | `"conversations"` | Memory namespace for grouping entries |
| `sidecar_url` | `"http://localhost:8080"` | 1Claw sidecar API base URL |
| `tier` | `"durable"` | Memory tier: `scratch`, `durable`, or `semantic` |
| `session_key` | `"default"` | Key within the namespace for this session |
| `ttl_seconds` | `None` | TTL for scratch tier entries (seconds) |
| `memory_key` | `"history"` | Key used in LangChain memory variables |

## How It Works

The adapter stores serialized conversation history as a single key in 1Claw's agent memory system. Each `save_context` call appends the latest exchange. The sidecar handles encryption, replication, and tier-based expiry.

## Testing

```bash
pytest test_memory.py
```
