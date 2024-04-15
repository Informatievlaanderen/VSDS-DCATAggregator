import cache
from rdflib import URIRef, Literal, Graph

def shapes_graph():
    shapes = cache.get('shapes_processed')
    if shapes:
        return shapes
    shapes = cache.fetch_graph_with_cache("https://raw.githubusercontent.com/sandervd/OSLOthema-metadataVoorServices/validation/metadata_dcat.jsonld", "json-ld", "shapes_source")
    pred = URIRef("http://www.w3.org/ns/shacl#deactivated")
    obj = Literal(True)

    # Don't validate if concept is member of the right vocab (external uris)
    result = shapes.query("""
        PREFIX sh:   <http://www.w3.org/ns/shacl#>
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        SELECT ?rule
        WHERE {?rule sh:node/sh:property/sh:class skos:ConceptScheme}
        """)
    
    for row in result:
        shapes.add((row.rule, pred, obj))
    # External instances (e.g. license, skos concepts,...) are absent from datagraph, so don't check range for references to them.
    result = shapes.query("""
        PREFIX sh:   <http://www.w3.org/ns/shacl#>
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        SELECT ?rule
        WHERE {
            VALUES (?class) {
                # non exhaustive list, should check all...
                (<http://purl.org/dc/terms/LicenseDocument>)
                (<http://purl.org/dc/terms/Standard>)
                (skos:Concept)
            }
            ?rule sh:class ?class .
        }
        """)
    for row in result:
        shapes.add((row.rule, pred, obj))

    # Disable unique lang constraint on keywords.
    keywords = URIRef("https://data.vlaanderen.be/shacl/metadata_dcat#DatasetShape/1b8b3557ea1ccbabc0962c345782ae53740e72e1")
    shapes.add((keywords, pred, obj))
    
    # Disable dcat:endpointDescription restriction to anyURI
    endpoint = URIRef("https://data.vlaanderen.be/shacl/metadata_dcat#DataServiceShape/dbc2548616486a154002cfba6a3bc2cbc554a682")
    shapes.add((endpoint, pred, obj))
    # Disable dcat:endpoinURL restriction to anyURI
    endpoint = URIRef("https://data.vlaanderen.be/shacl/metadata_dcat#DataServiceShape/67c89165b0f38567bf099862ffdef88f25e68714")
    shapes.add((endpoint, pred, obj))

    # Add a constraint: all dataset accessability must be public.
    shapes.update("""
        INSERT DATA {
        <https://data.vlaanderen.be/shacl/DCAT-AP-VL#hack-1>
            a sh:PropertyShape ;
                sh:hasValue <http://publications.europa.eu/resource/authority/access-right/PUBLIC>;
                sh:description  "De toegankelijkheid voor de dataset."@nl;
                sh:name         "toegankelijkheid"@nl;
                sh:path         <http://purl.org/dc/terms/accessRights>;
                vl:message      [ <https://data.vlaanderen.be/shacl/DCAT-AP-VLnl>
                                "De toegankelijkheid moet publiek zijn." ];
                vl:rule         "hack-1" .
        }
        """)
    
    cache.set('shapes_processed', shapes)
    # @todo Check for LDES format on datasets.
    return shapes
    
# Remove all non dcat triples from the graph. Also catalog is deleted.
def delete_non_dcat_data(graph: Graph):
    results = graph.query("""
        prefix schema: <http://schema.org/> 
        prefix v:    <http://www.w3.org/2006/vcard/ns#> 
        prefix dcat: <http://www.w3.org/ns/dcat#> 
        prefix dct:  <http://purl.org/dc/terms/>

        SELECT ?id
        WHERE {
            VALUES (?types) {
                (dcat:CatalogRecord)
                (dcat:DataService)
                (dcat:Dataset)
                (dcat:Distribution)
                (dcat:Relationship)
                (dcat:Resource)
                (dcat:Role)
                (dct:Agent)
                (v:Kind)
                (v:Organization)
                (schema:ContactPoint)
                (dct:ProvenanceStatement)
                (dct:RightsStatement)
                (dct:LicenseDocument)
                (dct:Location)
                (dct:Standard)
            }
            FILTER (isIRI(?id))
            ?id a ?type .
            FILTER(?type IN (?types)) .
        }
        """)
    
    ng = Graph()
    cache.set_namespace(ng)
    for row in results:
        # Serialze and deserialize to get rid of bnodes shared between entities.
        cbd_text = graph.cbd(row.id).serialize(format="turtle")
        cbd = Graph().parse(data=cbd_text)
        ng += cbd
    return ng

# Make each dataset and dataservice a member of the shared (vsds) catalog.
def add_catalog_membership(graph: Graph):
    graph.update(
    """
        prefix dcat: <http://www.w3.org/ns/dcat#> 

        INSERT {
            <htts://data.vlaanderen.be/id/catalog/vsds> dcat:dataset ?dataset .
        }
        WHERE {
            ?dataset a dcat:Dataset
        }
    """
    )
    graph.update(
    """
        prefix dcat: <http://www.w3.org/ns/dcat#> 

        INSERT {
            <htts://data.vlaanderen.be/id/catalog/vsds> dcat:service ?dataservice .
        }
        WHERE {
            ?dataservice a dcat:DataService
        }
    """
    )

    return graph