import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from katala_web_research.archive import Archive
from katala_web_research.cli import main
from katala_web_research.issues import build_project_radar, parse_gh_search_items


GH_ISSUES = [
    {
        "number": 22,
        "repository": {"nameWithOwner": "Nicolas0315/cybertical"},
        "state": "open",
        "title": "TIKTOK-AWS-000: AWS migration control plane",
        "updatedAt": "2026-05-29T03:35:29Z",
        "url": "https://github.com/Nicolas0315/cybertical/issues/22",
        "labels": [
            {"name": "area/aws"},
            {"name": "priority/p0"},
            {"name": "phase/0-control-plane"},
        ],
    },
    {
        "number": 6,
        "repository": {"nameWithOwner": "Nicolas0315/katala-web-research"},
        "state": "open",
        "title": "Add OpenAlex citation expansion and cached URL reading",
        "updatedAt": "2026-05-27T14:25:11Z",
        "url": "https://github.com/Nicolas0315/katala-web-research/issues/6",
        "labels": [{"name": "research"}, {"name": "enhancement"}],
    },
]


class ProjectIssueTests(unittest.TestCase):
    def test_archive_project_items_are_queryable_by_labels_and_title(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = Path(tmp) / "archive.sqlite"
            items = parse_gh_search_items(GH_ISSUES, kind="issue")
            archive = Archive(archive_path)
            try:
                count = archive.upsert_project_items(items)
                hits = archive.query_project_items("aws p0", limit=5)
            finally:
                archive.close()

        self.assertEqual(count, 2)
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].repository, "Nicolas0315/cybertical")
        self.assertEqual(hits[0].priority, "p0")

    def test_project_radar_report_summarizes_priority_items(self):
        items = parse_gh_search_items(GH_ISSUES, kind="issue")

        report = build_project_radar(
            items,
            archive_path="/tmp/projects.sqlite",
            owner="Nicolas0315",
            generated_at="2026-05-29T00:00:00+00:00",
        )

        self.assertIn("# Katala Project Radar", report)
        self.assertIn("owner: Nicolas0315", report)
        self.assertIn("## P0", report)
        self.assertIn("TIKTOK-AWS-000: AWS migration control plane", report)
        self.assertIn("https://github.com/Nicolas0315/cybertical/issues/22", report)

    def test_cli_issues_ingest_query_and_report_from_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = Path(tmp) / "archive.sqlite"
            source_path = Path(tmp) / "issues.json"
            report_path = Path(tmp) / "radar.md"
            source_path.write_text(json.dumps(GH_ISSUES), encoding="utf-8")

            with contextlib.redirect_stdout(io.StringIO()):
                ingest_code = main(
                    [
                        "issues",
                        "ingest",
                        "--from-json",
                        str(source_path),
                        "--kind",
                        "issue",
                        "--archive",
                        str(archive_path),
                    ]
                )
            query_stdout = io.StringIO()
            with contextlib.redirect_stdout(query_stdout):
                query_code = main(
                    [
                        "issues",
                        "query",
                        "aws p0",
                        "--archive",
                        str(archive_path),
                        "--json",
                    ]
                )
            with contextlib.redirect_stdout(io.StringIO()):
                report_code = main(
                    [
                        "issues",
                        "report",
                        "--archive",
                        str(archive_path),
                        "--out",
                        str(report_path),
                    ]
                )
            report_text = report_path.read_text(encoding="utf-8")

        self.assertEqual(ingest_code, 0)
        self.assertEqual(query_code, 0)
        self.assertEqual(report_code, 0)
        self.assertEqual(json.loads(query_stdout.getvalue())[0]["priority"], "p0")
        self.assertIn("Katala Project Radar", report_text)


if __name__ == "__main__":
    unittest.main()
