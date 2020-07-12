from asyncio.transports import Transport
from http.client import HTTPMessage
from typing import Generator
from unittest.mock import Mock, create_autospec, patch

import pytest

from sockit.server import (
    InvalidSecWebsocketKey,
    WebSocketServer,
    generate_handshake_response,
    generate_sec_server_accept_key,
)
from sockit.utils import HTTPRequest


class TestWebsocketServer:
    @pytest.fixture()
    def transport(self) -> Mock:
        transport_mock = create_autospec(Transport, spec_set=True)
        transport_mock.get_extra_info.side_effect = lambda key: {
            "peername": "test-peer"
        }[key]
        return transport_mock

    @pytest.fixture()
    def future(self) -> Mock:
        return Mock()

    @pytest.fixture(autouse=True)
    def mock_ensure_future(self, future: Mock) -> Generator[Mock, None, None]:
        with patch("asyncio.ensure_future") as mock:
            mock.return_value = future
            yield mock

    @pytest.fixture()
    def handshake_response(self) -> Generator[bytes, None, None]:
        response = b"test-response"
        with patch("sockit.server.generate_handshake_response") as mock:
            mock.return_value = response
            yield response

    def test_connection_made(self, future: Mock, transport: Mock) -> None:
        server = WebSocketServer()

        server.connection_made(transport)

        assert server.initialised is False
        assert server.transport == transport
        assert server._future == future

    def test_peername_return_none(self) -> None:
        server = WebSocketServer()

        assert server.peername is None

    def test_peername_return_str_when_connection_was_made(
        self, transport: Mock
    ) -> None:
        server = WebSocketServer()

        server.connection_made(transport)

        assert server.peername == "test-peer"

    def test_finalise_handshake_when_transport_is_none(self,) -> None:
        server = WebSocketServer()

        server.finalise_handshake(b"12345")

        assert server.initialised is False

    def test_finalise_handshake(
        self, handshake_response: Mock, transport: Mock
    ) -> None:
        server = WebSocketServer()
        server.transport = transport

        server.finalise_handshake(b"12345")

        assert server.initialised is True
        transport.write.assert_called_once_with(handshake_response)

    def test_data_received_not_initialised(self) -> None:
        server = WebSocketServer()
        server.initialised = False
        data = b"12345"

        with patch.object(
            server, "finalise_handshake"
        ) as mock_finalise_handshake:
            server.data_received(data)
            mock_finalise_handshake.assert_called_once_with(data)

    def test_data_received_initialised(self) -> None:
        server = WebSocketServer()
        server.initialised = True

        with patch.object(
            server, "finalise_handshake"
        ) as mock_finalise_handshake:
            server.data_received(b"12345")
            mock_finalise_handshake.assert_not_called()

    def test_connection_lost(self, future: Mock, transport: Mock) -> None:
        server = WebSocketServer()
        server._future = future
        server.transport = transport

        server.connection_lost(Exception())

        future.cancel.assert_called_once()
        transport.close.assert_called_once()

    def test_connection_lost_transport_and_future_are_none(self) -> None:
        server = WebSocketServer()

        server.connection_lost(Exception())

        assert server._future is None
        assert server.transport is None


class TestGenerateHandshakeResponse:
    @property
    def client_key(self) -> str:
        return "test-client-key"

    @pytest.fixture
    def http_request(self) -> HTTPRequest:
        headers = HTTPMessage()
        headers.add_header("Sec-WebSocket-Key", self.client_key)
        _request = HTTPRequest()
        _request.headers = headers
        return _request

    @pytest.fixture
    def mock_generate_sec_server_accept_key(
        self,
    ) -> Generator[Mock, None, None]:
        with patch("sockit.server.generate_sec_server_accept_key") as _mock:
            _mock.return_value = "test-server-key"
            yield _mock

    def test_generate_handshake_response(
        self,
        mock_generate_sec_server_accept_key: Mock,
        http_request: HTTPRequest,
    ) -> None:

        assert generate_handshake_response(http_request) == (
            b"HTTP/1.1 101 Switching Protocols\r\n"
            b"Upgrade: websocket\r\n"
            b"Connection: Upgrade\r\n"
            b"Sec-WebSocket-Accept: test-server-key\r\n\r\n"
        )
        mock_generate_sec_server_accept_key.assert_called_once_with(
            self.client_key
        )

    def test_generate_handshake_response_raise_key_error(
        self, http_request: HTTPRequest,
    ) -> None:
        http_request.headers = HTTPMessage()
        with pytest.raises(InvalidSecWebsocketKey):
            generate_handshake_response(http_request)

    def test_generate_sec_server_accept_key(self) -> None:
        accept_key = generate_sec_server_accept_key(self.client_key)

        assert accept_key == "xJtip0qWlpVJ1T9gWf+E1PvhNSc="
