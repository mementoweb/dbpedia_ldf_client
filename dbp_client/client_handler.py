"""
Displays the dbpedia client home page with a queryable memento user
 interface.
"""

__author__ = 'Harihar Shankar'


class ClientHandler(object):
    """
    Displays the dbpedia client home page with a queryable memento user
     interface.
    """

    def __init__(self, env, start_response):
        self.env = env
        self.start_response = start_response

    def handle(self):
        self.start_response("200 OK", [("Content-Type", "text/html")])
        return [b"ClientHandler!!!!"]
