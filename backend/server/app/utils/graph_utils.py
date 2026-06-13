import json
import os
import copy

from config.settings import settings


# Module-level cache: load data.json once
_data_cache = None


def _load_data():
    """Load and cache knowledge graph data from data.json."""
    global _data_cache
    if _data_cache is None:
        data_file = str(settings.PROJECT_ROOT / 'backend' / 'server' / 'data' / 'data.json')
        with open(data_file, 'r', encoding='utf-8') as f:
            _data_cache = json.load(f)
    return _data_cache


def search_node_item(user_input, lite_graph=None):
    data = _load_data()

    if lite_graph is None:
        lite_graph = {
            'nodes': [],
            'links': [],
            'sents': [],
            'categories': data.get('categories', [])
        }

    # Build O(1) lookup indexes
    node_index = {n['name']: i for i, n in enumerate(lite_graph['nodes'])}
    sent_index = {s: i for i, s in enumerate(lite_graph['sents'])}

    DEEP = 1

    search_nodes = [user_input]
    for d in range(DEEP):
        for search_node in search_nodes:
            for edge in data['links']:
                src_name = data['nodes'][int(edge['source'])]['name']
                tgt_name = data['nodes'][int(edge['target'])]['name']
                if (src_name in search_node or search_node in src_name or
                        tgt_name in search_node or search_node in tgt_name):
                    # Handle sent
                    sent = data['sents'][edge['sent']]
                    if sent not in sent_index:
                        sent_index[sent] = len(lite_graph['sents'])
                        lite_graph['sents'].append(sent)

                    # Handle source node
                    if src_name not in node_index:
                        source = copy.deepcopy(data['nodes'][int(edge['source'])])
                        source['id'] = len(lite_graph['nodes'])
                        node_index[src_name] = source['id']
                        lite_graph['nodes'].append(source)

                    # Handle target node
                    if tgt_name not in node_index:
                        target = copy.deepcopy(data['nodes'][int(edge['target'])])
                        target['id'] = len(lite_graph['nodes'])
                        node_index[tgt_name] = target['id']
                        lite_graph['nodes'].append(target)

                    # Create edge copy
                    edge_copy = copy.deepcopy(edge)
                    edge_copy['source'] = node_index[src_name]
                    edge_copy['target'] = node_index[tgt_name]
                    edge_copy['sent'] = sent_index[sent]
                    lite_graph['links'].append(edge_copy)

        if len(lite_graph['nodes']) == 0:
            break

        search_nodes = [node['name'] for node in lite_graph['nodes']]

    return lite_graph


def convert_graph_to_triples(graph, entity=None):
    triples = []
    for link in graph['links']:
        source = graph['nodes'][link['source']]
        target = graph['nodes'][link['target']]

        if entity is not None:
            if entity in source['name'] or entity in target['name']:
                triples.append((source['name'], link["name"], target['name']))
        else:
            triples.append((source['name'], link["name"], target['name']))

    return triples
