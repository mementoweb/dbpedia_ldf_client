"""
Proxies requests to the Memento compatible LDF server and prepares the
response. May make multiple queries to the LDF server for one request.
"""


import requests
from urllib.parse import quote, urlparse
from dbp_client import logging, LDF_TIMEGATE_URL, MEMENTO_PATH
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
        self.host = env.get("UWSGI_ROUTER") + "://" + env.get("HTTP_HOST")

    def handle(self):
        req_uri = self.env.get("REQUEST_URI")
        subject_uri = req_uri.split("/timegate/")[1]
        subject_uri = quote(subject_uri)

        original_uri = self.host + req_uri

        accept_dt = self.env.get("HTTP_ACCEPT_DATETIME")
        if not bool(accept_dt):
            accept_dt = MementoClient.convert_to_http_datetime(datetime.now())

        logging.info("Fetching response from timegate %s with accept dt %s"
                     % (LDF_TIMEGATE_URL % subject_uri, accept_dt))

        ldf_resp = requests.head(LDF_TIMEGATE_URL % subject_uri,
                                 headers={"Accept-Datetime": accept_dt},
                                 allow_redirects=False)
        loc_url = ldf_resp.headers.get("location")
        logging.info("Received Memento URL from TG %s." % loc_url)

        loc_parts = urlparse(loc_url)
        mem_url = "%s%s%s" % (self.host, MEMENTO_PATH, loc_parts.path)
        if bool(loc_parts.query):
            mem_url += "?" + loc_parts.query

        self.start_response("303", [
            ("Location", mem_url),
            ("Vary", "accept-datetime"),
            ("Link", "<%s>; rel=\"original\"" % original_uri)
        ])
        return []
