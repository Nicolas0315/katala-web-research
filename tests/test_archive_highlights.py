import tempfile
import unittest
from pathlib import Path

from katala_web_research.archive import Archive
from katala_web_research.archive_highlights import apply_archive_highlights, build_highlight
from katala_web_research.models import PageSnapshot, SearchResult


class ArchiveHighlightTests(unittest.TestCase):
    def test_build_highlight_selects_query_relevant_sentences(self):
        content = (
            "Generic introduction. "
            "Agentic retrieval systems need source quality scoring and benchmark evidence. "
            "Unrelated closing text. "
            "Evaluation benchmarks reveal whether retrieval quality improved."
        )

        highlight = build_highlight("retrieval benchmark quality", content)

        self.assertIn("Agentic retrieval systems", highlight)
        self.assertIn("Evaluation benchmarks", highlight)
        self.assertNotIn("Generic introduction", highlight)

    def test_apply_archive_highlights_replaces_snippet_for_archived_url(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = Path(tmp) / "archive.sqlite"
            archive = Archive(archive_path)
            try:
                archive.upsert_page(
                    PageSnapshot(
                        url="https://example.com/a",
                        title="A",
                        content=(
                            "Thin intro. "
                            "Katala search should use archive backed highlights for retrieval quality."
                        ),
                        source="direct",
                        fetched_at="2026-06-15T00:00:00+00:00",
                    )
                )
            finally:
                archive.close()

            results = [
                SearchResult(title="A", url="https://example.com/a", snippet="thin", source="ddg", rank=1),
                SearchResult(title="B", url="https://example.com/b", snippet="other", source="ddg", rank=2),
            ]
            highlighted = apply_archive_highlights(
                "archive highlights retrieval quality",
                results,
                archive_path=archive_path,
                highlight_top=2,
            )

        by_url = {result.url: result for result in highlighted}
        self.assertIn("archive backed highlights", by_url["https://example.com/a"].snippet)
        self.assertEqual(by_url["https://example.com/a"].metadata["highlight_status"], "ok")
        self.assertEqual(by_url["https://example.com/b"].metadata["highlight_status"], "miss")


if __name__ == "__main__":
    unittest.main()
