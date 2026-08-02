"""Tests for 1Claw LangChain memory adapter."""

import json
from unittest.mock import MagicMock, patch

import pytest

from memory import OneclawMemory, OneclawScratchMemory


@pytest.fixture
def memory():
    return OneclawMemory(
        namespace="test-ns",
        sidecar_url="http://localhost:9999",
        session_key="session-1",
    )


@pytest.fixture
def scratch_memory():
    return OneclawScratchMemory(
        namespace="test-scratch",
        sidecar_url="http://localhost:9999",
        ttl_seconds=600,
    )


class TestOneclawMemory:
    def test_memory_variables(self, memory: OneclawMemory):
        assert memory.memory_variables == ["history"]

    @patch("memory.requests.get")
    def test_load_empty(self, mock_get: MagicMock, memory: OneclawMemory):
        mock_get.return_value = MagicMock(status_code=404)
        result = memory.load_memory_variables({})
        assert result == {"history": ""}

    @patch("memory.requests.get")
    def test_load_existing(self, mock_get: MagicMock, memory: OneclawMemory):
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"value": "Human: Hi\nAI: Hello!"},
        )
        mock_get.return_value.raise_for_status = lambda: None
        result = memory.load_memory_variables({})
        assert result == {"history": "Human: Hi\nAI: Hello!"}

    @patch("memory.requests.put")
    @patch("memory.requests.get")
    def test_save_context(
        self, mock_get: MagicMock, mock_put: MagicMock, memory: OneclawMemory
    ):
        mock_get.return_value = MagicMock(status_code=404)
        memory.save_context({"input": "Hello"}, {"output": "Hi there!"})

        mock_put.assert_called_once()
        call_kwargs = mock_put.call_args
        body = call_kwargs.kwargs["json"] if "json" in call_kwargs.kwargs else call_kwargs[1]["json"]
        assert "Human: Hello" in body["value"]
        assert "AI: Hi there!" in body["value"]
        assert body["tier"] == "durable"

    @patch("memory.requests.delete")
    def test_clear(self, mock_delete: MagicMock, memory: OneclawMemory):
        memory.clear()
        mock_delete.assert_called_once()


class TestOneclawScratchMemory:
    def test_defaults(self, scratch_memory: OneclawScratchMemory):
        assert scratch_memory.tier == "scratch"
        assert scratch_memory.ttl_seconds == 600

    @patch("memory.requests.put")
    @patch("memory.requests.get")
    def test_save_with_ttl(
        self, mock_get: MagicMock, mock_put: MagicMock, scratch_memory: OneclawScratchMemory
    ):
        mock_get.return_value = MagicMock(status_code=404)
        scratch_memory.save_context({"input": "temp"}, {"output": "data"})

        call_kwargs = mock_put.call_args
        body = call_kwargs.kwargs["json"] if "json" in call_kwargs.kwargs else call_kwargs[1]["json"]
        assert body["tier"] == "scratch"
        assert body["ttl_seconds"] == 600
