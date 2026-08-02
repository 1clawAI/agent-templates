"""
1Claw Agent Memory adapter for CrewAI.

Provides a storage backend for CrewAI agents, enabling persistent
memory across crew runs via the 1Claw sidecar.

Usage:
    from oneclaw_crewai import OneclawStorage
    from crewai import Agent, Crew, Task

    storage = OneclawStorage(namespace="crew-research")
    agent = Agent(
        role="Researcher",
        memory=True,
        storage=storage,
    )
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import requests


class OneclawStorage:
    """CrewAI storage backed by 1Claw Agent Memory."""

    def __init__(
        self,
        namespace: str = "crewai",
        sidecar_url: str = "http://localhost:8080",
        tier: str = "durable",
        ttl_seconds: Optional[int] = None,
    ):
        self.namespace = namespace
        self.sidecar_url = sidecar_url
        self.tier = tier
        self.ttl_seconds = ttl_seconds

    def _url(self, key: str) -> str:
        return f"{self.sidecar_url}/memory/{self.namespace}/{key}"

    def save(self, key: str, value: Any) -> None:
        """Store a value in 1Claw memory."""
        body: Dict[str, Any] = {"tier": self.tier}
        if isinstance(value, (dict, list)):
            body["value"] = json.dumps(value)
        else:
            body["value"] = str(value)
        if self.ttl_seconds is not None:
            body["ttl_seconds"] = self.ttl_seconds

        resp = requests.put(self._url(key), json=body, timeout=5)
        resp.raise_for_status()

    def load(self, key: str) -> Optional[Any]:
        """Load a value from 1Claw memory. Returns None if not found."""
        try:
            resp = requests.get(
                self._url(key),
                params={"tier": self.tier},
                timeout=5,
            )
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            data = resp.json()
            value = data.get("value", "")
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        except requests.RequestException:
            return None

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Semantic search over stored memory (requires semantic tier)."""
        try:
            resp = requests.post(
                f"{self.sidecar_url}/memory/search",
                json={
                    "namespace": self.namespace,
                    "query": query,
                    "top_k": top_k,
                },
                timeout=10,
            )
            if resp.status_code == 404:
                return []
            resp.raise_for_status()
            return resp.json().get("results", [])
        except requests.RequestException:
            return []

    def delete(self, key: str) -> None:
        """Delete a key from memory."""
        try:
            requests.delete(self._url(key), timeout=5)
        except requests.RequestException:
            pass

    def list_keys(self) -> List[str]:
        """List all keys in the namespace."""
        try:
            resp = requests.get(
                f"{self.sidecar_url}/memory/{self.namespace}",
                timeout=5,
            )
            if resp.status_code == 404:
                return []
            resp.raise_for_status()
            entries = resp.json().get("entries", [])
            return [e.get("key", "") for e in entries]
        except requests.RequestException:
            return []

    def clear(self) -> None:
        """Delete all entries in this namespace."""
        for key in self.list_keys():
            self.delete(key)


class OneclawSemanticStorage(OneclawStorage):
    """CrewAI storage with semantic search capabilities."""

    def __init__(
        self,
        namespace: str = "crewai-semantic",
        sidecar_url: str = "http://localhost:8080",
    ):
        super().__init__(
            namespace=namespace,
            sidecar_url=sidecar_url,
            tier="semantic",
        )
