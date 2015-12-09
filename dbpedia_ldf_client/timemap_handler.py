"""
Handles TimeMap requests and responses. Uses the ldfserver config file to build
timemaps.
"""

from dbpedia_ldf_client import DBPEDIA_VERSIONS, TIMEGATE_PATH,\
    TIMEMAP_PATH, logging, MEMENTO_PATH
from typing import List, Dict
import re
from datetime import datetime
from memento_client import MementoClient


__author__ = 'Harihar Shankar'


class TimemapHandler(object):

    def __init__(self, env, start_response):
        self.env = env
        self.start_response = start_response
        self.host = env.get("UWSGI_ROUTER", "http") + "://" + env.get("HTTP_HOST")
        self.tm_re = re.compile('(link|json)/http://dbpedia.org/data|page/(.+?)\\.rdf|html|n3|json|xml?$')

    def handle(self):
        mem_path = self.env.get("REQUEST_URI")
        mem_path = mem_path.split(TIMEMAP_PATH)[1]

        logging.info("mem path: " + mem_path)
        match = self.tm_re.match(mem_path)
        if match:
            (tm_type, subject) = match.groups()
            logging.info("groups: %s, %s" % (tm_type, subject))
        else:
            self.start_response("404", [("Content-Type", "text/html")])
            return [b'Resource Not Found!']

        subject_url = "http://dbpedia.org/resource/%s" % subject  # type: str
        logging.info("subj url " + subject_url)

        mem_dts = DBPEDIA_VERSIONS.values()  # type: List[str]
        timemap = {}  # type: Dict[str, List[Dict[str, str]]]
        timemap["memento"] = []
        mem_url_tmpl = self.host + MEMENTO_PATH + "/%s/%s"
        for mem_dt in mem_dts:
            dt = datetime.strptime(mem_dt, "%Y%m%d%H%M%S")
            mem_url = mem_url_tmpl % (mem_dt, subject_url)
            timemap["memento"].append(
                {
                    "uri": mem_url,
                    "datetime": MementoClient.convert_to_http_datetime(dt)
                 })

        timemap["timegate"].append(
            {"uri": self.host + TIMEGATE_PATH + "/" + subject_url})
        timemap["original"].append({"uri": subject_url})
        timemap["self"].append(
            {"uri": self.host + self.env.get("REQUEST_URI"),
             "type": "application/link-header"}
        )

        tm = self.create_link_timemap(timemap)
        return []

    def create_link_timemap(self, timemap: Dict[str, List[Dict[str, str]]]) -> str:
        link_tmpl = "<%s>; rel=\"%s\""
        link_header = []
        for rel in timemap:
            for link in timemap.get(rel):
                link_val = link_tmpl % (link.get("uri"), rel)
                for attr in link:
                    if attr != "uri":
                        link_val += "; " + attr + "=" + link.get(attr)
                link_header.append(link_val)
        return ",".join(link_header)

    def create_link_header(self, subject_url: str) -> str:
        link_tmpl = "<%s>; rel=\"%s\""
        link_header = []  # type: List[str]
        link_header.append(link_tmpl % (subject_url, "original"))

        mem_url = self.host + self.env.get("REQUEST_URI")
        link_header.append(link_tmpl % (mem_url, "memento"))

        tg_url = self.host + TIMEGATE_PATH + "/" + subject_url
        link_header.append(link_tmpl % (tg_url, "timegate"))
        return ",".join(link_header)

