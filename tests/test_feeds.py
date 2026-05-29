import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from katala_web_research.archive import Archive
from katala_web_research.feeds import parse_feed_text
from katala_web_research.models import FeedSource
from katala_web_research.providers import FeedSearch


FIXTURES = Path(__file__).parent / "fixtures"


class FeedTests(unittest.TestCase):
    def test_parse_rss_feed(self):
        parsed = parse_feed_text(
            (FIXTURES / "sample.rss.xml").read_text(encoding="utf-8"),
            source_url="https://example.com/feed.xml",
            fetched_at="2026-05-28T00:00:00+00:00",
        )

        self.assertEqual(parsed.source.title, "Katala Updates")
        self.assertEqual(parsed.source.kind, "rss")
        self.assertEqual(len(parsed.items), 2)
        self.assertEqual(parsed.items[0].url, "https://example.com/rsshub-adapter")
        self.assertEqual(parsed.items[1].url, "https://example.com/feed-archive")

    def test_parse_atom_feed(self):
        parsed = parse_feed_text(
            (FIXTURES / "sample.atom.xml").read_text(encoding="utf-8"),
            source_url="https://example.com/atom.xml",
            fetched_at="2026-05-28T00:00:00+00:00",
        )

        self.assertEqual(parsed.source.title, "Katala Atom")
        self.assertEqual(parsed.source.kind, "atom")
        self.assertEqual(parsed.items[0].published_at, "2026-05-27T13:30:00Z")

    def test_parse_json_feed(self):
        parsed = parse_feed_text(
            (FIXTURES / "sample.feed.json").read_text(encoding="utf-8"),
            source_url="https://example.com/feed.json",
            fetched_at="2026-05-28T00:00:00+00:00",
        )

        self.assertEqual(parsed.source.kind, "json")
        self.assertEqual(parsed.items[0].title, "JSON feed provider")

    def test_archive_query_and_feed_provider(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = Path(tmp) / "archive.sqlite"
            parsed = parse_feed_text(
                (FIXTURES / "sample.rss.xml").read_text(encoding="utf-8"),
                source_url="https://example.com/feed.xml",
                fetched_at="2026-05-28T00:00:00+00:00",
            )
            archive = Archive(archive_path)
            try:
                archive.upsert_feed_source(parsed.source)
                archive.upsert_feed_items(parsed.items)
                hits = archive.query_feeds("RSSHub", limit=5)
            finally:
                archive.close()

            self.assertEqual(len(hits), 1)
            self.assertEqual(hits[0].source_title, "Katala Updates")
            with patch.dict(os.environ, {"KWR_ARCHIVE": str(archive_path)}):
                results = FeedSearch().search("RSSHub adapter", limit=5)

            self.assertEqual(results[0].source, "feed")
            self.assertEqual(results[0].url, "https://example.com/rsshub-adapter")

    def test_feed_source_status_is_additive(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Archive(Path(tmp) / "archive.sqlite")
            try:
                archive.upsert_feed_source(
                    FeedSource(url="https://example.com/feed.xml", title="Manual")
                )
                sources = archive.feed_sources()
            finally:
                archive.close()

        self.assertEqual(sources[0].title, "Manual")
        self.assertEqual(sources[0].status, "pending")

    def test_malformed_feed_fails_cleanly(self):
        with self.assertRaises(ValueError):
            parse_feed_text("<rss><broken>", source_url="https://example.com/feed.xml")


if __name__ == "__main__":
    unittest.main()
