import json
import os
import copy


# Module-level cache: load data.json once
_data_cache = None


def _load_data():
    """Load and cache knowledge graph data from data.json."""
    global _data_cache
    if _data_cache is None:
        data_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            'data', 'data.json'
        )
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

    DEEP = 1

    # search node
    search_nodes = [user_input]
    for d in range(DEEP):
        for search_node in search_nodes:
            for edge in data['links']:
                source = copy.deepcopy(data['nodes'][int(edge['source'])])
                target = copy.deepcopy(data['nodes'][int(edge['target'])])
                if source['name'] in search_node or search_node in source['name'] or target['name'] in search_node or search_node in target['name']:
                    sent = data['sents'][edge['sent']]
                    if sent not in lite_graph['sents']:
                        edge_copy = copy.deepcopy(edge)
                        edge_copy['sent'] = len(lite_graph['sents'])
                        lite_graph['sents'].append(sent)
                    else:
                        edge_copy = copy.deepcopy(edge)
                        edge_copy['sent'] = lite_graph['sents'].index(sent)

                    if source not in lite_graph['nodes']:
                        source['id'] = len(lite_graph['nodes'])
                        lite_graph['nodes'].append(source)
                    else:
                        source['id'] = lite_graph['nodes'].index(source)

                    if target not in lite_graph['nodes']:
                        target['id'] = len(lite_graph['nodes'])
                        lite_graph['nodes'].append(target)
                    else:
                        target['id'] = lite_graph['nodes'].index(target)

                    edge_copy['source'] = source['id']
                    edge_copy['target'] = target['id']
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
