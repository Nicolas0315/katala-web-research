from __future__ import annotations

from .models import FeedHit, PageSnapshot, RepoHit, SearchResult, utc_now_iso
from .planner import SearchPlanStep, format_search_plan
from .source_quality import classify_url
from .source_registry import source_registry_metadata


def sort_web_candidates(results: list[SearchResult]) -> list[SearchResult]:
    return sorted(results, key=_candidate_sort_key)


def build_investigation_report(
    *,
    query: str,
    provider: str,
    archive_path: str,
    web_results: list[SearchResult],
    repo_hits: list[RepoHit],
    pages: list[PageSnapshot],
    search_plan: list[SearchPlanStep] | None = None,
    feed_hits: list[FeedHit] | None = None,
) -> str:
    feed_hits = feed_hits or []
    sorted_results = sort_web_candidates(web_results)
    captured_urls = {page.url for page in pages}
    lines = [
        f"# Investigation: {query}",
        "",
        f"- generated_at: {utc_now_iso()}",
        f"- provider: {provider}",
        f"- archive: `{archive_path}`",
        f"- web_results: {len(web_results)}",
        f"- repo_hits: {len(repo_hits)}",
        f"- feed_hits: {len(feed_hits)}",
        f"- pages_read: {len(pages)}",
        "",
        "## Source Strategy",
        "",
        "- Prefer official docs, primary code repositories, standards, papers, and institutional sources.",
        "- Use local repository evidence to compare prior art before adopting external behavior.",
        "- Store full-page captures only for selected URLs; keep raw runtime artifacts out of Git.",
        "",
    ]
    if search_plan:
        lines.extend(["## Search Plan", ""])
        for step in format_search_plan(search_plan):
            lines.append(f"- {step}")
        lines.append("")
    lines.extend(["## Evidence Matrix", ""])
    if sorted_results:
        for result in sorted_results:
            source_type, quality = classify_url(result.url)
            captured = "yes" if result.url in captured_urls else "no"
            registry = source_registry_metadata(result.url)
            registry_suffix = f" registry={registry['registry_source']}" if registry else ""
            lines.append(
                f"- `{source_type}` quality={quality} captured={captured} score={result.score}{registry_suffix}: {result.url}"
            )
        lines.append("")
    else:
        lines.extend(["No web evidence.", ""])
    lines.extend(["## Best Web Candidates", ""])
    if sorted_results:
        for result in sorted_results:
            source_type, quality = classify_url(result.url)
            lines.extend(
                [
                    f"### {result.title}",
                    "",
                    f"- url: {result.url}",
                    f"- source_type: {source_type}",
                    f"- quality_score: {quality}",
                    f"- search_score: {result.score}",
                    f"- published_at: {result.published_at or 'unknown'}",
                ]
            )
            lines.extend(_registry_lines(result.url))
            lines.extend([f"- snippet: {result.snippet or 'none'}", ""])
    else:
        lines.extend(["No web results.", ""])

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
        lines.extend(["No local repository evidence found in the selected archive.", ""])

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

    lines.extend(["## Captured Pages", ""])
    if pages:
        for page in pages:
            excerpt = page.content[:900].replace("\n", " ").strip()
            lines.extend(
                [
                    f"### {page.title}",
                    "",
                    f"- url: {page.url}",
                    f"- reader: {page.source}",
                    f"- fetched_at: {page.fetched_at or 'unknown'}",
                    f"- status_code: {page.status_code or 'unknown'}",
                    "",
                    excerpt or "No extractable content.",
                    "",
                ]
            )
    else:
        lines.extend(["No pages captured.", ""])

    lines.extend(
        [
            "## Operator Checklist",
            "",
            "- Verify claims against the captured pages or the linked primary sources before publication.",
            "- Re-run `kwr repos scan` before relying on local corpus evidence if repositories changed.",
            "- Use `kwr query` and `kwr repos query` for follow-up retrieval from the same archive.",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _candidate_sort_key(result: SearchResult) -> tuple[int, float, int, str]:
    _source_type, quality = classify_url(result.url)
    return (-quality, -result.score, result.rank, result.url)


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
