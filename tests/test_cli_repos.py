import json
import tempfile
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from katala_web_research.archive import Archive
from katala_web_research.cli import main
from katala_web_research.models import RepoDocument


class CliReposTests(unittest.TestCase):
    def test_repos_query_accepts_repo_and_path_filters(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = Path(tmp) / "archive.sqlite"
            archive = Archive(archive_path)
            try:
                archive.upsert_repo_documents(
                    [
                        RepoDocument(
                            repo_path="/repos/alpha",
                            repo_name="alpha",
                            rel_path="docs/search.md",
                            title="Search",
                            content="retrieval filter",
                            kind="doc",
                            indexed_at="2026-05-27T00:00:00+00:00",
                        ),
                        RepoDocument(
                            repo_path="/repos/beta",
                            repo_name="beta",
                            rel_path="docs/search.md",
                            title="Search",
                            content="retrieval filter",
                            kind="doc",
                            indexed_at="2026-05-27T00:00:00+00:00",
                        ),
                    ]
                )
            finally:
                archive.close()

            with patch("sys.stdout", new_callable=StringIO) as stdout:
                code = main(
                    [
                        "repos",
                        "query",
                        "retrieval filter",
                        "--archive",
                        str(archive_path),
                        "--repo",
                        "alpha",
                        "--path",
                        "docs/",
                        "--json",
                    ]
                )

        self.assertEqual(code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]["repo_name"], "alpha")
        self.assertEqual(payload[0]["rel_path"], "docs/search.md")

    def test_repos_query_accepts_inline_repo_and_path_filters(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = Path(tmp) / "archive.sqlite"
            archive = Archive(archive_path)
            try:
                archive.upsert_repo_documents(
                    [
                        RepoDocument(
                            repo_path="/repos/alpha",
                            repo_name="alpha",
                            rel_path="docs/search.md",
                            title="Search",
                            content="retrieval filter",
                            kind="doc",
                            indexed_at="2026-05-27T00:00:00+00:00",
                        ),
                        RepoDocument(
                            repo_path="/repos/beta",
                            repo_name="beta",
                            rel_path="docs/search.md",
                            title="Search",
                            content="retrieval filter",
                            kind="doc",
                            indexed_at="2026-05-27T00:00:00+00:00",
                        ),
                    ]
                )
            finally:
                archive.close()

            with patch("sys.stdout", new_callable=StringIO) as stdout:
                code = main(
                    [
                        "repos",
                        "query",
                        "repo:alpha path:docs/ retrieval filter",
                        "--archive",
                        str(archive_path),
                        "--json",
                    ]
                )

        self.assertEqual(code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]["repo_name"], "alpha")
        self.assertEqual(payload[0]["rel_path"], "docs/search.md")


if __name__ == "__main__":
    unittest.main()
