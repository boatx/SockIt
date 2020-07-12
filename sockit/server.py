import asyncio
import base64
import hashlib
import logging
import time
from asyncio.selector_events import _SelectorSocketTransport

from sockit.utils import HTTPRequest
from sockit.websockets import WebsocketRequest, WebsocketResponse

log = logging.getLogger(__name__)


_minimal_http_version = "1.1"
_magic_string = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
_accept_connection_response_template = """HTTP/1.1 101 Switching Protocols\r
Upgrade: websocket\r
Connection: Upgrade\r
Sec-WebSocket-Accept: {}\r\n\r\n"""


def generate_sec_server_accept_key(sec_client_key: str) -> str:
    sec_server_accept_key = f"{sec_client_key}{_magic_string}"
    sec_server_accept_key = hashlib.sha1(sec_server_accept_key.encode())
    return base64.b64encode(sec_server_accept_key.digest()).decode()


def generate_handshake_response(request: HTTPRequest) -> bytes:
    sec_client_key = request.headers["Sec-WebSocket-Key"]
    sec_server_key = generate_sec_server_accept_key(sec_client_key)
    return _accept_connection_response_template.format(sec_server_key).encode()


class WebSocketServer(asyncio.Protocol):
    def connection_made(self, transport: _SelectorSocketTransport) -> None:
        self.peername = transport.get_extra_info("peername")
        log.info(f"Connection from {self.peername}")
        self.transport = transport
        self.initialised = False
        self._future = asyncio.ensure_future(self.writer())

    def finalise_handshake(self, data: bytes) -> None:
        request = HTTPRequest(data)
        response = generate_handshake_response(request)
        self.transport.write(response)
        self.initialised = True

    def data_received(self, data: bytes) -> None:
        if not self.initialised:
            self.finalise_handshake(data)
            return
        request = WebsocketRequest(data)
        payload = request.payload()
        payload = "".join([chr(i) for i in payload])
        log.info(f"Received data: {payload}")

    def connection_lost(self, exc: Exception) -> None:
        log.info(f"Connection from {self.peername} close")
        log.warning(f"exc={exc}")
        self._future.cancel()
        self.transport.close()

    async def writer(self) -> None:
        try:
            while True:
                if self.initialised:
                    message = f"server message: {time.time()}"
                    response = WebsocketResponse(message).response()
                    self.transport.write(response)
                await asyncio.sleep(5)
        except Exception as e:
            log.error(f"{e} {e.msg}")
            self.transport.close()
