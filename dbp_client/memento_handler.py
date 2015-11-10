"""
Displays the memento page of a dbpedia resource.
"""

from urllib.parse import urlparse, unquote, parse_qs, quote
import rdflib
from dbp_client import logging, LDF_MEMENTO_URL,\
    NAMESPACES, LITERAL_TEMPLATE, URI_TEMPLATE, ROW_TEMPLATE, HTML_TEMPLATE
import re


__author__ = 'Harihar Shankar'


class MementoHandler(object):
    """
    Displays the memento page of a dbpedia resource.
    """

    def __init__(self, env, start_response):
        self.env = env
        self.start_response = start_response
        self.host = env.get("UWSGI_ROUTER") + "://" + env.get("HTTP_HOST")
        self.dbp_re = re.compile('/[0-9]{4,14}/http://dbpedia.org/(data|page)/(.+?)(\\.(rdf|html|n3|json|xml))?$')

    def handle(self):
        mem_path = self.env.get("REQUEST_URI")
        mem_path = mem_path.split("/memento/")[1]

        mem_url = LDF_MEMENTO_URL % mem_path

        logging.info("mem url: %s" % mem_url)
        subject_url = parse_qs(urlparse(mem_url).query).get("subject")[0]
        subject_url = unquote(subject_url)
        logging.info("subj url " + subject_url)

        graph = rdflib.Graph()
        graph.load(mem_url, format="n3")

        logging.info("graph is of length: %s" % len(graph))

        subject_ref = rdflib.URIRef(subject_url)
        mem_ref = rdflib.URIRef(mem_url)

        try:
            next_page = next(graph.objects(mem_ref,
                                        NAMESPACES.get("hydra")["nextPage"]))
        except StopIteration:
            next_page = None

        logging.info("next page: " + str(next_page))
        while next_page:
            g = rdflib.Graph()
            g.load(next_page, format="n3")
            try:
                subset_url = next(g.objects(mem_ref,
                                            NAMESPACES.get("void")["subset"]))
                next_page = next(g.objects(rdflib.URIRef(subset_url),
                                        NAMESPACES.get("hydra")["nextPage"]))
            except StopIteration:
                next_page = None

            graph += [(s, p, MementoHandler.url_fix(o)) for s, p, o in g]

        logging.info("graph is of length: %s" % len(graph))

        abstract = [abst for abst in graph.objects(
            subject_ref, NAMESPACES["rdflib"]["comment"])]
        if not abstract:
            abstract = [abst for abst in graph.objects(
                subject_ref, NAMESPACES["dbpprop"]["abstract"])]

        try:
            abstract = abstract[0]
        except IndexError:
            abstract = ""

        table = []
        row_count = 1
        ns_by_uri = {}
        for pref, ns in NAMESPACES.items():
            ns_by_uri[ns] = pref

        po = {}
        for predicate, obj in graph.predicate_objects(subject_ref):
            if not po.get(predicate):
                po[predicate] = []
            p_prefix, p_name = MementoHandler.split_uri(str(predicate))
            try:
                ns_prefix = ns_by_uri[rdflib.Namespace(p_prefix)]
            except KeyError:
                raise ValueError(p_prefix)
            if isinstance(obj, rdflib.Literal):
                po[predicate].append(LITERAL_TEMPLATE % {
                    "CLASS": "literal",
                    "DATA": obj
                })
            else:
                po[predicate].append(URI_TEMPLATE % {
                    "CLASS": "uri",
                    "ONT": p_name,
                    "NS": ns_prefix,
                    "URI": str(obj)
                })

        for predicate in po:
            html_links = "".join(po.get(predicate))

            p_prefix, p_name = MementoHandler.split_uri(str(predicate))
            try:
                ns_prefix = ns_by_uri[rdflib.Namespace(p_prefix)]
            except KeyError:
                raise ValueError(p_prefix)
            row = ROW_TEMPLATE % {
                "EVENODD": "even" if row_count % 2 == 0 else "odd",
                "ONT": p_name,
                "NS": ns_prefix,
                "LIS": html_links
            }
            table.append(row)
            row_count += 1

        html_table = "".join(table)
        sub_prefix, subj_name = MementoHandler.split_uri(subject_url)
        table_name = subj_name.replace("_", " ")
        data = HTML_TEMPLATE % {
            "NAME": subj_name,
            "TNAME": table_name,
            "DESC": abstract,
            "TABLE": html_table
        }

        self.start_response("200 OK", [("Content-Type", "text/html")])
        return [data.encode("utf-8")]

    @staticmethod
    def split_uri(uri: str) -> (str, str):
        # given namespaced uri, find base property name
        for n in NAMESPACES.values():
            if uri.startswith(str(n)):
                return str(n), uri[len(str(n)):]

        slsplit = uri.split('/')
        hsplit = slsplit[-1].split('#')
        return uri[:0-len(hsplit[-1])], hsplit[-1]

    @staticmethod
    def url_fix(url: str) -> rdflib.URIRef:

        invalid_chars = ['<', '>', '"', ' ', '{', '}', '|', '\\', '^', '`']

        if not url.startswith("http"):
            return rdflib.Literal(url)

        index = url.rindex("/")
        fixed_url = url.replace("\\", "")

        chars = [True for char in url if char in invalid_chars]
        if True in chars:
            fixed_url = fixed_url[:index] + quote(fixed_url[index:])
        return rdflib.URIRef(fixed_url)
