from __future__ import annotations

from .models import RepoHit, SearchResult, utc_now_iso
from .source_quality import classify_url


def build_brief(
    *,
    query: str,
    web_results: list[SearchResult],
    repo_hits: list[RepoHit],
    archive_path: str,
) -> str:
    lines = [
        f"# Research Brief: {query}",
        "",
        f"- generated_at: {utc_now_iso()}",
        f"- archive: `{archive_path}`",
        f"- web_results: {len(web_results)}",
        f"- repo_hits: {len(repo_hits)}",
        "",
        "## Best Web Candidates",
        "",
    ]
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
                    f"- snippet: {result.snippet or 'none'}",
                    "",
                ]
            )
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

