"""
Proxies requests to the Memento compatible LDF server and prepares the
response. May make multiple queries to the LDF server for one request.
"""


import requests
from urllib.parse import quote, urlparse, unquote
from dbpedia_ldf_client import logging, LDF_TIMEGATE_URL, MEMENTO_PATH, DBPEDIA_VERSIONS
from memento_client import MementoClient
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
        subject_uri = quote(subject_uri)

        accept_dt = self.env.get("HTTP_ACCEPT_DATETIME")  # type: str
        if not bool(accept_dt):
            accept_dt = MementoClient.convert_to_http_datetime(datetime.now())

        logging.info("Fetching response from timegate %s with accept dt %s"
                     % (LDF_TIMEGATE_URL % subject_uri, accept_dt))

        ldf_resp = requests.head(LDF_TIMEGATE_URL % subject_uri,
                                 headers={"Accept-Datetime": accept_dt},
                                 allow_redirects=False)
        """ type: requests.Response """

        loc_url = ldf_resp.headers.get("location")  # type: str
        logging.info("Received Memento URL from TG %s." % loc_url)

        loc_parts = urlparse(loc_url)
        dbp_version = loc_parts.path.split("?")[0]  # type: str
        dbp_version = dbp_version.replace("/", "")
        logging.info("DBPEDIA memento version: " + dbp_version)
        mem_time = DBPEDIA_VERSIONS.get(dbp_version)  # type: str
        if not mem_time:
            raise ValueError

        mem_url = "%s%s/%s/%s" % (self.host, MEMENTO_PATH,
                                  mem_time, unquote(subject_uri))  # type: str

        self.start_response("302", [
            ("Location", mem_url),
            ("Vary", "accept-datetime"),
            ("Link", "<%s>; rel=\"original\"" % original_uri)
        ])
        return []
