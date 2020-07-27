from http.server import BaseHTTPRequestHandler
from io import BytesIO
from typing import Optional


class HTTPRequest(BaseHTTPRequestHandler):
    def __init__(self, request_text: bytes = b"") -> None:
        self.rfile: BytesIO = BytesIO(request_text)
        self.raw_requestline: bytes = self.rfile.readline()
        self.error_code: Optional[int] = None
        self.error_message: Optional[str] = None
        self.explain: Optional[str] = None
        self.parse_request()

    def send_error(
        self,
        code: int,
        message: Optional[str] = None,
        explain: Optional[str] = None,
    ) -> None:
        self.error_code = code
        self.error_message = message
        self.explain = explain
