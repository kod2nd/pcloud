# -*- coding: utf-8 -*-
import logging
import socket
import _thread
import time

from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer
from urllib.parse import parse_qs
from urllib.parse import urlparse
from webbrowser import open_new

log = logging.getLogger("pcloud")
log.setLevel(logging.INFO)


PORT = 65432
REDIRECT_URL = f"http://localhost:{PORT}/"
AUTHORIZE_URL = "https://my.pcloud.com/oauth2/authorize"


class HTTPServerHandler(BaseHTTPRequestHandler):
    """
    HTTP Server callbacks to handle pCloud OAuth2 redirects
    """

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        parsed_url = urlparse(self.path)
        query = parse_qs(parsed_url.query)
        code = query.get("code")
        if code:
            self.server.access_token = code[0]
            self.server.pc_hostname = query.get("hostname", "api.pcloud.com")[0]
            self.wfile.write(b"<html><h1>You may now close this window.</h1></html>")


class HTTPServerWithAttributes(HTTPServer):
    def __init__(self, *args, **kwargs):
        self.access_token = None
        self.pc_hostname = None
        super().__init__(*args, **kwargs)


class TokenHandler(object):
    """
    Class used to handle pClouds oAuth2
    """

    redirect_url = REDIRECT_URL

    def __init__(self, client_id):
        self._id = client_id
        self.auth_url = f"{AUTHORIZE_URL}?response_type=code&redirect_uri={self.redirect_url}&client_id={self._id}"

    def open_browser(self):
        """Hook which is called before request is handled."""
        open_new(self.auth_url)

    def close_browser(self):
        """Hook which is called after request is handled."""

    def get_access_token(self):
        http_server = HTTPServerWithAttributes(("localhost", PORT), HTTPServerHandler)

        def start_server():
            http_server.handle_request()

        log.info(f"Start token server {PORT}")
        _thread.start_new_thread(start_server, ())
        self.open_browser()
        while not (http_server.access_token and http_server.pc_hostname):
            time.sleep(1)
        self.close_browser()
        http_server.server_close()
        log.info(f"Teardown token server {PORT}")
        return http_server.access_token, http_server.pc_hostname
