#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


@dataclass(slots=True)
class BenchCase:
    name: str
    cmd: list[str]
    budget_tokens: int
    include_files: list[Path] | None = None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", help="Optional real repository corpus root. Defaults to a generated fixture.")
    parser.add_argument("--query", default="research", help="Benchmark query. Default: research")
    parser.add_argument("--live-web", action="store_true", help="Include a live DDG/Jina-reader investigation benchmark.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        corpus_root = Path(args.root) if args.root else make_fixture(tmp_path / "repos")
        archive = tmp_path / "research.sqlite"
        report_dir = tmp_path / "reports"
        report_dir.mkdir()
        env = os.environ.copy()
        env["PYTHONPATH"] = str(ROOT / "src")

        cases = [
            BenchCase(
                "plan",
                [
                    "python3",
                    "-m",
                    "katala_web_research.cli",
                    "plan",
                    args.query,
                    "--max-subqueries",
                    "4",
                ],
                350,
            ),
            BenchCase(
                "eval",
                [
                    "python3",
                    "-m",
                    "katala_web_research.cli",
                    "eval",
                    "--min-score",
                    "80",
                    "--out",
                    str(report_dir / "eval.md"),
                ],
                1_600,
                [report_dir / "eval.md"],
            ),
            BenchCase(
                "repos_scan",
                [
                    "python3",
                    "-m",
                    "katala_web_research.cli",
                    "repos",
                    "scan",
                    str(corpus_root),
                    "--archive",
                    str(archive),
                    "--max-repos",
                    "3",
                    "--max-files-per-repo",
                    "8",
                ],
                700,
            ),
            BenchCase(
                "repos_query",
                [
                    "python3",
                    "-m",
                    "katala_web_research.cli",
                    "repos",
                    "query",
                    args.query,
                    "--archive",
                    str(archive),
                    "--limit",
                    "4",
                ],
                1_400,
            ),
            BenchCase(
                "brief_no_web",
                [
                    "python3",
                    "-m",
                    "katala_web_research.cli",
                    "brief",
                    args.query,
                    "--archive",
                    str(archive),
                    "--no-web",
                    "--repo-limit",
                    "4",
                    "--out",
                    str(report_dir / "brief.md"),
                ],
                800,
                [report_dir / "brief.md"],
            ),
            BenchCase(
                "investigate_no_web",
                [
                    "python3",
                    "-m",
                    "katala_web_research.cli",
                    "investigate",
                    args.query,
                    "--archive",
                    str(archive),
                    "--no-web",
                    "--repo-limit",
                    "4",
                    "--out",
                    str(report_dir / "investigation.md"),
                ],
                1_400,
                [report_dir / "investigation.md"],
            ),
        ]
        if args.live_web:
            cases.append(
                BenchCase(
                    "investigate_live_web",
                    [
                        "python3",
                        "-m",
                        "katala_web_research.cli",
                        "investigate",
                        "OpenAI Agents SDK handoffs",
                        "--archive",
                        str(archive),
                        "--web-limit",
                        "3",
                        "--repo-limit",
                        "2",
                        "--read-top",
                        "1",
                        "--expand-queries",
                        "--max-subqueries",
                        "3",
                        "--out",
                        str(report_dir / "live.md"),
                    ],
                    4_500,
                    [report_dir / "live.md"],
                )
            )

        results = [run_case(case, env) for case in cases]

    failed = [result for result in results if not result["ok"]]
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        for result in results:
            status = "ok" if result["ok"] else "FAIL"
            print(
                f"{status} {result['name']}: "
                f"approx_tokens={result['approx_tokens']} budget={result['budget_tokens']} "
                f"chars={result['chars']}"
            )
    return 1 if failed else 0


def run_case(case: BenchCase, env: dict[str, str]) -> dict:
    completed = subprocess.run(case.cmd, cwd=ROOT, env=env, text=True, capture_output=True, check=False)
    text = completed.stdout + completed.stderr
    if case.include_files:
        for path in case.include_files:
            if path.exists():
                text += "\n" + path.read_text(encoding="utf-8", errors="replace")
    chars = len(text)
    approx_tokens = estimate_tokens(text)
    return {
        "name": case.name,
        "returncode": completed.returncode,
        "chars": chars,
        "approx_tokens": approx_tokens,
        "budget_tokens": case.budget_tokens,
        "ok": completed.returncode == 0 and approx_tokens <= case.budget_tokens,
    }


def estimate_tokens(text: str) -> int:
    # Conservative approximation for mixed English/Japanese CLI reports.
    return math.ceil(len(text) / 3.5)


def make_fixture(root: Path) -> Path:
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    for name in ("alpha-research", "beta-agent", "gamma-search"):
        repo = root / name
        (repo / ".git").mkdir(parents=True)
        (repo / "docs").mkdir()
        (repo / "README.md").write_text(
            f"# {name}\n\nResearch workflow notes for web search, source ranking, and local evidence.\n",
            encoding="utf-8",
        )
        (repo / "AGENTS.md").write_text(
            "# Agent Notes\n\nUse official docs first and archive source evidence.\n",
            encoding="utf-8",
        )
        (repo / "pyproject.toml").write_text(
            f"[project]\nname = \"{name}\"\ndescription = \"fixture research package\"\n",
            encoding="utf-8",
        )
        (repo / "docs" / "workflow.md").write_text(
            "# Workflow\n\nSearch providers produce candidates, local corpora validate prior art, and reports capture evidence.\n",
            encoding="utf-8",
        )
    return root


if __name__ == "__main__":
    raise SystemExit(main())
