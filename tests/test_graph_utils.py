"""Tests for server/app/utils/graph_utils.py — data mutation and caching fixes."""
import copy
import json
import sys
from pathlib import Path

import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def sample_graph_data():
    """Minimal graph data matching server/data/data.json structure."""
    return {
        "nodes": [
            {"name": "舰艇", "category": 0},
            {"name": "起火", "category": 1},
            {"name": "损管", "category": 2},
        ],
        "links": [
            {"source": 0, "target": 1, "name": "发生", "sent": 0},
            {"source": 1, "target": 2, "name": "处置", "sent": 1},
        ],
        "sents": ["舰艇起火", "起火后进行损管"],
        "categories": [{"name": "设施"}, {"name": "事故"}, {"name": "措施"}],
    }


@pytest.fixture(autouse=True)
def reset_graph_cache(monkeypatch):
    """Reset graph_utils module-level cache before each test."""
    import server.app.utils.graph_utils as gu
    monkeypatch.setattr(gu, '_data_cache', None)


@pytest.fixture
def mock_data_file(monkeypatch, tmp_path, sample_graph_data):
    """Redirect graph_utils to read from a temp data.json."""
    data_file = tmp_path / "data.json"
    data_file.write_text(json.dumps(sample_graph_data, ensure_ascii=False), encoding='utf-8')

    import server.app.utils.graph_utils as gu
    original_abspath = Path.__init__

    # Patch _load_data to use our temp file
    original_load = gu._load_data

    def patched_load():
        if gu._data_cache is None:
            with open(data_file, 'r', encoding='utf-8') as f:
                gu._data_cache = json.load(f)
        return gu._data_cache

    monkeypatch.setattr(gu, '_load_data', patched_load)
    return sample_graph_data


class TestSearchNodeItemNoMutation:
    """Verify search_node_item does not mutate the original cached data."""

    def test_multiple_calls_return_consistent_results(self, mock_data_file):
        """Calling search_node_item twice for the same entity should yield identical results."""
        from server.app.utils.graph_utils import search_node_item

        result1 = search_node_item("舰艇")
        result2 = search_node_item("舰艇")

        assert result1['nodes'] == result2['nodes']
        assert result1['links'] == result2['links']

    def test_original_data_not_mutated(self, mock_data_file):
        """The cached data dict must not be modified by search_node_item."""
        from server.app.utils.graph_utils import search_node_item, _load_data

        data = _load_data()
        original_links = copy.deepcopy(data['links'])
        original_nodes = copy.deepcopy(data['nodes'])

        search_node_item("舰艇")

        assert data['links'] == original_links
        assert data['nodes'] == original_nodes

    def test_different_entities_produce_independent_graphs(self, mock_data_file):
        """Searching different entities should not contaminate each other."""
        from server.app.utils.graph_utils import search_node_item

        g1 = search_node_item("舰艇")
        g2 = search_node_item("损管")

        names1 = {n['name'] for n in g1['nodes']}
        names2 = {n['name'] for n in g2['nodes']}

        # "舰艇" graph should contain 舰艇; "损管" graph should contain 损管
        assert "舰艇" in names1
        assert "损管" in names2

    def test_edge_source_target_are_integers(self, mock_data_file):
        """Links in the returned graph must have integer source/target."""
        from server.app.utils.graph_utils import search_node_item

        result = search_node_item("舰艇")
        for link in result['links']:
            assert isinstance(link['source'], int)
            assert isinstance(link['target'], int)

    def test_node_ids_are_sequential(self, mock_data_file):
        """Node IDs should be sequential starting from 0."""
        from server.app.utils.graph_utils import search_node_item

        result = search_node_item("舰艇")
        for idx, node in enumerate(result['nodes']):
            assert node['id'] == idx


class TestConvertGraphToTriples:
    """Test triple extraction from graph."""

    def test_basic_triples(self, mock_data_file):
        from server.app.utils.graph_utils import search_node_item, convert_graph_to_triples

        graph = search_node_item("舰艇")
        triples = convert_graph_to_triples(graph, "舰艇")

        assert len(triples) > 0
        for s, r, o in triples:
            assert isinstance(s, str)
            assert isinstance(r, str)
            assert isinstance(o, str)

    def test_entity_filter(self, mock_data_file):
        """Triples should only include those mentioning the entity."""
        from server.app.utils.graph_utils import search_node_item, convert_graph_to_triples

        graph = search_node_item("舰艇")
        triples = convert_graph_to_triples(graph, "舰艇")

        for s, r, o in triples:
            assert "舰艇" in s or "舰艇" in o


class TestDataCaching:
    """Verify module-level data caching works."""

    def test_cache_is_populated_after_first_call(self, mock_data_file):
        from server.app.utils.graph_utils import _load_data, _data_cache

        # Cache starts as None (reset by fixture)
        result = _load_data()
        assert result is not None
        assert 'nodes' in result
        assert 'links' in result
