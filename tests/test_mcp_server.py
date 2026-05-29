import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch

from katala_web_research.archive import Archive
from katala_web_research.feeds import parse_feed_text
from katala_web_research.mcp_server import handle_request


FIXTURES = Path(__file__).parent / "fixtures"


class McpServerTests(unittest.TestCase):
    def test_initialize(self):
        response = handle_request({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
        self.assertEqual(response["result"]["serverInfo"]["name"], "katala-web-research")
        self.assertIn("tools", response["result"]["capabilities"])

    def test_tools_list(self):
        response = handle_request({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        names = {tool["name"] for tool in response["result"]["tools"]}
        self.assertIn("kwr.plan", names)
        self.assertIn("kwr.eval", names)
        self.assertIn("kwr.search", names)
        self.assertIn("kwr.repos_query", names)
        self.assertIn("kwr.investigate", names)

    def test_brief_feed_provider_uses_requested_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            feed_archive_path = Path(tmp) / "feed.sqlite"
            empty_archive_path = Path(tmp) / "empty.sqlite"
            parsed = parse_feed_text(
                (FIXTURES / "sample.rss.xml").read_text(encoding="utf-8"),
                source_url="https://example.com/feed.xml",
                fetched_at="2026-05-28T00:00:00+00:00",
            )
            feed_archive = Archive(feed_archive_path)
            try:
                feed_archive.upsert_feed_source(parsed.source)
                feed_archive.upsert_feed_items(parsed.items)
            finally:
                feed_archive.close()

            with patch.dict("os.environ", {"KWR_ARCHIVE": str(empty_archive_path)}):
                response = handle_request(
                    {
                        "jsonrpc": "2.0",
                        "id": 3,
                        "method": "tools/call",
                        "params": {
                            "name": "kwr.brief",
                            "arguments": {
                                "query": "RSSHub adapter",
                                "provider": "feed",
                                "archive": str(feed_archive_path),
                                "web_limit": 5,
                                "repo_limit": 0,
                            },
                        },
                    }
                )

        text = response["result"]["content"][0]["text"]
        self.assertIn("RSSHub adapter research", text)

    def test_search_feed_provider_uses_requested_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            feed_archive_path = Path(tmp) / "feed.sqlite"
            empty_archive_path = Path(tmp) / "empty.sqlite"
            parsed = parse_feed_text(
                (FIXTURES / "sample.rss.xml").read_text(encoding="utf-8"),
                source_url="https://example.com/feed.xml",
                fetched_at="2026-05-28T00:00:00+00:00",
            )
            feed_archive = Archive(feed_archive_path)
            try:
                feed_archive.upsert_feed_source(parsed.source)
                feed_archive.upsert_feed_items(parsed.items)
            finally:
                feed_archive.close()

            with patch.dict("os.environ", {"KWR_ARCHIVE": str(empty_archive_path)}):
                response = handle_request(
                    {
                        "jsonrpc": "2.0",
                        "id": 4,
                        "method": "tools/call",
                        "params": {
                            "name": "kwr.search",
                            "arguments": {
                                "query": "RSSHub adapter",
                                "provider": "feed",
                                "archive": str(feed_archive_path),
                                "limit": 5,
                            },
                        },
                    }
                )

        text = response["result"]["content"][0]["text"]
        self.assertIn("RSSHub adapter research", text)
        self.assertIn("https://example.com/rsshub-adapter", text)


if __name__ == "__main__":
    unittest.main()
