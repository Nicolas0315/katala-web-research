import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from katala_web_research.archive import Archive
from katala_web_research.cli import main
from katala_web_research.models import PageSnapshot, SearchResult


class CliSearchTests(unittest.TestCase):
    def test_search_threads_query_filters_to_provider_and_metadata(self):
        seen = {}

        def fake_search(query, *, provider, limit):
            seen["query"] = query
            seen["provider"] = provider
            seen["limit"] = limit
            return [
                SearchResult(
                    title="GitHub Docs",
                    url="https://docs.github.com/en/actions",
                    snippet="actions",
                    source="fake",
                    rank=1,
                )
            ]

        stdout = io.StringIO()
        with patch("katala_web_research.cli.search", side_effect=fake_search):
            with redirect_stdout(stdout):
                code = main(
                    [
                        "search",
                        "github actions",
                        "--provider",
                        "ddg",
                        "--limit",
                        "3",
                        "--category",
                        "github",
                        "--include-domain",
                        "docs.github.com",
                        "--exclude-domain",
                        "gist.github.com",
                        "--json",
                    ]
                )

        self.assertEqual(code, 0)
        self.assertEqual(seen["provider"], "ddg")
        self.assertEqual(seen["limit"], 6)
        self.assertIn("site:github.com", seen["query"])
        self.assertIn("site:docs.github.com", seen["query"])
        self.assertIn("-site:gist.github.com", seen["query"])
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload[0]["metadata"]["query_category"], "github")

    def test_search_can_apply_archive_highlights(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = Path(tmp) / "archive.sqlite"
            archive = Archive(archive_path)
            try:
                archive.upsert_page(
                    PageSnapshot(
                        url="https://example.com/a",
                        title="A",
                        content="Katala archive highlights improve retrieval quality for search results.",
                        source="direct",
                        fetched_at="2026-06-15T00:00:00+00:00",
                    )
                )
            finally:
                archive.close()

            stdout = io.StringIO()
            with patch(
                "katala_web_research.cli.search",
                return_value=[
                    SearchResult(
                        title="A",
                        url="https://example.com/a",
                        snippet="thin",
                        source="fake",
                        rank=1,
                    )
                ],
            ):
                with redirect_stdout(stdout):
                    code = main(
                        [
                            "search",
                            "archive highlights retrieval",
                            "--archive",
                            str(archive_path),
                            "--highlight-top",
                            "1",
                            "--json",
                        ]
                    )

        self.assertEqual(code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertIn("archive highlights improve", payload[0]["snippet"])
        self.assertEqual(payload[0]["metadata"]["highlight_status"], "ok")

    def test_search_accepts_github_code_provider(self):
        seen = {}

        def fake_search(query, *, provider, limit):
            seen["query"] = query
            seen["provider"] = provider
            seen["limit"] = limit
            return [
                SearchResult(
                    title="katala/search - src/providers.py",
                    url="https://github.com/katala/search/blob/main/src/providers.py",
                    snippet="class SearchResult",
                    source="github_code",
                    rank=1,
                )
            ]

        stdout = io.StringIO()
        with patch("katala_web_research.cli.search", side_effect=fake_search):
            with redirect_stdout(stdout):
                code = main(
                    [
                        "search",
                        "SearchResult repo:katala/search",
                        "--provider",
                        "github_code",
                        "--limit",
                        "2",
                        "--json",
                    ]
                )

        self.assertEqual(code, 0)
        self.assertEqual(seen["provider"], "github_code")
        self.assertEqual(seen["limit"], 4)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload[0]["source"], "github_code")


if __name__ == "__main__":
    unittest.main()
