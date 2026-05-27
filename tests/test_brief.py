import unittest

from katala_web_research.brief import build_brief
from katala_web_research.models import RepoHit, SearchResult
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


if __name__ == "__main__":
    unittest.main()

