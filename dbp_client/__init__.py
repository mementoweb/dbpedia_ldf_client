"""
"""

import logging
import rdflib
import os

__author__ = 'Harihar Shankar'


SERVER_PATH = "/dbpedia"
TIMEGATE_PATH = "/timegate"
MEMENTO_PATH = "/memento"

LDF_TIMEGATE_URL = "http://labs.mementoweb.org/timegate/dbpedia?subject=%s"
LDF_MEMENTO_URL = "http://labs.mementoweb.org/%s"

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
