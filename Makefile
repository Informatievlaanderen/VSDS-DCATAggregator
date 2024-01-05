tracked-catalogs = $(wildcard catalogs/*)
catalogs := $(subst catalogs, workspace/dcat, $(tracked-catalogs))
catalogs-dcat-rdf := $(patsubst %,%/validated.nt,$(catalogs))

publications/beta.catalog.rdf: apache-jena workspace/catalog.ttl
	 ./apache-jena/bin/turtle --formatted=rdfxml workspace/catalog.ttl > publications/beta.catalog.rdf

# Release current catalogue to production.
publications/prod.catalog.rdf: publications/beta.catalog.rdf
	cp publications/beta.catalog.rdf publications/prod.catalog.rdf

workspace/catalog.ttl: apache-jena $(catalogs-dcat-rdf) schemas/infer/catalog.ttl schemas/infer/1.rq schemas/infer/bnode-duplicator.rq
	#cat $(catalogs-dcat-rdf) 2>/dev/null > workspace/catalog-raw.nt
	cat schemas/infer/catalog.ttl | apache-jena/bin/turtle --output=ntriples | cat - $(catalogs-dcat-rdf) 2>/dev/null > workspace/catalog-raw.nt
	./apache-jena/bin/update --data workspace/catalog-raw.nt --update schemas/infer/1.rq --dump > workspace/catalog.0.ttl
	./apache-jena/bin/update --data workspace/catalog.0.ttl --update schemas/infer/2.rq --dump > workspace/catalog.1.ttl
	# 'tree'ify the graph (blank nodes are duplicated if they occur multiple times in object poisition.
	# We should apply this tranformation until no changes are made. For now, just run it a few times.
	./apache-jena/bin/update --data workspace/catalog.1.ttl --update schemas/infer/bnode-duplicator.rq --dump > workspace/catalog.2.ttl
	./apache-jena/bin/update --data workspace/catalog.2.ttl --update schemas/infer/bnode-duplicator.rq --dump > workspace/catalog.3.ttl
	./apache-jena/bin/update --data workspace/catalog.3.ttl --update schemas/infer/bnode-duplicator.rq --dump > workspace/catalog.4.ttl
	./apache-jena/bin/update --data workspace/catalog.4.ttl --update schemas/infer/bnode-duplicator.rq --dump > workspace/catalog.5.ttl
	./apache-jena/bin/update --data workspace/catalog.5.ttl --update schemas/infer/bnode-duplicator.rq --dump > workspace/catalog.ttl

workspace/dcat/%/validated.nt: shacl workspace/dcat/%/normalised.nt schemas/dcatapvl.ttl
	./bin/validate.sh $(*F)

workspace/dcat/%/normalised.nt: workspace/dcat/%/original apache-jena bin/normalise.sh
	./bin/normalise.sh $(*F)

workspace/dcat/%/original: catalogs/% ./bin/download.sh
	mkdir -p workspace/dcat/$(*F)
	./bin/download.sh $(^) > $@

schemas/dcatapvl.ttl: schemas/dcatap-normalised.ttl workspace/schema/1.ttl schemas/metadataportal-additional-checks.ttl
	cat workspace/schema/1.ttl schemas/metadataportal-additional-checks.ttl > schemas/dcatapvl.ttl

workspace/schema/1.ttl: apache-jena schemas/dcatap-normalised.ttl schemas/changes/1.rq
	mkdir -p workspace/schema
	./apache-jena/bin/update --data schemas/dcatap-normalised.ttl --update schemas/changes/1.rq --dump > workspace/schema/1.ttl

schemas/dcatap-normalised.ttl: apache-jena schemas/dcatapvl.jsonld
	./apache-jena/bin/riot --formatted=turtle schemas/dcatapvl.jsonld > schemas/dcatap-normalised.ttl

schemas/dcatapvl.jsonld:
	mkdir -p schemas
	wget https://raw.githubusercontent.com/Informatievlaanderen/OSLOthema-metadataVoorServices/validation/release/dcatapvl.jsonld -O schemas/dcatapvl.jsonld

expire:
	#       Mark all tracked catalogs older than a day for processing.
	find catalogs/* -mmin +1440 -exec touch {}  \;

apache-jena:
	./bin/download-jena.sh

shacl:
	# Download TopBraid SHALC validator.
	rm -f shacl
	wget https://repo1.maven.org/maven2/org/topbraid/shacl/1.4.2/shacl-1.4.2-bin.zip
	unzip shacl-1.4.2-bin.zip
	rm shacl-1.4.2-bin.zip
	ln -s shacl-* shacl
	chmod +x shacl/bin/shaclvalidate.sh

# Keep intermediate files for performance.
.PRECIOUS: workspace/dcat/%/original workspace/dcat/%/normalised.nt workspace/dcat/%/dcat.nt workspace/dcat/%/inferred.nt workspace/dcat/%/infer-1.nt workspace/dcat/%/infer-2.nt
# For performance, no need to process old suffix rules.
.SUFFIXES: 
