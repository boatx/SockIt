import asyncio
import base64
import hashlib
import logging
import time
from asyncio import Future
from asyncio.transports import Transport
from typing import Optional

from sockit.utils import HTTPRequest
from sockit.websockets import WebsocketRequest, WebsocketResponse

LOGGER = logging.getLogger(__name__)


_minimal_http_version = "1.1"
_magic_string = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
_accept_connection_response_template = (
    "HTTP/1.1 101 Switching Protocols\r\n"
    "Upgrade: websocket\r\n"
    "Connection: Upgrade\r\n"
    "Sec-WebSocket-Accept: {}\r\n\r\n"
)


class InvalidSecWebsocketKey(Exception):
    pass


def generate_sec_server_accept_key(sec_client_key: str) -> str:
    sec_server_accept_key = f"{sec_client_key}{_magic_string}"
    sec_server_accept_key_hash = hashlib.sha1(sec_server_accept_key.encode())
    return base64.b64encode(sec_server_accept_key_hash.digest()).decode()


def generate_handshake_response(request: HTTPRequest) -> bytes:
    sec_websocket_key = request.headers["Sec-WebSocket-Key"]
    if not sec_websocket_key:
        raise InvalidSecWebsocketKey()
    sec_client_key = request.headers["Sec-WebSocket-Key"]
    sec_server_key = generate_sec_server_accept_key(sec_client_key)
    return _accept_connection_response_template.format(sec_server_key).encode()


class WebSocketServer(asyncio.Protocol):
    def __init__(self) -> None:
        self.initialised: bool = False
        self.transport: Optional[Transport] = None
        self._future: Optional[Future[None]] = None

    def connection_made(self, transport: Transport) -> None:  # type: ignore
        self.transport = transport
        LOGGER.info("Connection from %s", self.peername)

    @property
    def peername(self) -> Optional[str]:
        if self.transport:
            return self.transport.get_extra_info("peername")
        return None

    def finalise_handshake(self, data: bytes) -> None:
        if not self.transport:
            return None
        request = HTTPRequest(data)
        response = generate_handshake_response(request)
        self.transport.write(response)
        self.initialised = True
        self._future = asyncio.ensure_future(self.writer(self.transport))

    def data_received(self, data: bytes) -> None:
        if not self.initialised:
            return self.finalise_handshake(data)
        request = WebsocketRequest(data)
        payload = request.payload()
        LOGGER.info("Received data: %s", payload.decode())

    def connection_lost(self, exc: Optional[Exception]) -> None:
        LOGGER.info("Connection from %s close", self.peername)
        LOGGER.warning("exc=%s", exc)
        if self._future:
            self._future.cancel()
        if self.transport:
            self.transport.close()

    async def writer(self, transport: Transport) -> None:
        try:
            while True:
                message = f"server message: {time.time()}"
                response = WebsocketResponse(message).response()
                transport.write(response)
                await asyncio.sleep(5)
        except Exception:
            LOGGER.exception("Error, closing")
            transport.close()
