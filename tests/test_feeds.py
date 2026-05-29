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

    def test_json_feed_does_not_fabricate_url_from_id(self):
        parsed = parse_feed_text(
            '{"version":"https://jsonfeed.org/version/1.1","title":"Katala","items":[{"id":"post-1","title":"Only ID","content_text":"No URL"}]}',
            source_url="https://example.com/feed.json",
            fetched_at="2026-05-28T00:00:00+00:00",
        )

        self.assertEqual(parsed.items, [])
        self.assertEqual(parsed.source.last_item_count, 0)

    def test_rss_guid_without_permalink_is_not_used_as_url(self):
        parsed = parse_feed_text(
            """
            <rss version="2.0">
              <channel>
                <title>Katala</title>
                <item>
                  <title>GUID only</title>
                  <guid isPermaLink="false">post-1</guid>
                  <description>No URL</description>
                </item>
                <item>
                  <title>Permalink GUID</title>
                  <guid>https://example.com/permalink-guid</guid>
                  <description>Real URL</description>
                </item>
              </channel>
            </rss>
            """,
            source_url="https://example.com/feed.xml",
            fetched_at="2026-05-28T00:00:00+00:00",
        )

        self.assertEqual(len(parsed.items), 1)
        self.assertEqual(parsed.items[0].url, "https://example.com/permalink-guid")

    def test_atom_id_is_not_used_as_url_unless_it_is_url(self):
        parsed = parse_feed_text(
            """
            <feed xmlns="http://www.w3.org/2005/Atom">
              <title>Katala Atom</title>
              <entry>
                <title>Tag ID only</title>
                <id>tag:example.com,2026:post-1</id>
                <summary>No URL</summary>
              </entry>
              <entry>
                <title>URL ID</title>
                <id>https://example.com/atom-id-url</id>
                <summary>URL ID</summary>
              </entry>
            </feed>
            """,
            source_url="https://example.com/atom.xml",
            fetched_at="2026-05-28T00:00:00+00:00",
        )

        self.assertEqual(len(parsed.items), 1)
        self.assertEqual(parsed.items[0].url, "https://example.com/atom-id-url")

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

    def test_feed_source_add_preserves_refresh_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Archive(Path(tmp) / "archive.sqlite")
            try:
                archive.upsert_feed_source(
                    FeedSource(
                        url="https://example.com/feed.xml",
                        title="Katala Updates",
                        kind="rss",
                        last_fetched_at="2026-05-28T00:00:00+00:00",
                        status="ok",
                        health_score=1.0,
                        last_item_count=2,
                    )
                )
                archive.upsert_feed_source(
                    FeedSource(url="https://example.com/feed.xml", title="Manual Title")
                )
                sources = archive.feed_sources()
            finally:
                archive.close()

        self.assertEqual(sources[0].title, "Manual Title")
        self.assertEqual(sources[0].kind, "rss")
        self.assertEqual(sources[0].last_fetched_at, "2026-05-28T00:00:00+00:00")
        self.assertEqual(sources[0].status, "ok")
        self.assertEqual(sources[0].health_score, 1.0)
        self.assertEqual(sources[0].last_item_count, 2)

    def test_malformed_feed_fails_cleanly(self):
        with self.assertRaises(ValueError):
            parse_feed_text("<rss><broken>", source_url="https://example.com/feed.xml")

    def test_non_feed_xml_fails_cleanly(self):
        with self.assertRaises(ValueError):
            parse_feed_text("<urlset><url><loc>https://example.com/a</loc></url></urlset>", source_url="https://example.com/sitemap.xml")

    def test_leading_whitespace_and_bom_are_accepted(self):
        rss = '\ufeff\n<?xml version="1.0"?><rss version="2.0"><channel><title>Katala</title></channel></rss>'
        parsed = parse_feed_text(rss, source_url="https://example.com/feed.xml")

        self.assertEqual(parsed.source.kind, "rss")


if __name__ == "__main__":
    unittest.main()
