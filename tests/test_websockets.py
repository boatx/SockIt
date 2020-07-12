from sockit.websockets import (
    WebsocketHeader,
    WebsocketRequest,
    WebsocketResponse,
)


class TestWebsocketHeader:
    def test_init(self):
        data = b"abcd"

        header = WebsocketHeader(data)

        assert header._as_byte == b"ab"

    def test_init_data_less_than_two_bytes(self):
        data = b"a"

        header = WebsocketHeader(data)

        assert header._as_byte == b"a"

    def test_init_data_empty(self):
        data = b""

        header = WebsocketHeader(data)

        assert header._as_byte == b""

    def test_bit_fields(self):
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
    pass
