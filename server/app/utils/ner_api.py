"""
NER module using jieba + knowledge graph entity matching.
No PaddlePaddle dependency required.
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
        self._load_graph_entities()
        logger.info(f"NER loaded with {len(self.graph_entities)} graph entities")

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
        except Exception as e:
            logger.error(f"Failed to load graph entities: {e}")

    def predict(self, text):
        """Predict named entities in text using jieba + graph matching."""
        if not text:
            return []

        results = []
        seen = set()
        # Use jieba to segment
        words = jieba.lcut(text)

        # Filter: only use entity names with reasonable length (2-30 chars)
        short_entities = [e for e in self.graph_entities if 2 <= len(e) <= 30]

        # 1. Exact match: jieba segment == entity name
        for word in words:
            word = word.strip()
            if not word or len(word) < 2:
                continue
            if word in self.graph_entities and word not in seen:
                results.append((word, 'graph_entity'))
                seen.add(word)

        # 2. Entity contained in text (e.g., "舰艇起火" in "舰艇起火后应该如何处理")
        for entity in short_entities:
            if entity in text and entity not in seen:
                results.append((entity, 'graph_entity'))
                seen.add(entity)

        # 3. Segment is substring of entity (e.g., "舰艇" matches "舰艇起火")
        # Only if no exact matches found, limit to top 5
        if not results:
            for word in words:
                word = word.strip()
                if not word or len(word) < 2:
                    continue
                for entity in short_entities:
                    if word in entity and entity not in seen:
                        results.append((entity, 'graph_entity'))
                        seen.add(entity)
                if len(results) >= 5:
                    break

        # Sort by length (shorter entities first - more specific) and limit
        results.sort(key=lambda x: len(x[0]))
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
