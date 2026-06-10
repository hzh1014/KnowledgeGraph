"""
NER module using jieba + knowledge graph entity matching.
No PaddlePaddle dependency required.

Confidence levels:
  1.0 — exact match (jieba segment == entity name)
  0.9 — synonym match (segment is synonym of entity)
  0.8 — entity-in-text (entity substring found in input)
  0.7 — combination match (adjacent jieba segments form entity name)
  0.5 — fuzzy match (segment is substring of entity, fallback)
"""
import os
import sys
import json
import jieba

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from modules.utils.logger import logger


class NerAPI:
    def __init__(self):
        """Initialize NER with jieba and graph entity list."""
        self.graph_entities = set()
        self.short_entities = []
        self.synonyms = {}        # canonical -> [aliases]
        self._alias_to_canonical = {}  # alias -> canonical
        self._load_graph_entities()
        self._load_synonyms()
        logger.info(f"NER loaded with {len(self.graph_entities)} graph entities, {len(self._alias_to_canonical)} synonym aliases")

    def _load_graph_entities(self):
        """Load entity names from the knowledge graph data."""
        try:
            data_file = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                'data', 'data.json'
            )
            if os.path.exists(data_file):
                with open(data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for node in data.get('nodes', []):
                    name = node.get('name', '').strip()
                    if name:
                        self.graph_entities.add(name)
                        # Add to jieba user dictionary for better segmentation
                        jieba.add_word(name, freq=10000, tag='nr')
            self.short_entities = [e for e in self.graph_entities if 2 <= len(e) <= 30]
        except Exception as e:
            logger.error(f"Failed to load graph entities: {e}")

    def _load_synonyms(self):
        """Load synonym dictionary for entity alias expansion."""
        try:
            synonyms_file = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                'data', 'synonyms.json'
            )
            if os.path.exists(synonyms_file):
                with open(synonyms_file, 'r', encoding='utf-8') as f:
                    self.synonyms = json.load(f)
                # Build reverse mapping: alias -> canonical name
                for canonical, aliases in self.synonyms.items():
                    for alias in aliases:
                        self._alias_to_canonical[alias] = canonical
                    # Also map canonical to itself
                    self._alias_to_canonical[canonical] = canonical
                logger.info(f"Loaded {len(self.synonyms)} synonym groups, {len(self._alias_to_canonical)} aliases")
        except Exception as e:
            logger.error(f"Failed to load synonyms: {e}")

    def _expand_with_synonyms(self, words):
        """Expand jieba segments with synonym mappings.

        Returns list of (word, canonical_name) tuples where canonical_name
        is the entity name that should be matched against the graph.
        """
        expanded = []
        for word in words:
            word = word.strip()
            if not word or len(word) < 2:
                continue
            expanded.append((word, word))
            # If this word is a synonym alias, also add the canonical form
            if word in self._alias_to_canonical:
                canonical = self._alias_to_canonical[word]
                if canonical != word:
                    expanded.append((word, canonical))
        return expanded

    def predict(self, text):
        """Predict named entities in text using jieba + graph matching.

        Returns list of (entity_name, entity_type, confidence) tuples,
        sorted by confidence (highest first).
        """
        if not text:
            return []

        results = []  # (name, etype, confidence)
        seen = set()
        # Use jieba to segment
        words = jieba.lcut(text)
        expanded = self._expand_with_synonyms(words)

        # 1. Exact match: jieba segment == entity name (confidence 1.0)
        for word, canonical in expanded:
            if canonical in self.graph_entities and canonical not in seen:
                results.append((canonical, 'graph_entity', 1.0 if word == canonical else 0.9))
                seen.add(canonical)

        # 2. Entity contained in text (confidence 0.8)
        for entity in self.short_entities:
            if entity in text and entity not in seen:
                results.append((entity, 'graph_entity', 0.8))
                seen.add(entity)

        # 3. Combination match: adjacent segments form entity name (confidence 0.7)
        if len(words) >= 2:
            for i in range(len(words) - 1):
                combo = words[i].strip() + words[i + 1].strip()
                if len(combo) < 2:
                    continue
                # Check if combo matches any entity
                if combo in self.graph_entities and combo not in seen:
                    results.append((combo, 'graph_entity', 0.7))
                    seen.add(combo)
                # Also check synonym expansion for combo
                if combo in self._alias_to_canonical:
                    canonical = self._alias_to_canonical[combo]
                    if canonical in self.graph_entities and canonical not in seen:
                        results.append((canonical, 'graph_entity', 0.7))
                        seen.add(canonical)

        # 4. Fuzzy fallback: segment is substring of entity (confidence 0.5)
        # Only if no high-confidence matches found
        if not results:
            for word, canonical in expanded:
                for entity in self.short_entities:
                    if word in entity and entity not in seen:
                        results.append((entity, 'graph_entity', 0.5))
                        seen.add(entity)
                if len(results) >= 5:
                    break

        # Sort by confidence (desc), then by length (asc, more specific first)
        results.sort(key=lambda x: (-x[2], len(x[0])))
        return results[:10]

    def get_entities(self, text, etypes=None):
        """Get entity strings from text.

        Args:
            text: Input text
            etypes: Ignored (kept for compatibility)

        Returns:
            List of entity strings
        """
        results = self.predict(text)
        return [r[0] for r in results]


# Global instance
_ner_instance = None


def get_ner():
    """Get or create NER instance (singleton)."""
    global _ner_instance
    if _ner_instance is None:
        _ner_instance = NerAPI()
    return _ner_instance
