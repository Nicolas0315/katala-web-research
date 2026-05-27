from __future__ import annotations

from .models import PageSnapshot, SearchResult, utc_now_iso


def build_report(
    *,
    query: str,
    provider: str,
    results: list[SearchResult],
    pages: list[PageSnapshot],
    archive_path: str,
) -> str:
    lines = [
        f"# Web Research Report: {query}",
        "",
        f"- generated_at: {utc_now_iso()}",
        f"- provider: {provider}",
        f"- archive: `{archive_path}`",
        f"- results: {len(results)}",
        f"- pages_read: {len(pages)}",
        "",
        "## Ranked Results",
        "",
    ]
    for result in results:
        lines.extend(
            [
                f"### {result.rank}. {result.title}",
                "",
                f"- url: {result.url}",
                f"- source: {result.source}",
                f"- score: {result.score}",
                f"- published_at: {result.published_at or 'unknown'}",
                f"- snippet: {result.snippet or 'none'}",
                "",
            ]
        )
    if pages:
        lines.extend(["## Captured Pages", ""])
        for page in pages:
            excerpt = page.content[:700].replace("\n", " ").strip()
            lines.extend(
                [
                    f"### {page.title}",
                    "",
                    f"- url: {page.url}",
                    f"- reader: {page.source}",
                    f"- fetched_at: {page.fetched_at}",
                    "",
                    excerpt,
                    "",
                ]
            )
    return "\n".join(lines).rstrip() + "\n"

