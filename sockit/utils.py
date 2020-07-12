from http.server import BaseHTTPRequestHandler
from io import BytesIO
from typing import Optional


class HTTPRequest(BaseHTTPRequestHandler):
    def __init__(self, request_text: Optional[bytes] = b""):
        self.rfile = BytesIO(request_text)
        self.raw_requestline = self.rfile.readline()
        self.error_code = None
        self.error_message = None
        self.parse_request()

    def send_error(self, code, message) -> None:
        self.error_code = code
        self.error_message = message
