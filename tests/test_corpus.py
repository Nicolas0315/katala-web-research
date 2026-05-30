import tempfile
import unittest
from pathlib import Path

from katala_web_research.corpus import classify_file, scan_repos


class CorpusTests(unittest.TestCase):
    def test_scan_repos_indexes_expected_docs(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "sample"
            (repo / ".git").mkdir(parents=True)
            (repo / "README.md").write_text("# Sample Repo\n\nAgent research toolkit.", encoding="utf-8")
            (repo / "pyproject.toml").write_text("[project]\nname = 'sample'\n", encoding="utf-8")
            (repo / "node_modules").mkdir()
            (repo / "node_modules" / "README.md").write_text("# Ignore", encoding="utf-8")

            documents, warnings = scan_repos(tmp)

        rel_paths = {doc.rel_path for doc in documents}
        self.assertEqual(warnings, [])
        self.assertIn("README.md", rel_paths)
        self.assertIn("pyproject.toml", rel_paths)
        self.assertNotIn("node_modules/README.md", rel_paths)
        self.assertTrue(all(doc.content_sha256 for doc in documents))
        readme = next(doc for doc in documents if doc.rel_path == "README.md")
        self.assertIn("repo:sample", readme.context)
        self.assertIn("path:README.md", readme.context)
        self.assertIn("headings:Sample Repo", readme.context)

    def test_scan_repos_skips_unchanged_docs(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "sample"
            (repo / ".git").mkdir(parents=True)
            readme = repo / "README.md"
            readme.write_text("# Sample Repo\n\nAgent research toolkit.", encoding="utf-8")
            first, _warnings = scan_repos(tmp)
            existing = {
                (first[0].repo_path, first[0].rel_path): (
                    first[0].file_size,
                    first[0].file_mtime_ns,
                    first[0].content_sha256,
                )
            }
            stats = {}
            second, _warnings = scan_repos(tmp, existing_metadata=existing, stats=stats)

        self.assertEqual(second, [])
        self.assertEqual(stats["skipped_unchanged"], 1)

    def test_unchanged_files_do_not_consume_max_files_budget(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "sample"
            (repo / ".git").mkdir(parents=True)
            readme = repo / "README.md"
            readme.write_text("# Sample Repo\n\nIndexed earlier.", encoding="utf-8")
            first, _warnings = scan_repos(tmp, max_files_per_repo=1)
            existing = {
                (first[0].repo_path, first[0].rel_path): (
                    first[0].file_size,
                    first[0].file_mtime_ns,
                    first[0].content_sha256,
                )
            }
            docs_dir = repo / "docs"
            docs_dir.mkdir()
            (docs_dir / "new.md").write_text("# New Doc\n\nFresh content.", encoding="utf-8")

            second, _warnings = scan_repos(tmp, max_files_per_repo=1, existing_metadata=existing)

        rel_paths = {doc.rel_path for doc in second}
        self.assertIn("docs/new.md", rel_paths)

    def test_classify_agent_context_files(self):
        self.assertEqual(classify_file(Path("CLAUDE.md")), "agent-context")
        self.assertEqual(classify_file(Path("GEMINI.md")), "agent-context")
        self.assertEqual(classify_file(Path("AGENTS.md")), "agent-context")


if __name__ == "__main__":
    unittest.main()
