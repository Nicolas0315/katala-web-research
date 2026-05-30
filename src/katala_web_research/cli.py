from __future__ import annotations

import argparse
import contextlib
import json
import os
import sqlite3
import sys
from pathlib import Path

from . import __version__
from .archive import DEFAULT_ARCHIVE, Archive
from .brief import build_brief
from .corpus import scan_repos
from .evaluation import build_eval_report, run_eval
from .feeds import fetch_and_parse_feed
from .investigation import build_investigation_report, sort_web_candidates
from .issues import build_project_radar, fetch_github_project_items, load_project_items_json
from .models import FeedSource, PageSnapshot, SearchResult, utc_now_iso
from .planner import SearchPlanStep, build_search_plan
from .providers import provider_status, search
from .reader import read_url
from .report import build_report
from .source_registry import source_registry
from .workflow import search_with_plan

PROVIDER_CHOICES = ["brave", "ddg", "feed", "github", "jina", "meta", "openalex", "searxng"]


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (OSError, RuntimeError, ValueError, sqlite3.Error) as exc:
        print(f"kwr: error: {exc}", file=sys.stderr)
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="kwr")
    parser.add_argument("--version", action="version", version=f"kwr {__version__}")
    sub = parser.add_subparsers(required=True)

    p_search = sub.add_parser("search", help="search the web or a provider")
    p_search.add_argument("query")
    p_search.add_argument("--provider", default="ddg", choices=PROVIDER_CHOICES)
    p_search.add_argument("--limit", "-n", type=int, default=10)
    p_search.add_argument("--archive", default=str(DEFAULT_ARCHIVE))
    p_search.add_argument("--json", action="store_true")
    p_search.set_defaults(func=cmd_search)

    p_read = sub.add_parser("read", help="read a URL into text")
    p_read.add_argument("url")
    p_read.add_argument("--reader", default="auto", choices=["auto", "jina", "direct"])
    p_read.add_argument("--json", action="store_true")
    p_read.set_defaults(func=cmd_read)

    p_collect = sub.add_parser("collect", help="search, read top pages, and archive evidence")
    p_collect.add_argument("query")
    p_collect.add_argument("--provider", default="ddg", choices=PROVIDER_CHOICES)
    p_collect.add_argument("--reader", default="auto", choices=["auto", "jina", "direct"])
    p_collect.add_argument("--limit", "-n", type=int, default=10)
    p_collect.add_argument("--read-top", type=int, default=3)
    p_collect.add_argument("--archive", default=str(DEFAULT_ARCHIVE))
    p_collect.add_argument("--report")
    p_collect.add_argument("--json", action="store_true")
    p_collect.set_defaults(func=cmd_collect)

    p_query = sub.add_parser("query", help="search the local SQLite archive")
    p_query.add_argument("terms")
    p_query.add_argument("--archive", default=str(DEFAULT_ARCHIVE))
    p_query.add_argument("--limit", "-n", type=int, default=10)
    p_query.add_argument("--json", action="store_true")
    p_query.set_defaults(func=cmd_query)

    p_plan = sub.add_parser("plan", help="decompose a research question into bounded search queries")
    p_plan.add_argument("query")
    p_plan.add_argument("--max-subqueries", type=int, default=4)
    p_plan.add_argument("--year", type=int)
    p_plan.add_argument("--json", action="store_true")
    p_plan.set_defaults(func=cmd_plan)

    p_repos = sub.add_parser("repos", help="index and query local Git repository corpora")
    repos_sub = p_repos.add_subparsers(required=True)
    p_repos_scan = repos_sub.add_parser("scan", help="scan Git repos under a root path into the archive")
    p_repos_scan.add_argument("root")
    p_repos_scan.add_argument("--archive", default=str(DEFAULT_ARCHIVE))
    p_repos_scan.add_argument("--max-repos", type=int, default=200)
    p_repos_scan.add_argument("--max-files-per-repo", type=int, default=80)
    p_repos_scan.add_argument("--max-bytes-per-file", type=int, default=80_000)
    p_repos_scan.add_argument("--no-incremental", action="store_true")
    p_repos_scan.add_argument("--json", action="store_true")
    p_repos_scan.set_defaults(func=cmd_repos_scan)

    p_repos_query = repos_sub.add_parser("query", help="search indexed repository documents")
    p_repos_query.add_argument("terms")
    p_repos_query.add_argument("--archive", default=str(DEFAULT_ARCHIVE))
    p_repos_query.add_argument("--limit", "-n", type=int, default=10)
    p_repos_query.add_argument("--json", action="store_true")
    p_repos_query.set_defaults(func=cmd_repos_query)

    p_feeds = sub.add_parser("feeds", help="register, refresh, and query feed sources")
    feeds_sub = p_feeds.add_subparsers(required=True)
    p_feeds_add = feeds_sub.add_parser("add", help="add a feed source URL to the archive")
    p_feeds_add.add_argument("url")
    p_feeds_add.add_argument("--title", default="")
    p_feeds_add.add_argument("--archive", default=str(DEFAULT_ARCHIVE))
    p_feeds_add.add_argument("--json", action="store_true")
    p_feeds_add.set_defaults(func=cmd_feeds_add)

    p_feeds_refresh = feeds_sub.add_parser("refresh", help="fetch and index feed source items")
    p_feeds_refresh.add_argument("--source")
    p_feeds_refresh.add_argument("--archive", default=str(DEFAULT_ARCHIVE))
    p_feeds_refresh.add_argument("--json", action="store_true")
    p_feeds_refresh.set_defaults(func=cmd_feeds_refresh)

    p_feeds_query = feeds_sub.add_parser("query", help="search archived feed items")
    p_feeds_query.add_argument("terms")
    p_feeds_query.add_argument("--archive", default=str(DEFAULT_ARCHIVE))
    p_feeds_query.add_argument("--limit", "-n", type=int, default=10)
    p_feeds_query.add_argument("--json", action="store_true")
    p_feeds_query.set_defaults(func=cmd_feeds_query)

    p_sources = sub.add_parser("sources", help="inspect trusted source registry entries")
    sources_sub = p_sources.add_subparsers(required=True)
    p_sources_list = sources_sub.add_parser("list", help="list source registry entries")
    p_sources_list.add_argument("--domain")
    p_sources_list.add_argument("--query-type")
    p_sources_list.add_argument("--limit", "-n", type=int, default=20)
    p_sources_list.add_argument("--json", action="store_true")
    p_sources_list.set_defaults(func=cmd_sources_list)
    p_sources_match = sources_sub.add_parser("match", help="match a URL against the source registry")
    p_sources_match.add_argument("url")
    p_sources_match.add_argument("--json", action="store_true")
    p_sources_match.set_defaults(func=cmd_sources_match)

    p_issues = sub.add_parser("issues", help="ingest, query, and report GitHub Issues and PRs")
    issues_sub = p_issues.add_subparsers(required=True)
    p_issues_ingest = issues_sub.add_parser("ingest", help="ingest GitHub Issues and PRs into the archive")
    p_issues_ingest.add_argument("--owner", default="Nicolas0315")
    p_issues_ingest.add_argument("--state", default="open", choices=["open", "closed"])
    p_issues_ingest.add_argument("--include", default="both", choices=["issues", "prs", "both"])
    p_issues_ingest.add_argument("--limit", "-n", type=int, default=50)
    p_issues_ingest.add_argument("--from-json")
    p_issues_ingest.add_argument("--kind", default="issue", choices=["issue", "pr"])
    p_issues_ingest.add_argument("--archive", default=str(DEFAULT_ARCHIVE))
    p_issues_ingest.add_argument("--json", action="store_true")
    p_issues_ingest.set_defaults(func=cmd_issues_ingest)

    p_issues_query = issues_sub.add_parser("query", help="search archived GitHub Issues and PRs")
    p_issues_query.add_argument("terms")
    p_issues_query.add_argument("--archive", default=str(DEFAULT_ARCHIVE))
    p_issues_query.add_argument("--limit", "-n", type=int, default=10)
    p_issues_query.add_argument("--json", action="store_true")
    p_issues_query.set_defaults(func=cmd_issues_query)

    p_issues_report = issues_sub.add_parser("report", help="write a Markdown project radar report")
    p_issues_report.add_argument("--archive", default=str(DEFAULT_ARCHIVE))
    p_issues_report.add_argument("--owner", default="")
    p_issues_report.add_argument("--limit", "-n", type=int, default=100)
    p_issues_report.add_argument("--out")
    p_issues_report.add_argument("--json", action="store_true")
    p_issues_report.set_defaults(func=cmd_issues_report)

    p_brief = sub.add_parser("brief", help="combine web search and local repo hits into a research brief")
    p_brief.add_argument("query")
    p_brief.add_argument("--archive", default=str(DEFAULT_ARCHIVE))
    p_brief.add_argument("--provider", default="ddg", choices=PROVIDER_CHOICES)
    p_brief.add_argument("--web-limit", type=int, default=5)
    p_brief.add_argument("--repo-limit", type=int, default=5)
    p_brief.add_argument("--feed-limit", type=int, default=0)
    p_brief.add_argument("--expand-queries", action="store_true")
    p_brief.add_argument("--max-subqueries", type=int, default=4)
    p_brief.add_argument("--no-web", action="store_true")
    p_brief.add_argument("--out")
    p_brief.add_argument("--json", action="store_true")
    p_brief.set_defaults(func=cmd_brief)

    p_investigate = sub.add_parser(
        "investigate",
        help="run web search, local repo lookup, selected URL capture, and report generation",
    )
    p_investigate.add_argument("query")
    p_investigate.add_argument("--archive", default=str(DEFAULT_ARCHIVE))
    p_investigate.add_argument("--provider", default="ddg", choices=PROVIDER_CHOICES)
    p_investigate.add_argument("--reader", default="auto", choices=["auto", "jina", "direct"])
    p_investigate.add_argument("--web-limit", type=int, default=8)
    p_investigate.add_argument("--repo-limit", type=int, default=6)
    p_investigate.add_argument("--feed-limit", type=int, default=0)
    p_investigate.add_argument("--read-top", type=int, default=3)
    p_investigate.add_argument("--expand-queries", action="store_true")
    p_investigate.add_argument("--max-subqueries", type=int, default=4)
    p_investigate.add_argument("--no-web", action="store_true")
    p_investigate.add_argument("--out")
    p_investigate.add_argument("--json", action="store_true")
    p_investigate.set_defaults(func=cmd_investigate)

    p_doctor = sub.add_parser("doctor", help="show provider and local archive capability")
    p_doctor.set_defaults(func=cmd_doctor)

    p_eval = sub.add_parser("eval", help="run deterministic research-quality benchmark cases")
    p_eval.add_argument("--min-score", type=int, default=80)
    p_eval.add_argument("--max-subqueries", type=int, default=4)
    p_eval.add_argument("--out")
    p_eval.add_argument("--json", action="store_true")
    p_eval.set_defaults(func=cmd_eval)

    p_mcp = sub.add_parser("mcp", help="run the katala-web-research MCP stdio server")
    p_mcp.set_defaults(func=cmd_mcp)
    return parser


def cmd_search(args: argparse.Namespace) -> int:
    with archive_env(args.archive):
        results = search(args.query, provider=args.provider, limit=args.limit)
    if args.json:
        print_json([result.to_dict() for result in results])
    else:
        print_results(results)
    return 0


def cmd_read(args: argparse.Namespace) -> int:
    page = read_url(args.url, reader=args.reader)
    if args.json:
        print_json(page.to_dict())
    else:
        print(page.content)
    return 0


def cmd_collect(args: argparse.Namespace) -> int:
    with archive_env(args.archive):
        results = search(args.query, provider=args.provider, limit=args.limit)
    pages: list[PageSnapshot] = []
    archive = Archive(args.archive)
    try:
        run_id = archive.store_run(args.query, args.provider, results)
        for result in results[: max(args.read_top, 0)]:
            try:
                page = read_url(result.url, reader=args.reader)
            except Exception as exc:
                page = PageSnapshot(
                    url=result.url,
                    title=result.title,
                    content=f"Read failed: {exc}",
                    source="error",
                    fetched_at="",
                )
            pages.append(page)
            archive.upsert_page(page)
    finally:
        archive.close()

    report_path = None
    if args.report:
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            build_report(
                query=args.query,
                provider=args.provider,
                results=results,
                pages=pages,
                archive_path=args.archive,
            ),
            encoding="utf-8",
        )

    payload = {
        "run_id": run_id,
        "archive": args.archive,
        "report": str(report_path) if report_path else None,
        "results": [result.to_dict() for result in results],
        "pages": [page.to_dict() for page in pages],
    }
    if args.json:
        print_json(payload)
    else:
        print(f"run_id: {run_id}")
        print(f"archive: {args.archive}")
        if report_path:
            print(f"report: {report_path}")
        print(f"results: {len(results)}")
        print(f"pages_read: {len(pages)}")
    return 0


def cmd_query(args: argparse.Namespace) -> int:
    archive = Archive(args.archive)
    try:
        hits = archive.query(args.terms, limit=args.limit)
    finally:
        archive.close()
    if args.json:
        print_json([hit.to_dict() for hit in hits])
    else:
        for idx, hit in enumerate(hits, start=1):
            print(f"{idx}. {hit.title}")
            print(f"   {hit.url}")
            print(f"   {hit.snippet}")
    return 0


def cmd_plan(args: argparse.Namespace) -> int:
    plan = build_search_plan(args.query, max_subqueries=args.max_subqueries, year=args.year)
    if args.json:
        print_json([step.to_dict() for step in plan])
    else:
        for idx, step in enumerate(plan, start=1):
            print(f"{idx}. {step.intent}: {step.query}")
    return 0


def cmd_repos_scan(args: argparse.Namespace) -> int:
    existing_metadata = {}
    if not args.no_incremental:
        archive = Archive(args.archive)
        existing_metadata = archive.repo_document_metadata()
        archive.close()
    stats: dict[str, int] = {"skipped_unchanged": 0}
    documents, warnings = scan_repos(
        args.root,
        max_repos=args.max_repos,
        max_files_per_repo=args.max_files_per_repo,
        max_bytes_per_file=args.max_bytes_per_file,
        existing_metadata=existing_metadata,
        stats=stats,
    )
    archive = Archive(args.archive)
    try:
        indexed = archive.upsert_repo_documents(documents)
    finally:
        archive.close()
    payload = {
        "root": args.root,
        "archive": args.archive,
        "indexed_documents": indexed,
        "skipped_unchanged": stats.get("skipped_unchanged", 0),
        "repos": sorted({doc.repo_path for doc in documents}),
        "warnings": warnings,
    }
    if args.json:
        print_json(payload)
    else:
        print(f"root: {args.root}")
        print(f"archive: {args.archive}")
        print(f"indexed_documents: {indexed}")
        print(f"skipped_unchanged: {stats.get('skipped_unchanged', 0)}")
        print(f"repos: {len(payload['repos'])}")
        for warning in warnings:
            print(f"warning: {warning}")
    return 0


def cmd_repos_query(args: argparse.Namespace) -> int:
    archive = Archive(args.archive)
    try:
        hits = archive.query_repos(args.terms, limit=args.limit)
    finally:
        archive.close()
    if args.json:
        print_json([hit.to_dict() for hit in hits])
    else:
        for idx, hit in enumerate(hits, start=1):
            print(f"{idx}. {hit.repo_name}/{hit.rel_path}")
            print(f"   {hit.title}")
            print(f"   {hit.snippet}")
            print(f"   {hit.repo_path}")
    return 0


def cmd_feeds_add(args: argparse.Namespace) -> int:
    source = FeedSource(url=args.url, title=args.title, status="pending")
    archive = Archive(args.archive)
    try:
        archive.upsert_feed_source(source)
        sources = archive.feed_sources()
    finally:
        archive.close()
    payload = {
        "archive": args.archive,
        "source": source.to_dict(),
        "source_count": len(sources),
    }
    if args.json:
        print_json(payload)
    else:
        print(f"archive: {args.archive}")
        print(f"source: {args.url}")
        print(f"source_count: {len(sources)}")
    return 0


def cmd_feeds_refresh(args: argparse.Namespace) -> int:
    archive = Archive(args.archive)
    refreshed = []
    try:
        if args.source:
            sources = [FeedSource(url=args.source, status="pending")]
            archive.upsert_feed_source(sources[0])
        else:
            sources = archive.feed_sources()
        for source in sources:
            try:
                parsed = fetch_and_parse_feed(source.url)
                archive.upsert_feed_source(parsed.source)
                indexed = archive.upsert_feed_items(parsed.items)
                refreshed.append(parsed.source.to_dict() | {"indexed_items": indexed})
            except Exception as exc:
                failed = FeedSource(
                    url=source.url,
                    title=source.title,
                    kind=source.kind,
                    last_fetched_at=utc_now_iso(),
                    status="error",
                    health_score=0.0,
                    error_kind=exc.__class__.__name__,
                )
                archive.upsert_feed_source(failed)
                refreshed.append(failed.to_dict() | {"indexed_items": 0})
    finally:
        archive.close()
    payload = {
        "archive": args.archive,
        "refreshed": refreshed,
        "source_count": len(refreshed),
        "indexed_items": sum(int(row["indexed_items"]) for row in refreshed),
    }
    if args.json:
        print_json(payload)
    else:
        print(f"archive: {args.archive}")
        print(f"sources: {payload['source_count']}")
        print(f"indexed_items: {payload['indexed_items']}")
        for row in refreshed:
            print(f"{row['url']}: {row['status']} items={row['indexed_items']}")
    return 0


def cmd_feeds_query(args: argparse.Namespace) -> int:
    archive = Archive(args.archive)
    try:
        hits = archive.query_feeds(args.terms, limit=args.limit)
    finally:
        archive.close()
    if args.json:
        print_json([hit.to_dict() for hit in hits])
    else:
        for idx, hit in enumerate(hits, start=1):
            print(f"{idx}. {hit.title}")
            print(f"   {hit.url}")
            print(f"   feed: {hit.source_title or hit.source_url}")
            print(f"   {hit.snippet}")
    return 0


def cmd_sources_list(args: argparse.Namespace) -> int:
    registry = source_registry()
    sources = registry.recommend(domain=args.domain, query_type=args.query_type, limit=args.limit)
    payload = {
        "count": len(sources),
        "domain": args.domain,
        "query_type": args.query_type,
        "sources": [source.to_dict() for source in sources],
    }
    if args.json:
        print_json(payload)
    else:
        print(f"count: {len(sources)}")
        for source in sources:
            print(f"- {source.domain}/{source.source_type}: {source.name}")
            print(f"  url: {source.url}")
            if source.bias_caveat:
                print(f"  caveat: {source.bias_caveat}")
    return 0


def cmd_sources_match(args: argparse.Namespace) -> int:
    source = source_registry().match_url(args.url)
    payload = {
        "url": args.url,
        "matched": source is not None,
        "source": source.to_dict() if source else None,
    }
    if args.json:
        print_json(payload)
    else:
        if source is None:
            print("matched: false")
        else:
            print("matched: true")
            print(f"source: {source.name}")
            print(f"domain: {source.domain}")
            print(f"source_type: {source.source_type}")
            print(f"trust_score: {source.trust_score}")
            if source.bias_caveat:
                print(f"bias_caveat: {source.bias_caveat}")
    return 0


def cmd_issues_ingest(args: argparse.Namespace) -> int:
    if args.from_json:
        items = load_project_items_json(args.from_json, kind=args.kind)
    else:
        items = fetch_github_project_items(
            owner=args.owner,
            state=args.state,
            limit=args.limit,
            include=args.include,
        )
    archive = Archive(args.archive)
    try:
        indexed = archive.upsert_project_items(items)
    finally:
        archive.close()
    payload = {
        "archive": args.archive,
        "indexed_items": indexed,
        "owner": args.owner,
        "state": args.state,
        "include": args.include,
    }
    if args.json:
        print_json(payload)
    else:
        print(f"archive: {args.archive}")
        print(f"indexed_items: {indexed}")
    return 0


def cmd_issues_query(args: argparse.Namespace) -> int:
    archive = Archive(args.archive)
    try:
        hits = archive.query_project_items(args.terms, limit=args.limit)
    finally:
        archive.close()
    if args.json:
        print_json([hit.to_dict() for hit in hits])
    else:
        for idx, hit in enumerate(hits, start=1):
            print(f"{idx}. {hit.repository}#{hit.number} {hit.title}")
            print(f"   {hit.url}")
            print(f"   kind={hit.kind} priority={hit.priority} updated_at={hit.updated_at}")
            if hit.labels:
                print(f"   labels={', '.join(hit.labels)}")
    return 0


def cmd_issues_report(args: argparse.Namespace) -> int:
    archive = Archive(args.archive)
    try:
        items = archive.project_items(limit=args.limit)
    finally:
        archive.close()
    report = build_project_radar(items, archive_path=args.archive, owner=args.owner)
    out_path = None
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(report, encoding="utf-8")
    payload = {
        "archive": args.archive,
        "out": str(out_path) if out_path else None,
        "item_count": len(items),
    }
    if args.json:
        print_json(payload)
    else:
        if out_path:
            print(f"project_radar: {out_path}")
        else:
            print(report)
    return 0


def cmd_brief(args: argparse.Namespace) -> int:
    search_plan: list[SearchPlanStep] = []
    web_results: list[SearchResult] = []
    if not args.no_web:
        with archive_env(args.archive):
            web_results, search_plan = search_with_plan(
                args.query,
                provider=args.provider,
                limit=args.web_limit,
                expand_queries=args.expand_queries,
                max_subqueries=args.max_subqueries,
            )
    archive = Archive(args.archive)
    try:
        repo_hits = archive.query_repos(args.query, limit=args.repo_limit)
        feed_hits = archive.query_feeds(args.query, limit=args.feed_limit) if args.feed_limit > 0 else []
    finally:
        archive.close()
    brief = build_brief(
        query=args.query,
        web_results=web_results,
        repo_hits=repo_hits,
        archive_path=args.archive,
        search_plan=search_plan,
        feed_hits=feed_hits,
    )
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(brief, encoding="utf-8")
    if args.json:
        print_json(
            {
                "query": args.query,
                "archive": args.archive,
                "out": args.out,
                "web_results": [result.to_dict() for result in web_results],
                "repo_hits": [hit.to_dict() for hit in repo_hits],
                "feed_hits": [hit.to_dict() for hit in feed_hits],
                "search_plan": [step.to_dict() for step in search_plan],
            }
        )
    else:
        if args.out:
            print(f"brief: {args.out}")
        else:
            print(brief)
    return 0


def cmd_investigate(args: argparse.Namespace) -> int:
    search_plan: list[SearchPlanStep] = []
    web_results: list[SearchResult] = []
    if not args.no_web:
        with archive_env(args.archive):
            web_results, search_plan = search_with_plan(
                args.query,
                provider=args.provider,
                limit=args.web_limit,
                expand_queries=args.expand_queries,
                max_subqueries=args.max_subqueries,
            )
    archive = Archive(args.archive)
    pages: list[PageSnapshot] = []
    try:
        repo_hits = archive.query_repos(args.query, limit=args.repo_limit)
        feed_hits = archive.query_feeds(args.query, limit=args.feed_limit) if args.feed_limit > 0 else []
        if web_results:
            archive.store_run(args.query, args.provider, web_results)
        for result in sort_web_candidates(web_results)[: max(args.read_top, 0)]:
            try:
                page = read_url(result.url, reader=args.reader)
            except Exception as exc:
                page = PageSnapshot(
                    url=result.url,
                    title=result.title,
                    content=f"Read failed: {exc}",
                    source="error",
                    fetched_at="",
                )
            pages.append(page)
            archive.upsert_page(page)
    finally:
        archive.close()

    report = build_investigation_report(
        query=args.query,
        provider=args.provider,
        archive_path=args.archive,
        web_results=web_results,
        repo_hits=repo_hits,
        pages=pages,
        search_plan=search_plan,
        feed_hits=feed_hits,
    )
    out_path = None
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(report, encoding="utf-8")

    if args.json:
        print_json(
            {
                "query": args.query,
                "archive": args.archive,
                "out": str(out_path) if out_path else None,
                "web_results": [result.to_dict() for result in web_results],
                "repo_hits": [hit.to_dict() for hit in repo_hits],
                "feed_hits": [hit.to_dict() for hit in feed_hits],
                "pages": [page.to_dict() for page in pages],
                "search_plan": [step.to_dict() for step in search_plan],
            }
        )
    else:
        if out_path:
            print(f"investigation: {out_path}")
        else:
            print(report)
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    for row in provider_status():
        print(f"{row['provider']}: {row['status']} - {row['detail']}")
    with sqlite3.connect(":memory:") as conn:
        conn.execute("CREATE VIRTUAL TABLE probe USING fts5(value)")
    print("sqlite_fts5: ok")
    return 0


def cmd_eval(args: argparse.Namespace) -> int:
    summary = run_eval(min_score=args.min_score, max_subqueries=args.max_subqueries)
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(build_eval_report(summary), encoding="utf-8")
    if args.json:
        print_json(summary.to_dict())
    else:
        print(f"score: {summary.score}")
        print(f"min_score: {summary.min_score}")
        print(f"passed: {str(summary.passed).lower()}")
        if args.out:
            print(f"report: {args.out}")
    return 0 if summary.passed else 1


def cmd_mcp(args: argparse.Namespace) -> int:
    from .mcp_server import main as mcp_main

    return mcp_main()


def print_results(results: list[SearchResult]) -> None:
    for result in results:
        print(f"{result.rank}. {result.title}")
        print(f"   {result.url}")
        if result.snippet:
            print(f"   {result.snippet}")
        print(f"   source={result.source} score={result.score}")


def print_json(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


@contextlib.contextmanager
def archive_env(path: str):
    previous = os.environ.get("KWR_ARCHIVE")
    os.environ["KWR_ARCHIVE"] = path
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop("KWR_ARCHIVE", None)
        else:
            os.environ["KWR_ARCHIVE"] = previous


if __name__ == "__main__":
    raise SystemExit(main())
