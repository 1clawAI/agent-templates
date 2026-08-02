"""Tests for 1Claw CrewAI storage adapter."""

import json
from unittest.mock import MagicMock, patch

import pytest

from storage import OneclawStorage, OneclawSemanticStorage


@pytest.fixture
def storage():
    return OneclawStorage(
        namespace="test-crew",
        sidecar_url="http://localhost:9999",
    )


@pytest.fixture
def semantic():
    return OneclawSemanticStorage(
        namespace="test-semantic",
        sidecar_url="http://localhost:9999",
    )


class TestOneclawStorage:
    @patch("storage.requests.put")
    def test_save_dict(self, mock_put: MagicMock, storage: OneclawStorage):
        mock_put.return_value = MagicMock(status_code=200)
        mock_put.return_value.raise_for_status = lambda: None

        storage.save("key1", {"hello": "world"})
        mock_put.assert_called_once()
        body = mock_put.call_args.kwargs["json"]
        assert json.loads(body["value"]) == {"hello": "world"}
        assert body["tier"] == "durable"

    @patch("storage.requests.put")
    def test_save_string(self, mock_put: MagicMock, storage: OneclawStorage):
        mock_put.return_value = MagicMock(status_code=200)
        mock_put.return_value.raise_for_status = lambda: None

        storage.save("key2", "plain text")
        body = mock_put.call_args.kwargs["json"]
        assert body["value"] == "plain text"

    @patch("storage.requests.get")
    def test_load_existing(self, mock_get: MagicMock, storage: OneclawStorage):
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"value": '{"data": 123}'},
        )
        mock_get.return_value.raise_for_status = lambda: None

        result = storage.load("key1")
        assert result == {"data": 123}

    @patch("storage.requests.get")
    def test_load_not_found(self, mock_get: MagicMock, storage: OneclawStorage):
        mock_get.return_value = MagicMock(status_code=404)
        result = storage.load("missing")
        assert result is None

    @patch("storage.requests.delete")
    def test_delete(self, mock_delete: MagicMock, storage: OneclawStorage):
        mock_delete.return_value = MagicMock(status_code=200)
        storage.delete("key1")
        mock_delete.assert_called_once()

    @patch("storage.requests.get")
    def test_list_keys(self, mock_get: MagicMock, storage: OneclawStorage):
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"entries": [{"key": "a"}, {"key": "b"}]},
        )
        mock_get.return_value.raise_for_status = lambda: None

        keys = storage.list_keys()
        assert keys == ["a", "b"]


class TestOneclawSemanticStorage:
    def test_defaults(self, semantic: OneclawSemanticStorage):
        assert semantic.tier == "semantic"
        assert semantic.namespace == "test-semantic"

    @patch("storage.requests.post")
    def test_search(self, mock_post: MagicMock, semantic: OneclawSemanticStorage):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"results": [{"key": "r1", "score": 0.95}]},
        )
        mock_post.return_value.raise_for_status = lambda: None

        results = semantic.search("test query", top_k=3)
        assert len(results) == 1
        assert results[0]["key"] == "r1"
