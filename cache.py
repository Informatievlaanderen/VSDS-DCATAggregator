from rdflib import Graph, Namespace
import os

def set_namespace(graph: Graph):
    MDCAT = Namespace("http://data.vlaanderen.be/ns/metadata-dcat#")
    VCARD = Namespace("http://www.w3.org/2006/vcard/ns#")
    graph.bind("mdcat", MDCAT)
    graph.bind("vcard", VCARD)
    return graph

def fetch_graph_with_cache(url, format, cache_id):
    g = get(cache_id)
    if g:
        return g
    g = Graph()
    set_namespace(g)
    g.parse(location=url, format=format)
    set(cache_id, g)
    return g


def get(cache_id):
    graph = Graph()
    set_namespace(graph)
    cache_path = 'cache/' + cache_id + '.ttl'
    # Hit
    if os.path.isfile(cache_path):
        graph.parse(cache_path, format="turtle")
        return graph
    # Miss
    return None

def set(cache_id, graph):
    cache_path = 'cache/' + cache_id + '.ttl'
    graph.serialize(cache_path, format="turtle")
    return graph

def has_override(id):
    override_path = 'override/' + id + '.ttl'
    return os.path.isfile(override_path)

def get_override(id):
    graph = Graph()
    set_namespace(graph)
    override_path = 'override/' + id + '.ttl'
    if os.path.isfile(override_path):
        graph.parse(override_path, format="turtle")
        return graph
    raise RuntimeError("Override not found.")