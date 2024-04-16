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
parser.add_argument("-c", "--cache", action='store_true', help = "Enable caching of resources to speed up/offline development")
args = parser.parse_args()
logger = logging.getLogger(__name__)
if args.log:
    numeric_level = getattr(logging, args.log.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % args.log.upper())
    logging.basicConfig(level=numeric_level)

cache.caching_enabled = args.cache
if cache.caching_enabled:
    logger.warning("Caching is enabled, this should not be used in production.")

with open('config.yml', 'r') as file:
    config = yaml.safe_load(file)
shape_graph = dcat.shapes_graph()

# Prepare the encapsulating catalogue
catalog = Graph()
catalog = dcat.set_namespace(catalog)
catalog.parse("vsds-catalog.ttl", format="turtle")

for catalogue_id in config['catalogues']:
    catalogue = config['catalogues'][catalogue_id]
    logger.info("%s: start processing", catalogue_id)

    try:
        data_graph = cache.fetch_graph_with_cache(catalogue['url'], catalogue['format'], catalogue_id)
        data_graph = dcat.delete_non_dcat_data(data_graph)
        data_graph = dcat.add_catalog_membership(data_graph)

        # Validate
        validation_result = validate(data_graph, shacl_graph=shape_graph)
        conforms, results_graph, results_text = validation_result
        if not conforms:
            logger.warning("%s: validation failed.", catalogue_id)
            logger.debug(results_text)
    except Exception as e:
        logger.error("%s: something went wrong processing this catalog: %s", catalogue_id, e)
        conforms = False

    dataset_path = "datasets/" + catalogue_id + ".ttl"
    if conforms:
        logger.info("%s: succesfully validated, updating dataset", catalogue_id)
        # Commit dataset to disk
        data_graph.serialize(dataset_path, format="turtle")
    else:
        # Dataset is invalid.
        data_graph = Graph()
        # If a previous version exists on disk, use that.
        if os.path.isfile(dataset_path):
            logger.info("%s: falling back to previous version of dataset.")
            data_graph = data_graph.parse(dataset_path, format="turtle")
    catalog += data_graph

# Store the updated catalog
catalog.serialize("datasets/catalog.ttl", format="turtle")
