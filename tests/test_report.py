import unittest

from katala_web_research.models import PageSnapshot, SearchResult
from katala_web_research.report import build_report


class ReportTests(unittest.TestCase):
    def test_report_contains_source_links(self):
        report = build_report(
            query="test",
            provider="ddg",
            results=[SearchResult(title="Example", url="https://example.com", source="ddg", rank=1, score=1.0)],
            pages=[
                PageSnapshot(
                    url="https://example.com",
                    title="Example",
                    content="Example page content",
                    source="direct",
                    fetched_at="2026-05-27T00:00:00+00:00",
                )
            ],
            archive_path="archive.sqlite",
        )
        self.assertIn("https://example.com", report)
        self.assertIn("pages_read: 1", report)


if __name__ == "__main__":
    unittest.main()

