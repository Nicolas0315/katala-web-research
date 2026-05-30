from __future__ import annotations

from .models import FeedHit, RepoHit, SearchResult, utc_now_iso
from .planner import SearchPlanStep, format_search_plan
from .source_quality import classify_url
from .source_registry import source_registry_metadata


def build_brief(
    *,
    query: str,
    web_results: list[SearchResult],
    repo_hits: list[RepoHit],
    archive_path: str,
    search_plan: list[SearchPlanStep] | None = None,
    feed_hits: list[FeedHit] | None = None,
) -> str:
    feed_hits = feed_hits or []
    lines = [
        f"# Research Brief: {query}",
        "",
        f"- generated_at: {utc_now_iso()}",
        f"- archive: `{archive_path}`",
        f"- web_results: {len(web_results)}",
        f"- repo_hits: {len(repo_hits)}",
        f"- feed_hits: {len(feed_hits)}",
        "",
    ]
    if search_plan:
        lines.extend(["## Search Plan", ""])
        for step in format_search_plan(search_plan):
            lines.append(f"- {step}")
        lines.append("")
    lines.extend(["## Best Web Candidates", ""])
    if web_results:
        for result in sorted(web_results, key=_web_sort_key):
            label, quality = classify_url(result.url)
            lines.extend(
                [
                    f"### {result.title}",
                    "",
                    f"- url: {result.url}",
                    f"- source_type: {label}",
                    f"- quality_score: {quality}",
                    f"- search_score: {result.score}",
                ]
            )
            lines.extend(_registry_lines(result.url))
            lines.extend([f"- snippet: {result.snippet or 'none'}", ""])
    else:
        lines.extend(["No web search was run.", ""])

    lines.extend(["## Local Repository Evidence", ""])
    if repo_hits:
        for hit in repo_hits:
            lines.extend(
                [
                    f"### {hit.repo_name}/{hit.rel_path}",
                    "",
                    f"- repo_path: {hit.repo_path}",
                    f"- kind: {hit.kind}",
                    f"- indexed_at: {hit.indexed_at}",
                    f"- document_url: {hit.document_url}",
                    f"- snippet: {hit.snippet}",
                    "",
                ]
            )
    else:
        lines.extend(["No local repository hits found in the selected archive.", ""])

    lines.extend(["## Feed Evidence", ""])
    if feed_hits:
        for hit in feed_hits:
            lines.extend(
                [
                    f"### {hit.title}",
                    "",
                    f"- url: {hit.url}",
                    f"- feed: {hit.source_title or hit.source_url}",
                    f"- published_at: {hit.published_at or 'unknown'}",
                    f"- snippet: {hit.snippet or 'none'}",
                    "",
                ]
            )
    else:
        lines.extend(["No archived feed items matched in the selected archive.", ""])

    lines.extend(
        [
            "## Next Actions",
            "",
            "- Read the highest-quality official or primary source URLs first.",
            "- Compare local repository evidence before adopting external tool behavior.",
            "- Run `kwr collect` for the best URLs when full-page evidence should be archived.",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _web_sort_key(result: SearchResult) -> tuple[int, float, int]:
    _label, quality = classify_url(result.url)
    return (-quality, -result.score, result.rank)


def _registry_lines(url: str) -> list[str]:
    metadata = source_registry_metadata(url)
    if metadata is None:
        return []
    return [
        f"- registry_source: {metadata['registry_source']}",
        f"- registry_domain: {metadata['registry_domain']}",
        f"- registry_freshness: {metadata['registry_freshness']}",
        f"- registry_update_cadence: {metadata['registry_update_cadence']}",
        f"- registry_trust_score: {metadata['registry_trust_score']}",
        f"- bias_caveat: {metadata['bias_caveat']}",
    ]
