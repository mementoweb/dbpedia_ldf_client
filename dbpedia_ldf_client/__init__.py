"""
"""

import logging
import rdflib
import os
import json
from typing import Dict

__author__ = 'Harihar Shankar'


SERVER_PATH = "/dbpedia"
TIMEGATE_PATH = "/timegate"
MEMENTO_PATH = "/memento"
TIMEMAP_PATH = "/timemap"

LDF_TIMEGATE_URL = "http://localhost:3000/timegate/dbpedia?subject=%s"
LDF_MEMENTO_URL = "http://localhost:3000/%s?subject=%s"
LDF_CONFIG_PATH = "config/config-memento-dbpedia.json"

NAMESPACES = {
    "dbpedia": rdflib.Namespace("http://dbpedia.org/ontology/"),
    "hydra": rdflib.Namespace("http://www.w3.org/ns/hydra/core#"),
    "dcterms": rdflib.Namespace("http://purl.org/dc/terms/"),
    "rdf": rdflib.Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#"),
    "rdflib": rdflib.Namespace("http://www.w3.org/2000/01/rdf-schema#"),
    "owl": rdflib.Namespace("http://www.w3.org/2002/07/owl#"),
    "skos": rdflib.Namespace("http://www.w3.org/2004/02/skos/core#"),
    "xsd": rdflib.Namespace("http://www.w3.org/2001/XMLSchema#"),
    "dc": rdflib.Namespace("http://purl.org/dc/terms/"),
    "dc11": rdflib.Namespace("http://purl.org/dc/elements/1.1/"),
    "foaf": rdflib.Namespace("http://xmlns.com/foaf/0.1/"),
    "geo": rdflib.Namespace("http://www.w3.org/2003/01/geo/wgs84_pos#"),
    "dbpedia-owl": rdflib.Namespace("http://dbpedia.org/ontology/"),
    "dbpprop": rdflib.Namespace("http://dbpedia.org/property/"),
    "void": rdflib.Namespace("http://rdfs.org/ns/void#"),
    "georss": rdflib.Namespace("http://www.georss.org/georss/"),
    "prov": rdflib.Namespace("http://www.w3.org/ns/prov#"),
    "w3geo": rdflib.Namespace("http://www.w3.org/2003/01/geo/wgs84_pos#"),
    "purl": rdflib.Namespace("http://purl.org/linguistics/gold/")
}


SERIALIZERS = {
    "xml": "application/xml",
    "rdfxml": "application/rdf+xml",
    "n3": "text/n3",
    "turtle": "text/turtle",
    "nt": "application/n-triples",
    "html": "text/html"
}

loglevel = "INFO"
logging.propogate = False

log_level = getattr(logging, loglevel.upper(), None)
logging.basicConfig(level=log_level)

ROW_TEMPLATE = """
<tr class="%(EVENODD)s">
<td class="property">
<a class="uri" href="http://dbpedia.org/ontology/%(ONT)s"><small>%(NS)s:</small>%(ONT)s</a>
</td>
<td>
<ul>
%(LIS)s
</ul>
</td>
</tr>"""

URI_TEMPLATE = """
<li>
<span class="%(CLASS)s">
<a class="%(CLASS)s" rel="%(ONT)s:%(NS)s" href="%(URI)s">%(URI)s</a>
</span>
</li>"""

LITERAL_TEMPLATE = """
<li>
<span class="%(CLASS)s">
%(DATA)s
</span>
</li>"""

fh = open(os.path.join(os.path.dirname(__file__),
                       "../static/dbpedia_template.html"))
HTML_TEMPLATE = fh.read()
fh.close()

ldf_config = json.load(open(LDF_CONFIG_PATH))

DBPEDIA_VERSIONS = {}  # type: Dict[str, str]
try:
    versions = ldf_config.get("timegates").get("mementos").get("dbpedia").get("versions")
except KeyError:
    raise

for version in versions:
    try:
        start = ldf_config.get("datasources").get(version).get("memento").get("interval")[0]
    except KeyError:
        raise
    if not start or start == "":
        raise ValueError

    start = start.replace("-", "")
    start = start.replace(":", "")
    start = start.replace("T", "")
    start = start.replace("Z", "")
    DBPEDIA_VERSIONS[version] = start

# logging.info(DBPEDIA_VERSIONS)
