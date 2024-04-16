from rdflib import Graph
import os
import logging

logger = logging.getLogger(__name__)

caching_enabled = False

def fetch_graph_with_cache(url, format, cache_id):
    g = get(cache_id)
    if g:
        return g
    g = Graph()
    g.parse(location=url, format=format)
    set(cache_id, g)
    return g


def get(cache_id):
    # Overrides allow for temporary fixes, that should be made in the upstream source.
    if has_override(cache_id):
        logger.warning("%s is loaded from override. Overrides should not be used in production.", cache_id)
        return get_override(cache_id)
    # If caching is disabled -> cache miss.
    if not caching_enabled:
        return None
    logger.debug("cache get: %s", cache_id)
    graph = Graph()
    cache_path = 'cache/' + cache_id + '.ttl'
    # Hit
    if os.path.isfile(cache_path):
        graph.parse(cache_path, format="turtle")
        return graph
    # Miss
    return None

def set(cache_id, graph):
    if not caching_enabled:
        return graph
    logger.debug("cache set: %s", cache_id)
    cache_path = 'cache/' + cache_id + '.ttl'
    graph.serialize(cache_path, format="turtle")
    return graph

def has_override(id):
    override_path = 'override/' + id + '.ttl'
    return os.path.isfile(override_path)

def get_override(id):
    graph = Graph()
    override_path = 'override/' + id + '.ttl'
    if os.path.isfile(override_path):
        graph.parse(override_path, format="turtle")
        return graph
    raise RuntimeError("Override not found.")