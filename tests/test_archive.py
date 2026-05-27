import tempfile
import unittest
from pathlib import Path

from katala_web_research.archive import Archive
from katala_web_research.models import PageSnapshot, RepoDocument, SearchResult


class ArchiveTests(unittest.TestCase):
    def test_store_and_query_pages(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = Path(tmp) / "archive.sqlite"
            archive = Archive(archive_path)
            try:
                run_id = archive.store_run(
                    "agent research",
                    "ddg",
                    [SearchResult(title="Agent Research", url="https://example.com", source="ddg", rank=1)],
                )
                archive.upsert_page(
                    PageSnapshot(
                        url="https://example.com",
                        title="Agent Research",
                        content="A durable web research archive for agents.",
                        source="direct",
                        fetched_at="2026-05-27T00:00:00+00:00",
                    )
                )
                hits = archive.query("durable", limit=5)
            finally:
                archive.close()

            self.assertEqual(run_id, 1)
            self.assertEqual(len(hits), 1)
            self.assertEqual(hits[0].url, "https://example.com")

    def test_store_and_query_repo_documents(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = Path(tmp) / "archive.sqlite"
            archive = Archive(archive_path)
            try:
                archive.upsert_repo_document(
                    RepoDocument(
                        repo_path="/repos/sample",
                        repo_name="sample",
                        rel_path="README.md",
                        title="Sample",
                        content="This repository improves web research access.",
                        kind="readme",
                        indexed_at="2026-05-27T00:00:00+00:00",
                        file_size=51,
                        file_mtime_ns=123,
                        content_sha256="abc",
                    )
                )
                hits = archive.query_repos("web research", limit=5)
                metadata = archive.repo_document_metadata()
            finally:
                archive.close()

            self.assertEqual(len(hits), 1)
            self.assertEqual(hits[0].repo_name, "sample")
            self.assertEqual(metadata[("/repos/sample", "README.md")], (51, 123, "abc"))


if __name__ == "__main__":
    unittest.main()
