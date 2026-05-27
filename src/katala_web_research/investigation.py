from __future__ import annotations

from .models import PageSnapshot, RepoHit, SearchResult, utc_now_iso
from .source_quality import classify_url


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
) -> str:
    sorted_results = sort_web_candidates(web_results)
    lines = [
        f"# Investigation: {query}",
        "",
        f"- generated_at: {utc_now_iso()}",
        f"- provider: {provider}",
        f"- archive: `{archive_path}`",
        f"- web_results: {len(web_results)}",
        f"- repo_hits: {len(repo_hits)}",
        f"- pages_read: {len(pages)}",
        "",
        "## Source Strategy",
        "",
        "- Prefer official docs, primary code repositories, standards, papers, and institutional sources.",
        "- Use local repository evidence to compare prior art before adopting external behavior.",
        "- Store full-page captures only for selected URLs; keep raw runtime artifacts out of Git.",
        "",
        "## Best Web Candidates",
        "",
    ]
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
                    f"- snippet: {result.snippet or 'none'}",
                    "",
                ]
            )
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
