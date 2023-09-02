from unittest.mock import patch

from sockit.utils import HTTPRequest


class TestHttpRequest:
    def test_init(self) -> None:
        request_text = b"test"

        http_request = HTTPRequest(request_text=request_text)

        assert http_request.raw_requestline == request_text

    def test_init_default_params(self) -> None:
        http_request = HTTPRequest()

        assert http_request.raw_requestline == b""

    def test_init_call_parse_request(self) -> None:
        with patch.object(HTTPRequest, "parse_request") as mock_parse_request:
            HTTPRequest()
            mock_parse_request.assert_called_once_with()
