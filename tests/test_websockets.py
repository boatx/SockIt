from typing import Any, NamedTuple
from unittest.mock import create_autospec

import pytest

from sockit.websockets import (
    WebsocketHeader,
    WebsocketRequest,
    WebsocketResponse,
)


def _get_header(header_length: int, mask: int = 0) -> WebsocketHeader:
    header = WebsocketHeader()
    header.fin = 1
    header.opcode = 1
    header.payload_length = header_length
    header.mask = mask
    return header


class WebsocketMessageFixture(NamedTuple):
    data: bytes
    payload: str
    payload_length_bytes: bytes
    header: WebsocketHeader


@pytest.fixture(
    params=[
        (4, 4, b""),
        (125, 125, b""),
        (126, 126, int.to_bytes(126, 2, "big")),
        (65535, 126, int.to_bytes(65535, 2, "big")),
        (65536, 127, int.to_bytes(65536, 8, "big")),
    ],
    ids=lambda fixture_value: f"{fixture_value[0]} character message",
)
def websocket_message(request: Any) -> WebsocketMessageFixture:  # noqa: ANN401
    payload_length, header_length, payload_length_bytes = request.param
    header = _get_header(header_length)
    payload = "".join(("x" for _ in range(payload_length)))
    data = header._as_byte + payload_length_bytes + payload.encode()
    return WebsocketMessageFixture(data, payload, payload_length_bytes, header)


class TestWebsocketHeader:
    def test_init(self) -> None:
        data = b"abcd"

        header = WebsocketHeader(data)

        assert header._as_byte == b"ab"

    def test_init_data_less_than_two_bytes(self) -> None:
        data = b"a"

        header = WebsocketHeader(data)

        assert header._as_byte == b"a"

    def test_init_data_empty(self) -> None:
        data = b""

        header = WebsocketHeader(data)

        assert header._as_byte == b""

    def test_bit_fields(self) -> None:
        data = 0b1010001110101101

        header = WebsocketHeader(data.to_bytes(2, byteorder="big"))

        assert header.fin == 1
        assert header.rsv1 == 0
        assert header.rsv2 == 1
        assert header.rsv3 == 0
        assert header.opcode == 3
        assert header.mask == 1
        assert header.payload_length == 45


class TestWebsocketRequest:
    @pytest.fixture()
    def header(self) -> bytes:
        return _get_header(19, 1)._as_byte

    @pytest.fixture()
    def data(self, header: bytes) -> bytes:
        payload = b"]\x04&X>hO=3p\x06,8wRx0aU+<cC"
        return header + payload

    def test_init(self, data: bytes, header: bytes) -> None:
        request = WebsocketRequest(data)

        assert request.header._as_byte == header
        assert request.data == data
        assert request.mask == data[2:6]
        assert request.start_byte == 6
        assert request.length == 19

    def test_get_payload(self, data: bytes) -> None:
        request = WebsocketRequest(data)

        assert request.payload() == b"client test message"

    def test_get_length(
        self, websocket_message: WebsocketMessageFixture
    ) -> None:
        request = WebsocketRequest(websocket_message.data)
        length = len(websocket_message.payload)

        assert request._get_length() == length
        assert request.length == length

    def test_get_length_raise_value_error_for_invalid_header_payload_length(
        self, data: bytes
    ) -> None:
        request = WebsocketRequest(data)
        request.header = create_autospec(
            request.header, spec_set=True, payload_length=129
        )

        with pytest.raises(ValueError):
            request._get_length()


class TestWebsocketResponse:
    def test_response_payload(self) -> None:
        response = WebsocketResponse("test")

        assert response.payload == b"test"

    def test_response_header(
        self, websocket_message: WebsocketMessageFixture
    ) -> None:
        response = WebsocketResponse(websocket_message.payload)

        assert response.header._as_byte == websocket_message.header._as_byte

    def test_response(
        self, websocket_message: WebsocketMessageFixture
    ) -> None:
        response = WebsocketResponse(websocket_message.payload)

        assert response.response() == websocket_message.data
