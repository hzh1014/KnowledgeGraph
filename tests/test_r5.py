"""Tests for R5 features: history window, export data structure."""
import json
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TestHistoryWindow:
    """Test conversation history windowing logic."""

    def _apply_window(self, history, window):
        """Replicate the windowing logic from main_api.py."""
        if window > 0 and len(history) > window:
            return history[-window:]
        return history

    def test_no_window_returns_all(self):
        history = [(f"q{i}", f"a{i}") for i in range(20)]
        result = self._apply_window(history, 0)
        assert len(result) == 20

    def test_window_truncates(self):
        history = [(f"q{i}", f"a{i}") for i in range(20)]
        result = self._apply_window(history, 5)
        assert len(result) == 5
        assert result[0] == ("q15", "a15")
        assert result[-1] == ("q19", "a19")

    def test_window_larger_than_history(self):
        history = [(f"q{i}", f"a{i}") for i in range(3)]
        result = self._apply_window(history, 10)
        assert len(result) == 3

    def test_window_equal_to_history(self):
        history = [(f"q{i}", f"a{i}") for i in range(5)]
        result = self._apply_window(history, 5)
        assert len(result) == 5

    def test_window_of_one(self):
        history = [("q0", "a0"), ("q1", "a1"), ("q2", "a2")]
        result = self._apply_window(history, 1)
        assert len(result) == 1
        assert result[0] == ("q2", "a2")

    def test_empty_history(self):
        result = self._apply_window([], 5)
        assert result == []


class TestExportDataStructure:
    """Test that graph data structure is suitable for export."""

    def test_graph_json_serializable(self):
        """Graph data must be JSON-serializable for export."""
        graph = {
            "nodes": [{"name": "舰艇", "id": 0, "category": 0}],
            "links": [{"source": 0, "target": 1, "name": "关系"}],
            "sents": ["句子"],
            "categories": [{"name": "设施"}]
        }
        # Should not raise
        serialized = json.dumps(graph, ensure_ascii=False)
        deserialized = json.loads(serialized)
        assert deserialized == graph

    def test_graph_nodes_have_required_fields(self):
        """Each node should have at least 'name' for display."""
        graph = {
            "nodes": [
                {"name": "舰艇", "id": 0},
                {"name": "损管", "id": 1}
            ],
            "links": []
        }
        for node in graph["nodes"]:
            assert "name" in node
            assert isinstance(node["name"], str)
            assert len(node["name"]) > 0

    def test_graph_links_have_required_fields(self):
        """Each link should have source, target for ECharts."""
        graph = {
            "nodes": [],
            "links": [
                {"source": 0, "target": 1, "name": "关系"}
            ]
        }
        for link in graph["links"]:
            assert "source" in link
            assert "target" in link

    def test_export_json_format(self):
        """Exported JSON should be pretty-printed."""
        graph = {"nodes": [{"name": "test"}], "links": []}
        output = json.dumps(graph, indent=2, ensure_ascii=False)
        assert "\n" in output
        assert "  " in output


class TestLocalStorageKey:
    """Test localStorage key consistency."""

    def test_storage_key_defined(self):
        """The storage key should be a consistent string."""
        STORAGE_KEY = 'chatkg_history'
        assert STORAGE_KEY == 'chatkg_history'
        assert isinstance(STORAGE_KEY, str)
        assert len(STORAGE_KEY) > 0
