"""
The WSGI application. Will route the requests to the appropriate handlers.
"""

from dbpedia_ldf_client import SERVER_PATH, TIMEGATE_PATH,\
    MEMENTO_PATH, TIMEMAP_PATH
from dbpedia_ldf_client.timegate_handler import TimegateHandler
from dbpedia_ldf_client.memento_handler import MementoHandler
from dbpedia_ldf_client.client_handler import ClientHandler
from dbpedia_ldf_client.timemap_handler import TimemapHandler


__author__ = 'Harihar Shankar'


def application(env, start_response):
    """
    the router.
    :param env:
    :param start_response:
    :return:
    """

req_path = env.get("PATH_INFO", "/")

    if not req_path.startswith("/"):
        req_path = "/" + req_path

    req_path = req_path.replace(SERVER_PATH, "")

    if req_path == "/":
        client_handler = ClientHandler(env, start_response)
        return client_handler.handle()
    elif req_path.startswith(TIMEGATE_PATH):
        ldf_handler = TimegateHandler(env, start_response)
        return ldf_handler.handle()
    elif req_path.startswith(MEMENTO_PATH):
        memento_handler = MementoHandler(env, start_response)
        return memento_handler.handle()
    elif req_path.startswith(TIMEMAP_PATH):
        timemap_handler = TimemapHandler(env, start_response)
        return timemap_handler.handle()
    else:
        start_response("404", [])
        return [b"Resource not found."]
