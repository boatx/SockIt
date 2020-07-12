import pytest

from sockit.websockets import (
    WebsocketHeader,
    WebsocketRequest,
    WebsocketResponse,
)


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
        return int.to_bytes(0b01000000110010011, 2, "big")

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

    def test_get_length(self, data: bytes) -> None:
        request = WebsocketRequest(data)

        assert request._get_length() == 19
        assert request.length == 19

    def test_get_payload(self, data: bytes) -> None:
        request = WebsocketRequest(data)

        assert request.payload() == b"client test message"


class TestWebsocketResponse:
    @pytest.fixture()
    def header(self) -> bytes:
        _header = 0b1000000100000100
        return _header.to_bytes(2, "big")

    def test_response_payload(self) -> None:
        response = WebsocketResponse("test")

        assert response.payload == b"test"

    def test_response_header(self, header: bytes) -> None:
        payload = "test"

        response = WebsocketResponse(payload)

        assert response.header._as_byte == header

    def test_response(self, header: bytes) -> None:
        payload = "test"
        expected_response = header + payload.encode()

        response = WebsocketResponse(payload)

        assert response.response() == expected_response
