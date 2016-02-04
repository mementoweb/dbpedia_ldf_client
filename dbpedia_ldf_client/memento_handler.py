"""
Displays the memento page of a dbpedia resource.
"""

from urllib.parse import unquote, quote
import rdflib
from dbpedia_ldf_client import logging, LDF_MEMENTO_URL, MEMENTO_PATH, \
    NAMESPACES, LITERAL_TEMPLATE, URI_TEMPLATE,\
    ROW_TEMPLATE, HTML_TEMPLATE, DBPEDIA_VERSIONS, SERIALIZERS, TIMEGATE_PATH,\
    TIMEMAP_PATH
import re
from datetime import datetime
from typing import List

__author__ = 'Harihar Shankar'


class MementoHandler(object):
    """
    Displays the memento page of a dbpedia resource.
    """

    def __init__(self, env, start_response):
        self.env = env
        self.start_response = start_response
        self.host = env.get("UWSGI_ROUTER", "http") + "://" + env.get("HTTP_HOST")
        self.dbp_re = re.compile('([0-9]{4,14})/http://dbpedia.org/(data|page)/(.+?)(\\.(rdf|html|n3|json|xml))?$')

    def handle(self):
        mem_path = self.env.get("REQUEST_URI")
        mem_path = mem_path.split(MEMENTO_PATH + "/")[1]

        logging.info("mem path: " + mem_path)
        match = self.dbp_re.match(mem_path)
        response_ct = ""  # type: str
        if match:
            (mem_dt, res, subject, ct_type, supported_ct) = match.groups()
            logging.info("groups: %s, %s, %s, %s, %s" %
                         (mem_dt, res, subject, ct_type, supported_ct))
            response_ct = MementoHandler.get_content_type(res,
                                                          ct_type,
                                                          supported_ct,
                                                          self.env.get("HTTP_ACCEPT"))
        else:
            self.start_response("404", [("Content-Type", "text/html")])
            return [b'Resource Not Found!']

        subject_url = "http://dbpedia.org/resource/%s" % subject  # type: str
        req_subject_url = "http://dbpedia.org/%s/%s" % (res, subject)  # type: str
        logging.info("subj url " + subject_url)
        db_version, mem_dt = MementoHandler.get_db_version(mem_dt)
        logging.info("db version: " + db_version)

        mem_url = LDF_MEMENTO_URL % (db_version, quote(subject_url))
        # type: str
        logging.info("mem url: %s" % mem_url)

        graph = MementoHandler.get_graph(mem_url)
        subject_ref = rdflib.URIRef(subject_url)

        if response_ct == "html":
            data = MementoHandler.serialize_to_html(graph, subject_ref)
            data = data.encode("utf-8")
        else:
            sub_graph = rdflib.Graph()
            sub_po = graph.predicate_objects(subject_ref)
            sub_g = [(subject_ref, p, MementoHandler.url_fix(o))
                     for p, o in sub_po]

            for sub in sub_g:
                sub_graph.add(sub)
            resp_format = response_ct if response_ct != "rdfxml" else "xml"
            data = sub_graph.serialize(format=resp_format)

        link_header = self.create_link_header(req_subject_url,
                                              MementoHandler.get_http_date(mem_dt))
        self.start_response("200 OK",
                            [
                                ("Content-Type", SERIALIZERS.get(response_ct)),
                                ("Link", link_header),
                                ("Memento-Datetime", MementoHandler.get_http_date(mem_dt))
                             ])
        return [data]

    @staticmethod
    def get_http_date(date_str: str) -> str:
        dt = datetime.strptime(date_str, "%Y%m%d%H%M%S")
        return dt.strftime("%a, %d %b %Y %H:%M:%S GMT")

    def create_link_header(self, subject_url: str, mem_dt: str) -> str:
        link_tmpl = "<%s>; rel=\"%s\""
        link_header = []  # type: List[str]
        link_header.append(link_tmpl % (subject_url, "original"))

        mem_url = self.host + self.env.get("REQUEST_URI")
        link_header.append(link_tmpl % (mem_url, "memento") +
                           "; datetime=\"" + mem_dt + "\"")

        tg_url = self.host + TIMEGATE_PATH + "/" + subject_url
        link_header.append(link_tmpl % (tg_url, "timegate"))

        tm_url = self.host + TIMEMAP_PATH + "/link/" + subject_url
        link_header.append(link_tmpl % (tm_url, "timemap"))

        return ", ".join(link_header)

    @staticmethod
    def serialize_to_html(graph: rdflib.Graph, subject_ref: rdflib.URIRef)\
            -> str:
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

        pred_obj = list(graph.predicate_objects(subject_ref))
        pred_obj.sort()

        po = {}
        for predicate, obj in pred_obj:
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
                    "URI": unquote(str(obj).replace("\\", ""))
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
        sub_prefix, subj_name = MementoHandler.split_uri(str(subject_ref))
        table_name = subj_name.replace("_", " ")
        data = HTML_TEMPLATE % {
            "NAME": subj_name,
            "TNAME": table_name,
            "DESC": abstract,
            "TABLE": html_table
        }
        return data


    @staticmethod
    def get_graph(mem_url: str) -> rdflib.Graph:
        graph = rdflib.Graph()
        graph.load(mem_url, format="n3")
        logging.info("graph is of length: %s" % len(graph))

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
        return graph

    @staticmethod
    def get_db_version(mem_dt: str) -> (str, str):
        for dbv in DBPEDIA_VERSIONS:
            if DBPEDIA_VERSIONS.get(dbv).startswith(mem_dt):
                return dbv, DBPEDIA_VERSIONS.get(dbv)
        # TODO: choose the latest memento
        db_version = list(DBPEDIA_VERSIONS.keys())[-1]
        return db_version, DBPEDIA_VERSIONS.get(db_version)

    @staticmethod
    def get_content_type(res: str, ct_type: str, supported_ct: str,
                         accept: str) -> str:
        response_ct = "n3"
        if res == "page":
            response_ct = "html"
        elif accept and accept in SERIALIZERS.values():
            for ct in SERIALIZERS:
                if accept == SERIALIZERS.get(ct):
                    response_ct = ct
                    break
        elif not ct_type:
            response_ct = "xml"
        elif supported_ct == "xml":
            response_ct = "xml"
        else:
            response_ct = supported_ct

        if response_ct not in SERIALIZERS:
            response_ct = "n3"

        return response_ct

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
