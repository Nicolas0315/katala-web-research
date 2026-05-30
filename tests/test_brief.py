import unittest

from katala_web_research.brief import build_brief
from katala_web_research.models import FeedHit, RepoHit, SearchResult
from katala_web_research.source_quality import classify_url


class BriefTests(unittest.TestCase):
    def test_classifies_official_docs(self):
        label, score = classify_url("https://docs.github.com/en/rest/search/search")
        self.assertEqual(label, "official-docs")
        self.assertEqual(score, 100)

    def test_builds_combined_brief(self):
        brief = build_brief(
            query="web research",
            web_results=[
                SearchResult(
                    title="GitHub Docs",
                    url="https://docs.github.com/en/rest/search/search",
                    snippet="Search API",
                    source="ddg",
                    rank=1,
                    score=2.0,
                )
            ],
            repo_hits=[
                RepoHit(
                    repo_path="/repos/sample",
                    repo_name="sample",
                    rel_path="README.md",
                    title="Sample",
                    snippet="local repo evidence",
                    kind="readme",
                    rank=0.0,
                    indexed_at="2026-05-27T00:00:00+00:00",
                )
            ],
            archive_path="archive.sqlite",
        )
        self.assertIn("Best Web Candidates", brief)
        self.assertIn("official-docs", brief)
        self.assertIn("Local Repository Evidence", brief)

    def test_brief_includes_registry_caveat_for_matched_source(self):
        brief = build_brief(
            query="security priority",
            web_results=[
                SearchResult(
                    title="CISA KEV",
                    url="https://www.cisa.gov/known-exploited-vulnerabilities-catalog",
                    snippet="Known exploited vulnerabilities",
                    source="ddg",
                    rank=1,
                    score=2.0,
                )
            ],
            repo_hits=[],
            archive_path="archive.sqlite",
        )

        self.assertIn("registry_source: CISA Known Exploited Vulnerabilities Catalog", brief)
        self.assertIn("bias_caveat: US government operational perspective", brief)

    def test_brief_includes_feed_evidence_section(self):
        brief = build_brief(
            query="python release",
            web_results=[],
            repo_hits=[],
            archive_path="archive.sqlite",
            feed_hits=[
                FeedHit(
                    url="https://docs.python.org/3/whatsnew/3.14.html",
                    title="What's New in Python 3.14",
                    snippet="Release notes",
                    rank=0.0,
                    source_url="https://docs.python.org/feed.xml",
                    source_title="Python Insider",
                    published_at="2026-05-01",
                    fetched_at="2026-05-27T00:00:00+00:00",
                )
            ],
        )

        self.assertIn("## Feed Evidence", brief)
        self.assertIn("What's New in Python 3.14", brief)
        self.assertIn("feed: Python Insider", brief)

    def test_brief_reports_empty_feed_evidence(self):
        brief = build_brief(
            query="python release",
            web_results=[],
            repo_hits=[],
            archive_path="archive.sqlite",
        )

        self.assertIn("No archived feed items matched", brief)


if __name__ == "__main__":
    unittest.main()
