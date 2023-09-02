import ctypes
import logging
from typing import NamedTuple, Optional

LOGGER = logging.getLogger(__name__)


class WebsocketHeader(ctypes.Union):
    class _FlagBits(ctypes.BigEndianStructure):
        _fields_ = [
            ("fin", ctypes.c_uint8, 1),
            ("rsv1", ctypes.c_uint8, 1),
            ("rsv2", ctypes.c_uint8, 1),
            ("rsv3", ctypes.c_uint8, 1),
            ("opcode", ctypes.c_uint8, 4),
            ("mask", ctypes.c_uint8, 1),
            ("payload_length", ctypes.c_uint8, 7),
        ]

        def __str__(self) -> str:
            return " ".join(
                [
                    f"{field_name}={getattr(self, field_name)},"
                    for field_name, *_ in self._fields_
                ]
            )

    _anonymous_ = ("_bits",)
    _fields_ = [("_bits", _FlagBits), ("_as_byte", ctypes.c_char * 2)]

    def __init__(self, data: bytes = b"") -> None:
        self._as_byte = data[0:2]

    def __str__(self) -> str:
        return f"WebsocketHeader({self._bits})"


class WebsocketRequest:
    def __init__(self, data: bytes) -> None:
        self.header = WebsocketHeader(data)
        LOGGER.info("Received request: %s", self.header)
        self.data = data
        self.start_byte = 2
        self.length = self._get_length()
        self.mask = self._get_mask()

    def _get_length(self) -> int:
        length = self.header.payload_length
        if length < 126:
            return length
        if length == 126:
            self.start_byte = 4
            return int.from_bytes(self.data[2:4], byteorder="big")
        if length == 127:
            self.start_byte = 10
            return int.from_bytes(self.data[2:10], byteorder="big")
        raise ValueError("Invalid Header")

    def _get_mask(self) -> Optional[bytes]:
        if not self.header.mask:
            return None
        end_byte = self.start_byte + 4
        mask = self.data[self.start_byte : end_byte]
        self.start_byte = end_byte
        return mask

    def payload(self) -> bytes:
        end_byte = self.length + self.start_byte
        payload = self.data[self.start_byte : end_byte]
        if not self.mask:
            return payload
        bytes_list = (self.mask[i % 4] ^ b for i, b in enumerate(payload))
        return b"".join((i.to_bytes(1, "big") for i in bytes_list))


class Length(NamedTuple):
    header: int
    as_byte: bytes


class WebsocketResponse:
    def __init__(self, payload: str) -> None:
        self.payload = payload.encode()
        self.length = self._get_length()
        self.header = self._get_header()

    def _get_header(self) -> WebsocketHeader:
        header = WebsocketHeader()
        header.fin = 1
        header.opcode = 1
        header.payload_length = self.length.header
        header.mask = 0
        return header

    def _get_length(self) -> Length:
        length = len(self.payload)
        if length < 126:
            return Length(length, b"")
        if length < 65536:
            return Length(126, length.to_bytes(2, "big"))
        return Length(127, length.to_bytes(8, "big"))

    def response(self) -> bytes:
        return self.header._as_byte + self.length.as_byte + self.payload
