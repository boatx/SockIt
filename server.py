import asyncio
import base64
import hashlib
import logging
import time

from utils import HTTPRequest
from ws import WebsocketRequest, WebsocketResponse


log = logging.getLogger(__name__)


_minimal_http_version = '1.1'
_magic_string = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
_accept_connection_response = '''HTTP/1.1 101 Switching Protocols\r
Upgrade: websocket\r
Connection: Upgrade\r
Sec-WebSocket-Accept: {}\r\n\r\n'''


def generate_sec_server_accept_key(sec_client_key):
    sec_server_accept_key = '{}{}'.format(sec_client_key, _magic_string)
    sec_server_accept_key = hashlib.sha1(sec_server_accept_key.encode())
    return base64.b64encode(sec_server_accept_key.digest()).decode()


def generate_handshake_response(request):
    sec_client_key = request.headers['Sec-WebSocket-Key']
    sec_server_key = generate_sec_server_accept_key(sec_client_key)
    return _accept_connection_response.format(sec_server_key).encode()


class WebSocketServer(asyncio.Protocol):
    def connection_made(self, transport):
        self.peername = transport.get_extra_info('peername')
        self.transport = transport
        log.info('Connection from {}'.format(self.peername))
        self.initialised = False
        self._future = asyncio.async(self.writer())
        asyncio.wait_for(self._future, 60)

    def finalise_handshake(self, data):
        request = HTTPRequest(data)
        response = generate_handshake_response(request)
        self.transport.write(response)
        self.initialised = True

    def data_received(self, data):
        if not self.initialised:
            self.finalise_handshake(data)
        else:
            request = WebsocketRequest(data)
            payload = request.payload()
            payload = ''.join([chr(i) for i in payload])
            log.info('Received data: {}'.format(payload))

    def connection_lost(self, exc):
        log.info('Connection from {} close'.format(self.peername))
        self._future.cancel()
        self.transport.close()

    async def writer(self):
        try:
            while True:
                if self.initialised:
                    message = 'server message: {}'.format(time.time())
                    response = WebsocketResponse(message).response()
                    self.transport.write(response)
                await asyncio.sleep(5)
        except Exception as e:
            log.error('{} {}'.format(e, e.msg))
            self.transport.close()
