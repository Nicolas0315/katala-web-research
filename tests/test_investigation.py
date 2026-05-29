import unittest

from katala_web_research.investigation import build_investigation_report, sort_web_candidates
from katala_web_research.models import PageSnapshot, SearchResult


class InvestigationTests(unittest.TestCase):
    def test_sort_web_candidates_prefers_official_docs(self):
        results = [
            SearchResult(title="Blog", url="https://example.com/post", source="ddg", rank=1, score=4.0),
            SearchResult(title="Docs", url="https://docs.github.com/en/rest/search/search", source="ddg", rank=2, score=1.0),
        ]
        sorted_results = sort_web_candidates(results)
        self.assertEqual(sorted_results[0].title, "Docs")

    def test_build_investigation_report_includes_captures(self):
        report = build_investigation_report(
            query="web research",
            provider="ddg",
            archive_path="archive.sqlite",
            web_results=[
                SearchResult(title="Docs", url="https://docs.github.com/en/rest/search/search", source="ddg", rank=1)
            ],
            repo_hits=[],
            pages=[
                PageSnapshot(
                    url="https://docs.github.com/en/rest/search/search",
                    title="GitHub Search",
                    content="Search API content",
                    source="direct",
                    fetched_at="2026-05-27T00:00:00+00:00",
                    status_code=200,
                )
            ],
        )
        self.assertIn("Investigation: web research", report)
        self.assertIn("Evidence Matrix", report)
        self.assertIn("Captured Pages", report)
        self.assertIn("Search API content", report)

    def test_investigation_report_includes_registry_caveat(self):
        report = build_investigation_report(
            query="news bias",
            provider="ddg",
            archive_path="archive.sqlite",
            web_results=[SearchResult(title="Ground News", url="https://ground.news/", source="ddg", rank=1)],
            repo_hits=[],
            pages=[],
        )

        self.assertIn("registry_source: Ground News", report)
        self.assertIn("bias_caveat: News domain only", report)


if __name__ == "__main__":
    unittest.main()
