import ctypes
import logging


log = logging.getLogger(__name__)


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

        def __str__(self):
            return " ".join(
                ["{}={},".format(f, getattr(self, f)) for f, *_ in self._fields_]
            )

    _anonymous_ = ("_bits",)
    _fields_ = [("_bits", _FlagBits), ("_as_byte", ctypes.c_char * 2)]

    def __init__(self, data=b""):
        self._as_byte = data[0:2]

    def __str__(self):
        return "WebsocketHeader({})".format(self._bits)


class WebsocketRequest:
    def __init__(self, data):
        self.header = WebsocketHeader(data)
        log.info("Received request: {}".format(self.header))
        self.data = data
        self.start_byte = 2
        self.length = self._get_length()
        self.mask = self._get_mask()

    def _get_length(self):
        length = self.header.payload_length
        if length < 126:
            return length

        raise NotImplementedError()

    def _get_mask(self):
        if not self.header.mask:
            return None
        end_byte = self.start_byte + 4
        mask = self.data[self.start_byte : end_byte]
        self.start_byte = end_byte
        return mask

    def payload(self):
        end_byte = self.length + self.start_byte
        payload = self.data[self.start_byte : end_byte]
        if self.mask:
            return [self.mask[i % 4] ^ b for i, b in enumerate(payload)]
        return payload


class WebsocketResponse:
    def __init__(self, payload):
        self.payload = payload.encode()
        self.header = self._get_header()

    def _get_length(self):
        raise NotImplementedError()

    def _get_header(self):
        header = WebsocketHeader()
        header.fin = 1
        header.opcode = 1
        header.payload_length = len(self.payload)
        header.mask = 0
        return header

    def response(self):
        return self.header._as_byte + self.payload
