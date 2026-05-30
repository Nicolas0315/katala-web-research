import unittest

from katala_web_research.http import HttpResponse


class HttpResponseTextTests(unittest.TestCase):
    def test_unknown_charset_falls_back_to_utf8(self):
        response = HttpResponse(
            url="https://example.com",
            status=200,
            headers={"content-type": "text/html; charset=x-bogus-codec"},
            body="café".encode("utf-8"),
        )

        self.assertEqual(response.text, "café")

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
