import unittest
from unittest.mock import Mock, patch

from katala_web_research.http import FetchError, HttpResponse, fetch_url


class _FakeUrlopenResponse:
    status = 200
    headers = {"content-type": "text/plain"}

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def geturl(self):
        return "https://example.com/"

    def read(self):
        return b"ok"


class HttpResponseTextTests(unittest.TestCase):
    def test_unknown_charset_falls_back_to_utf8(self):
        response = HttpResponse(
            url="https://example.com",
            status=200,
            headers={"content-type": "text/html; charset=x-bogus-codec"},
            body="café".encode("utf-8"),
        )

        self.assertEqual(response.text, "café")


class FetchUrlTests(unittest.TestCase):
    def test_env_timeout_is_used_when_timeout_is_not_explicit(self):
        opener = Mock(return_value=_FakeUrlopenResponse())
        with patch.dict("os.environ", {"KWR_HTTP_TIMEOUT_SECONDS": "3.5"}, clear=False):
            with patch("katala_web_research.http.urlopen", opener):
                fetch_url("https://example.com/")

        self.assertEqual(opener.call_args.kwargs["timeout"], 3.5)

    def test_explicit_timeout_overrides_env_timeout(self):
        opener = Mock(return_value=_FakeUrlopenResponse())
        with patch.dict("os.environ", {"KWR_HTTP_TIMEOUT_SECONDS": "3.5"}, clear=False):
            with patch("katala_web_research.http.urlopen", opener):
                fetch_url("https://example.com/", timeout=8)

        self.assertEqual(opener.call_args.kwargs["timeout"], 8)

    def test_invalid_env_timeout_raises_fetch_error_before_request(self):
        opener = Mock(return_value=_FakeUrlopenResponse())
        with patch.dict("os.environ", {"KWR_HTTP_TIMEOUT_SECONDS": "0"}, clear=False):
            with patch("katala_web_research.http.urlopen", opener):
                with self.assertRaises(FetchError):
                    fetch_url("https://example.com/")

        opener.assert_not_called()

    def test_declared_charset_is_honored(self):
        response = HttpResponse(
            url="https://example.com",
            status=200,
            headers={"content-type": "text/plain; charset=latin-1"},
            body="café".encode("latin-1"),
        )

        self.assertEqual(response.text, "café")


if __name__ == "__main__":
    unittest.main()
