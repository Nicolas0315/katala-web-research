import os
import unittest
from unittest.mock import patch

from katala_web_research.http import HttpResponse
from katala_web_research.providers import BraveSearch, SearxngSearch


class ProviderTests(unittest.TestCase):
    def test_searxng_provider_parses_results(self):
        response = HttpResponse(
            url="http://localhost/search",
            status=200,
            headers={"content-type": "application/json"},
            body=b'{"results":[{"title":"A","url":"https://example.com/a","content":"Alpha"}]}',
        )
        with patch.dict(os.environ, {"KWR_SEARXNG_URL": "http://localhost:8080"}):
            with patch("katala_web_research.providers.fetch_url", return_value=response):
                results = SearxngSearch().search("alpha")

        self.assertEqual(results[0].url, "https://example.com/a")
        self.assertEqual(results[0].source, "searxng")

    def test_brave_provider_parses_results(self):
        response = HttpResponse(
            url="https://api.search.brave.com/res/v1/web/search",
            status=200,
            headers={"content-type": "application/json"},
            body=b'{"web":{"results":[{"title":"B","url":"https://example.com/b","description":"Beta"}]}}',
        )
        with patch.dict(os.environ, {"BRAVE_SEARCH_API_KEY": "test"}, clear=False):
            with patch("katala_web_research.providers.fetch_url", return_value=response):
                results = BraveSearch().search("beta")

        self.assertEqual(results[0].url, "https://example.com/b")
        self.assertEqual(results[0].source, "brave")


if __name__ == "__main__":
    unittest.main()
