"""
1Claw Agent Memory adapter for LangChain.

Provides a BaseMemory implementation backed by the 1Claw Agent Memory sidecar,
enabling durable and scratch-tier conversation history for LangChain agents.

Usage:
    from oneclaw_langchain import OneclawMemory
    from langchain.chains import ConversationChain
    from langchain_openai import ChatOpenAI

    memory = OneclawMemory(namespace="conversations")
    chain = ConversationChain(llm=ChatOpenAI(), memory=memory)
    chain.invoke({"input": "Hello!"})
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

import requests
from langchain.memory.base import BaseMemory
from pydantic import Field


class OneclawMemory(BaseMemory):
    """LangChain memory backed by 1Claw Agent Memory via sidecar."""

    namespace: str = Field(default="conversations")
    sidecar_url: str = Field(default="http://localhost:8080")
    tier: str = Field(default="durable")
    memory_key: str = Field(default="history")
    human_prefix: str = Field(default="Human")
    ai_prefix: str = Field(default="AI")
    session_key: str = Field(default="default")
    ttl_seconds: int | None = Field(default=None)

    @property
    def memory_variables(self) -> List[str]:
        return [self.memory_key]

    def _api_url(self, *parts: str) -> str:
        path = "/".join(parts)
        return f"{self.sidecar_url}/memory/{self.namespace}/{path}"

    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, str]:
        """Fetch conversation history from durable memory."""
        try:
            resp = requests.get(
                self._api_url(self.session_key),
                params={"tier": self.tier},
                timeout=5,
            )
            if resp.status_code == 404:
                return {self.memory_key: ""}
            resp.raise_for_status()
            data = resp.json()
            value = data.get("value", "")
            if isinstance(value, str):
                return {self.memory_key: value}
            return {self.memory_key: json.dumps(value)}
        except requests.RequestException:
            return {self.memory_key: ""}

    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, str]) -> None:
        """Save the latest exchange to durable memory."""
        existing = self.load_memory_variables(inputs).get(self.memory_key, "")

        human_input = inputs.get("input", inputs.get("human_input", ""))
        ai_output = outputs.get("output", outputs.get("response", ""))

        new_entry = f"{self.human_prefix}: {human_input}\n{self.ai_prefix}: {ai_output}"
        updated = f"{existing}\n{new_entry}".strip() if existing else new_entry

        body: Dict[str, Any] = {"value": updated, "tier": self.tier}
        if self.ttl_seconds is not None:
            body["ttl_seconds"] = self.ttl_seconds

        requests.put(
            self._api_url(self.session_key),
            json=body,
            timeout=5,
        )

    def clear(self) -> None:
        """Delete the session entry from memory."""
        try:
            requests.delete(self._api_url(self.session_key), timeout=5)
        except requests.RequestException:
            pass


class OneclawScratchMemory(OneclawMemory):
    """Short-lived ephemeral memory using the scratch tier (auto-expires)."""

    tier: str = Field(default="scratch")
    ttl_seconds: int | None = Field(default=3600)
