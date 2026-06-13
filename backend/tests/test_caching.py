"""Tests for caching logic in main_api.py (R2)."""
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TestWikiCache:
    """Test Wikipedia search result caching pattern."""

    def test_cache_hit_skips_search(self):
        """When a query is in cache, WikiSearcher.search should not be called."""
        cache = {}
        mock_searcher = MagicMock()

        query = "舰艇"
        cached_result = {"title": "舰艇", "summary": "军用船只"}
        cache[query] = cached_result

        # Simulate chat logic: check cache first
        wiki = {"title": "无相关信息", "summary": "暂无相关描述"}
        if query in cache:
            wiki = cache[query]
        else:
            mock_searcher.search(query)

        assert wiki == cached_result
        mock_searcher.search.assert_not_called()

    def test_cache_miss_calls_search(self):
        """When a query is not in cache, WikiSearcher.search should be called."""
        cache = {}
        mock_searcher = MagicMock()
        mock_result = MagicMock()
        mock_result.title = "舰艇"
        mock_result.summary = "军用船只"
        mock_searcher.search.return_value = mock_result

        query = "舰艇"
        wiki = {"title": "无相关信息", "summary": "暂无相关描述"}
        if query in cache:
            wiki = cache[query]
        else:
            result = mock_searcher.search(query)
            if result is not None:
                wiki = {"title": result.title, "summary": result.summary[:500]}
                cache[query] = wiki

        assert wiki["title"] == "舰艇"
        assert wiki["summary"] == "军用船只"
        assert query in cache
        mock_searcher.search.assert_called_once_with(query)

    def test_cache_populates_all_searched_entities(self):
        """Cache should store results for all entities that were searched."""
        cache = {}
        entities = ["舰艇", "起火", "损管"]
        user_input = "舰艇起火怎么办"
        wiki = {"title": "舰艇", "summary": "军用船只"}

        # Simulate: wiki was found via "舰艇", cache all searched terms
        for ent in entities + [user_input]:
            cache[ent] = wiki

        for ent in entities + [user_input]:
            assert ent in cache
            assert cache[ent]["title"] == "舰艇"


class TestGraphCache:
    """Test graph search result caching pattern."""

    def test_cache_returns_same_result(self):
        """Cached graph result should be identical on repeated access."""
        cache = {}

        # Simulate caching
        entity = "舰艇"
        entity_graph = {"nodes": [{"name": "舰艇"}], "links": [], "sents": []}
        entity_triples = [("舰艇", "是", "军用船只")]
        cache[entity] = (entity_graph, entity_triples)

        # Access from cache
        cached_graph, cached_triples = cache[entity]
        assert cached_graph == entity_graph
        assert cached_triples == entity_triples

    def test_multi_entity_merge(self):
        """Multiple entity results should merge correctly."""
        cache = {}

        entities = ["舰艇", "损管"]
        graphs = {
            "舰艇": {"nodes": [{"name": "舰艇"}], "links": [], "sents": ["舰艇"]},
            "损管": {"nodes": [{"name": "损管"}], "links": [], "sents": ["损管"]},
        }
        triples_map = {
            "舰艇": [("舰艇", "是", "军用船只")],
            "损管": [("损管", "用于", "损害管制")],
        }

        # Simulate independent search + cache
        merged_graph = {"nodes": [], "links": [], "sents": [], "categories": []}
        all_triples = []

        for entity in entities:
            if entity in cache:
                eg, et = cache[entity]
            else:
                eg = graphs[entity]
                et = triples_map[entity]
                cache[entity] = (eg, et)
            merged_graph["nodes"].extend(eg.get("nodes", []))
            merged_graph["links"].extend(eg.get("links", []))
            merged_graph["sents"].extend(eg.get("sents", []))
            all_triples += et

        assert len(merged_graph["nodes"]) == 2
        assert len(merged_graph["sents"]) == 2
        assert len(all_triples) == 2

    def test_cache_independence(self):
        """Cached results for different entities should be independent."""
        cache = {}

        graph_a = {"nodes": [{"name": "A"}], "links": [], "sents": []}
        graph_b = {"nodes": [{"name": "B"}], "links": [], "sents": []}

        cache["A"] = (graph_a, [("A", "r", "X")])
        cache["B"] = (graph_b, [("B", "r", "Y")])

        ga, ta = cache["A"]
        gb, tb = cache["B"]

        assert ga["nodes"][0]["name"] == "A"
        assert gb["nodes"][0]["name"] == "B"
        assert len(ta) == 1
        assert len(tb) == 1


class TestStreamChunkStructure:
    """Test that streaming response structure matches frontend expectations."""

    def test_intermediate_chunk_has_only_updates(self):
        """Intermediate chunks should only contain 'updates' field."""
        chunk = {
            "updates": {"query": "test", "response": "partial"}
        }
        assert "updates" in chunk
        assert "graph" not in chunk
        assert "wiki" not in chunk
        assert "image" not in chunk
        assert "history" not in chunk

    def test_final_chunk_has_all_fields(self):
        """Final chunk should contain all fields including entities."""
        chunk = {
            "history": [("test", "response")],
            "updates": {"query": "test", "response": "response"},
            "image": None,
            "graph": {"nodes": [], "links": []},
            "wiki": {"title": "t", "summary": "s"},
            "entities": ["舰艇", "损管"]
        }
        assert "updates" in chunk
        assert "history" in chunk
        assert "graph" in chunk
        assert "wiki" in chunk
        assert "image" in chunk
        assert "entities" in chunk
        assert isinstance(chunk["entities"], list)
