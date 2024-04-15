from pyshacl import validate

import dcat
import cache

import argparse
import yaml
import logging
from rdflib import Graph
import os

# Handle cli arguments, e.g. --log=DEBUG
parser = argparse.ArgumentParser()
parser.add_argument("-l", "--log", help = "loglevel, e.g. INFO, DEBUG,...")
args = parser.parse_args()
logger = logging.getLogger(__name__)
if args.log:
    numeric_level = getattr(logging, args.log.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % args.log.upper())
    logging.basicConfig(level=numeric_level)

with open('config.yml', 'r') as file:
    config = yaml.safe_load(file)
shape_graph = dcat.shapes_graph()

# Prepare the encapsulating catalogue
catalog = Graph()
catalog = cache.set_namespace(catalog)
catalog.parse("vsds-catalog.ttl", format="turtle")

for catalogue_id in config['catalogues']:
    catalogue = config['catalogues'][catalogue_id]
    logger.info("%s: start processing", catalogue_id)

    # Get the data
    data_graph = cache.fetch_graph_with_cache(catalogue['url'], catalogue['format'], catalogue_id + '_source')
    if(cache.has_override(catalogue_id)):
        data_graph = cache.get_override(catalogue_id)
        logger.warning("Using override for catalogue %s, cached copy is used!", catalogue_id)
    data_graph = dcat.delete_non_dcat_data(data_graph)
    data_graph = dcat.add_catalog_membership(data_graph)
    
    # Validate
    validation_result = validate(data_graph, shacl_graph=shape_graph)
    conforms, results_graph, results_text = validation_result
    dataset_path = "datasets/" + catalogue_id + ".ttl"
    if conforms:
        logger.info("%s: succesfully validated.", catalogue_id)
        # Commit dataset to disk
        data_graph.serialize(dataset_path, format="turtle")
    else:
        # New dataset is invalid.
        data_graph = Graph()
        # If a previous version exists on disk, use that.
        if os.path.isfile(dataset_path):
            data_graph = data_graph.parse(dataset_path, format="turtle")
        logger.error("%s: validation failed.", catalogue_id)
        logger.debug(results_text)
    catalog += data_graph
catalog.serialize("datasets/catalog.ttl", format="turtle")
