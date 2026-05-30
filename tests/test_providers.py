import json
import os
import unittest
from unittest.mock import patch

from katala_web_research.http import FetchError, HttpResponse
from katala_web_research.models import SearchResult
from katala_web_research.providers import BraveSearch, MetaSearch, OpenAlexSearch, SearxngSearch


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

    def test_non_json_response_raises_fetch_error(self):
        # A WAF / rate-limit page returns HTML; the provider must surface it as
        # a FetchError naming the URL, not a bare JSONDecodeError.
        response = HttpResponse(
            url="http://localhost/search",
            status=200,
            headers={"content-type": "text/html"},
            body=b"<html><body>rate limited</body></html>",
        )
        with patch.dict(os.environ, {"KWR_SEARXNG_URL": "http://localhost:8080"}):
            with patch("katala_web_research.providers.fetch_url", return_value=response):
                with self.assertRaises(FetchError):
                    SearxngSearch().search("alpha")

    def test_searxng_provider_passes_optional_parameters(self):
        response = HttpResponse(
            url="http://localhost/search",
            status=200,
            headers={"content-type": "application/json"},
            body=b'{"results":[]}',
        )
        env = {
            "KWR_SEARXNG_URL": "http://localhost:8080",
            "KWR_SEARXNG_CATEGORIES": "general,it",
            "KWR_SEARXNG_ENGINES": "duckduckgo,wikipedia",
            "KWR_SEARXNG_LANGUAGE": "ja",
            "KWR_SEARXNG_TIME_RANGE": "month",
            "KWR_SEARXNG_SAFESEARCH": "1",
        }
        with patch.dict(os.environ, env, clear=False):
            with patch("katala_web_research.providers.fetch_url", return_value=response) as fetch:
                SearxngSearch().search("alpha")

        called_url = fetch.call_args.args[0]
        self.assertIn("categories=general%2Cit", called_url)
        self.assertIn("engines=duckduckgo%2Cwikipedia", called_url)
        self.assertIn("language=ja", called_url)
        self.assertIn("time_range=month", called_url)
        self.assertIn("safesearch=1", called_url)

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

    def test_openalex_provider_parses_work_results(self):
        body = json.dumps(
            {
                "results": [
                    {
                        "id": "https://openalex.org/W1",
                        "doi": "https://doi.org/10.123/example",
                        "display_name": "Query Decomposition for RAG",
                        "publication_year": 2025,
                        "publication_date": "2025-07-01",
                        "type": "article",
                        "cited_by_count": 42,
                        "open_access": {"is_oa": True},
                        "primary_location": {
                            "landing_page_url": "https://aclanthology.org/2025.acl-srw.32/",
                            "source": {"display_name": "ACL Anthology"},
                        },
                        "abstract_inverted_index": {"query": [0], "decomposition": [1], "retrieval": [2]},
                    }
                ]
            }
        ).encode()
        response = HttpResponse(
            url="https://api.openalex.org/works",
            status=200,
            headers={"content-type": "application/json"},
            body=body,
        )
        with patch.dict(os.environ, {"OPENALEX_API_KEY": "test"}, clear=False):
            with patch("katala_web_research.providers.fetch_url", return_value=response):
                results = OpenAlexSearch().search("query decomposition retrieval")

        self.assertEqual(results[0].url, "https://aclanthology.org/2025.acl-srw.32/")
        self.assertIn("citations=42", results[0].snippet)
        self.assertEqual(results[0].source, "openalex")

    def test_meta_provider_merges_and_dedupes_engines(self):
        class FakeProvider:
            def __init__(self, name, url):
                self.name = name
                self.url = url

            def search(self, query, *, limit=10):
                return [SearchResult(title=f"{self.name} result", url=self.url, source=self.name, rank=1)]

        fake_providers = {
            "a": FakeProvider("a", "https://docs.github.com/example"),
            "b": FakeProvider("b", "https://docs.github.com/example/"),
            "c": FakeProvider("c", "https://arxiv.org/abs/2510.18633"),
            "meta": MetaSearch(),
        }
        with patch.dict(os.environ, {"KWR_META_PROVIDERS": "a,b,c"}, clear=False):
            with patch("katala_web_research.providers.PROVIDERS", fake_providers):
                results = MetaSearch().search("query decomposition", limit=5)

        self.assertEqual(len(results), 2)
        self.assertIn("https://arxiv.org/abs/2510.18633", {result.url for result in results})

    def test_meta_provider_records_engine_health(self):
        class OkProvider:
            name = "ok"

            def search(self, query, *, limit=10):
                return [SearchResult(title="Ok result", url="https://example.com/ok", source=self.name, rank=1)]

        class EmptyProvider:
            name = "empty"

            def search(self, query, *, limit=10):
                return []

        class FailingProvider:
            name = "boom"

            def search(self, query, *, limit=10):
                raise RuntimeError("provider failed")

        fake_providers = {
            "ok": OkProvider(),
            "empty": EmptyProvider(),
            "boom": FailingProvider(),
            "meta": MetaSearch(),
        }
        with patch.dict(os.environ, {"KWR_META_PROVIDERS": "ok,empty,boom"}, clear=False):
            with patch("katala_web_research.providers.PROVIDERS", fake_providers):
                results = MetaSearch().search("alpha", limit=5)

        self.assertEqual(len(results), 1)
        metadata = results[0].metadata
        runs = {row["provider"]: row for row in metadata["meta_engine_runs"]}
        self.assertEqual(runs["ok"]["status"], "ok")
        self.assertGreater(runs["ok"]["health_score"], 0)
        self.assertEqual(runs["empty"]["status"], "empty")
        self.assertEqual(runs["boom"]["status"], "error")
        self.assertEqual(runs["boom"]["error_kind"], "RuntimeError")
        self.assertEqual(metadata["engine_health"], {"ok": runs["ok"]["health_score"]})

    def test_meta_profile_rewrites_queries(self):
        seen_queries = {}

        class FakeProvider:
            def __init__(self, name):
                self.name = name

            def search(self, query, *, limit=10):
                seen_queries[self.name] = query
                return [SearchResult(title=f"{self.name} result", url=f"https://example.com/{self.name}", source=self.name, rank=1)]

        fake_providers = {
            "github": FakeProvider("github"),
            "searxng": FakeProvider("searxng"),
            "ddg": FakeProvider("ddg"),
            "meta": MetaSearch(),
        }
        with patch.dict(os.environ, {"KWR_META_PROFILE": "code", "KWR_META_PROVIDERS": ""}, clear=False):
            with patch("katala_web_research.providers.PROVIDERS", fake_providers):
                MetaSearch().search("browser agent", limit=3)

        self.assertEqual(seen_queries["github"], "browser agent implementation library")
        self.assertEqual(seen_queries["ddg"], "browser agent")


if __name__ == "__main__":
    unittest.main()
