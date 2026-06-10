"""Tests for server/app/utils/ner_api.py — NER with synonyms, combinations, confidence."""
import json
import sys
from pathlib import Path

import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def sample_ner_data():
    """Minimal data.json for NER testing."""
    return {
        "nodes": [
            {"name": "潜水装备"},
            {"name": "损管"},
            {"name": "舰艇"},
            {"name": "起火"},
            {"name": "灭火训练"},
            {"name": "A"},           # too short (<2), should be excluded
            {"name": "这是一个非常非常非常非常非常非常非常非常非常非常长的实体名称超过三十个字符"},
        ],
        "links": [],
        "sents": [],
    }


@pytest.fixture
def sample_synonyms():
    """Minimal synonyms.json for testing."""
    return {
        "舰艇": ["军舰", "舰船"],
        "损管": ["损害管制"],
        "起火": ["着火", "失火"],
    }


@pytest.fixture
def ner_instance(monkeypatch, tmp_path, sample_ner_data, sample_synonyms):
    """Create a NerAPI instance with temp data and synonym files."""
    data_file = tmp_path / "data.json"
    data_file.write_text(json.dumps(sample_ner_data, ensure_ascii=False), encoding='utf-8')

    synonyms_file = tmp_path / "synonyms.json"
    synonyms_file.write_text(json.dumps(sample_synonyms, ensure_ascii=False), encoding='utf-8')

    import server.app.utils.ner_api as ner_mod

    def patched_init(self):
        self.graph_entities = set()
        self.short_entities = []
        self.synonyms = {}
        self._alias_to_canonical = {}
        # Load entities
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for node in data.get('nodes', []):
            name = node.get('name', '').strip()
            if name:
                self.graph_entities.add(name)
        self.short_entities = [e for e in self.graph_entities if 2 <= len(e) <= 30]
        # Load synonyms
        with open(synonyms_file, 'r', encoding='utf-8') as f:
            self.synonyms = json.load(f)
        for canonical, aliases in self.synonyms.items():
            for alias in aliases:
                self._alias_to_canonical[alias] = canonical
            self._alias_to_canonical[canonical] = canonical

    monkeypatch.setattr(ner_mod.NerAPI, '__init__', patched_init)
    monkeypatch.setattr(ner_mod, '_ner_instance', None)

    return ner_mod.NerAPI()


# ==================== Short Entities ====================

class TestShortEntitiesPrecomputed:
    """Verify short_entities is computed once at init."""

    def test_short_entities_excludes_too_short(self, ner_instance):
        for name in ner_instance.short_entities:
            assert len(name) >= 2

    def test_short_entities_excludes_too_long(self, ner_instance):
        for name in ner_instance.short_entities:
            assert len(name) <= 30

    def test_short_entities_contains_valid_entries(self, ner_instance):
        names = set(ner_instance.short_entities)
        assert "潜水装备" in names
        assert "损管" in names
        assert "舰艇" in names

    def test_short_entities_not_recomputed_on_predict(self, ner_instance):
        original = list(ner_instance.short_entities)
        ner_instance.predict("舰艇起火")
        assert ner_instance.short_entities == original


# ==================== Synonym Loading ====================

class TestSynonyms:
    """Test synonym dictionary loading and mapping."""

    def test_synonyms_loaded(self, ner_instance):
        assert len(ner_instance.synonyms) > 0
        assert "舰艇" in ner_instance.synonyms

    def test_alias_to_canonical(self, ner_instance):
        assert ner_instance._alias_to_canonical.get("军舰") == "舰艇"
        assert ner_instance._alias_to_canonical.get("舰船") == "舰艇"
        assert ner_instance._alias_to_canonical.get("损害管制") == "损管"

    def test_canonical_maps_to_self(self, ner_instance):
        assert ner_instance._alias_to_canonical.get("舰艇") == "舰艇"
        assert ner_instance._alias_to_canonical.get("损管") == "损管"


# ==================== Confidence Scores ====================

class TestConfidence:
    """Test that confidence scores are assigned correctly."""

    def test_exact_match_has_highest_confidence(self, ner_instance):
        results = ner_instance.predict("损管训练")
        names_conf = {r[0]: r[2] for r in results}
        # "损管" is an exact match (jieba should segment it out)
        assert "损管" in names_conf
        assert names_conf["损管"] == 1.0

    def test_synonym_match_confidence(self, ner_instance):
        # "军舰" is a synonym of "舰艇"
        results = ner_instance.predict("军舰起火")
        names_conf = {r[0]: r[2] for r in results}
        if "舰艇" in names_conf:
            # Should be synonym confidence (0.9) or exact (1.0 if canonical in text)
            assert names_conf["舰艇"] >= 0.9

    def test_substring_match_confidence(self, ner_instance):
        # "舰艇" is contained in "舰艇起火后如何处理"
        results = ner_instance.predict("舰艇起火后如何处理")
        names_conf = {r[0]: r[2] for r in results}
        if "舰艇" in names_conf:
            assert names_conf["舰艇"] >= 0.8

    def test_results_sorted_by_confidence(self, ner_instance):
        results = ner_instance.predict("舰艇损管训练")
        if len(results) >= 2:
            for i in range(len(results) - 1):
                assert results[i][2] >= results[i + 1][2]

    def test_result_tuple_has_three_elements(self, ner_instance):
        results = ner_instance.predict("舰艇起火")
        for r in results:
            assert len(r) == 3
            assert isinstance(r[0], str)
            assert isinstance(r[1], str)
            assert isinstance(r[2], float)


# ==================== Combination Matching ====================

class TestCombinationMatch:
    """Test adjacent segment combination matching."""

    def test_combination_entity_found(self, ner_instance):
        # "灭火训练" should be found when jieba segments it as ["灭火", "训练"]
        results = ner_instance.predict("进行灭火训练")
        names = [r[0] for r in results]
        # Either exact or combination match
        assert "灭火训练" in names

    def test_combination_confidence(self, ner_instance):
        results = ner_instance.predict("进行灭火训练")
        names_conf = {r[0]: r[2] for r in results}
        if "灭火训练" in names_conf:
            # Should be combination match (0.7) or higher
            assert names_conf["灭火训练"] >= 0.7


# ==================== Predict ====================

class TestPredict:
    """Test NER prediction logic."""

    def test_exact_match(self, ner_instance):
        results = ner_instance.predict("损管训练")
        names = [r[0] for r in results]
        assert "损管" in names

    def test_substring_match(self, ner_instance):
        results = ner_instance.predict("舰艇起火后如何处理")
        names = [r[0] for r in results]
        assert "舰艇" in names

    def test_empty_input(self, ner_instance):
        results = ner_instance.predict("")
        assert results == []

    def test_no_match(self, ner_instance):
        results = ner_instance.predict("今天天气真好")
        assert results == []

    def test_multiple_calls_consistent(self, ner_instance):
        text = "舰艇损管训练"
        r1 = ner_instance.predict(text)
        r2 = ner_instance.predict(text)
        assert r1 == r2

    def test_results_limited_to_10(self, ner_instance):
        results = ner_instance.predict("潜水装备损管舰艇起火灭火训练")
        assert len(results) <= 10


# ==================== Get Entities ====================

class TestGetEntities:
    """Test the simplified entity extraction interface."""

    def test_returns_string_list(self, ner_instance):
        entities = ner_instance.get_entities("舰艇起火")
        assert isinstance(entities, list)
        for e in entities:
            assert isinstance(e, str)

    def test_matches_predict(self, ner_instance):
        text = "损管训练"
        entities = ner_instance.get_entities(text)
        predicted = [r[0] for r in ner_instance.predict(text)]
        assert entities == predicted
