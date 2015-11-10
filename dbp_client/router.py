"""
The WSGI application. Will route the requests to the appropriate handlers.
"""

from dbp_client import SERVER_PATH, TIMEGATE_PATH, MEMENTO_PATH
from dbp_client.timegate_handler import TimegateHandler
from dbp_client.memento_handler import MementoHandler
from dbp_client.client_handler import ClientHandler


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
    else:
        start_response("404", [])
        return [b"Resource not found."]
