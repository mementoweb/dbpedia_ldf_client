"""
Proxies requests to the Memento compatible LDF server and prepares the
response. May make multiple queries to the LDF server for one request.
"""


import requests
from urllib.parse import quote, urlparse, unquote
from dbpedia_ldf_client import logging, LDF_TIMEGATE_URL, MEMENTO_PATH,\
    DBPEDIA_VERSIONS, TIMEMAP_PATH
from memento_client import MementoClient
from dbpedia_ldf_client.memento_handler import MementoHandler
from datetime import datetime

__author__ = 'Harihar Shankar'


class TimegateHandler(object):
    """
    Proxies requests to the Memento compatible LDF server and prepares the
    response. May make multiple queries to the LDF server for one request.
    """

    def __init__(self, env, start_response):
        self.env = env
        self.start_response = start_response
        self.host = env.get("UWSGI_ROUTER", "http") + "://" + env.get("HTTP_HOST")

    def handle(self):
        req_uri = self.env.get("REQUEST_URI")  # type: str
        subject_uri = req_uri.split("/timegate/")[1]  # type: str
        original_uri = subject_uri  # type: str

        # fix for issue #1
        if original_uri.find("dbpedia.org/resource/") > 0:
            ct = MementoHandler.get_content_type("", "", "", self.env.get("HTTP_ACCEPT"))
            if ct == "html":
                new_tg_url = req_uri.replace("dbpedia.org/resource/", "dbpedia.org/page/")
            else:
                new_tg_url = req_uri.replace("dbpedia.org/resource/", "dbpedia.org/data/")

            self.start_response("303", [
                ("Location", self.host + new_tg_url)
            ])
            return []

        subject_uri = quote(subject_uri)
        accept_dt = self.env.get("HTTP_ACCEPT_DATETIME")  # type: str

        if bool(accept_dt):
            try:
                logging.info("Checking validity of acc dt: %s" % accept_dt)
                MementoClient.convert_to_datetime(accept_dt)
            except ValueError:
                logging.info("Invalid acc dt, issuing 400.")
                self.start_response("400", [])
                return ["The requested Accept-Datetime cannot be parsed."]
        else:
            accept_dt = MementoClient.convert_to_http_datetime(datetime.now())

        logging.info("Fetching response from timegate %s with accept dt %s"
                     % (LDF_TIMEGATE_URL % subject_uri, accept_dt))

        ldf_resp = requests.head(LDF_TIMEGATE_URL % subject_uri,
                                 headers={"Accept-Datetime": accept_dt},
                                 allow_redirects=False)
        """ type: requests.Response """

        loc_url = ldf_resp.headers.get("location")  # type: str
        if not loc_url:
            loc_url = ldf_resp.headers.get("content-location")  # type: str
        logging.info("Received Memento URL from TG %s." % loc_url)

        loc_parts = urlparse(loc_url)
        dbp_version = loc_parts.path.split("?")[0]  # type: str
        dbp_version = dbp_version.replace("/", "")
        logging.info("DBPEDIA memento version: " + dbp_version)
        mem_time = DBPEDIA_VERSIONS.get(dbp_version)  # type: str
        if not mem_time:
            raise ValueError

        mem_dt = datetime.strptime(mem_time, "%Y%m%d%H%M%S")
        mem_http_dt = MementoClient.convert_to_http_datetime(mem_dt)
        mem_url = "%s%s/%s/%s" % (self.host, MEMENTO_PATH,
                                  mem_time, unquote(subject_uri))  # type: str

        link_tmpl = "<%s>; rel=\"%s\""
        link_hdr = link_tmpl % (original_uri, "original")
        link_hdr += "," + link_tmpl % (
            self.host + TIMEMAP_PATH + "/link/" + original_uri, "timemap")
        link_hdr += "; type=\"application/link-format\""
        link_hdr += "," + link_tmpl % (mem_url, "memento")
        link_hdr += "; datetime=\"" + mem_http_dt + "\""

        #link_hdr += "," + link_tmpl % (
        #    self.host + TIMEMAP_PATH + "/json/" + original_uri, "timemap")
        #link_hdr += "; type=\"application/json\""

        self.start_response("302", [
            ("Location", mem_url),
            ("Vary", "accept-datetime"),
            ("Link", link_hdr)
        ])
        return []
