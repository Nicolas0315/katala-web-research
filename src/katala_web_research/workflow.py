from __future__ import annotations

import contextlib
import os
from math import ceil

from .models import SearchResult
from .planner import SearchPlanStep, build_search_plan
from .providers import search
from .rank import rank_results
from .reader import read_url


def search_with_plan(
    query: str,
    *,
    provider: str,
    limit: int,
    expand_queries: bool = False,
    max_subqueries: int = 4,
    archive_path: str | None = None,
    year: int | None = None,
    candidate_multiplier: float = 1.0,
) -> tuple[list[SearchResult], list[SearchPlanStep]]:
    candidate_limit = _candidate_limit(limit, candidate_multiplier)
    with _archive_env(archive_path):
        if not expand_queries:
            return rank_results(query, search(query, provider=provider, limit=candidate_limit))[:limit], []

        plan = build_search_plan(query, max_subqueries=max_subqueries, year=year)
        if not plan:
            return rank_results(query, search(query, provider=provider, limit=candidate_limit))[:limit], []

        per_query_limit = max(2, ceil(max(candidate_limit, 1) / len(plan)) + 2)
        combined: list[SearchResult] = []
        for step in plan:
            combined.extend(search(step.query, provider=provider, limit=per_query_limit))
        return rank_results(query, combined)[:limit], plan


def enrich_search_results(
    query: str,
    results: list[SearchResult],
    *,
    read_top: int = 0,
    reader: str = "auto",
) -> list[SearchResult]:
    if read_top <= 0 or not results:
        return results

    enriched: list[SearchResult] = []
    for index, result in enumerate(results):
        if index >= read_top:
            enriched.append(result)
            continue
        try:
            page = read_url(result.url, reader=reader)
        except Exception as exc:
            metadata = dict(result.metadata)
            metadata["read_status"] = "error"
            metadata["read_error_kind"] = exc.__class__.__name__
            enriched.append(_copy_result(result, metadata=metadata))
            continue
        metadata = dict(result.metadata)
        metadata["read_status"] = "ok"
        metadata["read_source"] = page.source
        metadata["read_status_code"] = page.status_code
        snippet = _snippet_from_page(page.content)
        enriched.append(
            _copy_result(
                result,
                title=result.title or page.title,
                snippet=snippet or result.snippet,
                metadata=metadata,
            )
        )
    return rank_results(query, enriched)


@contextlib.contextmanager
def _archive_env(path: str | None):
    if not path:
        yield
        return
    previous = os.environ.get("KWR_ARCHIVE")
    os.environ["KWR_ARCHIVE"] = path
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop("KWR_ARCHIVE", None)
        else:
            os.environ["KWR_ARCHIVE"] = previous


def _snippet_from_page(content: str, *, max_chars: int = 700) -> str:
    return " ".join(content.split())[:max_chars]


def _candidate_limit(limit: int, multiplier: float) -> int:
    return max(limit, ceil(max(limit, 1) * max(multiplier, 1.0)))


def _copy_result(
    result: SearchResult,
    *,
    title: str | None = None,
    snippet: str | None = None,
    metadata: dict | None = None,
) -> SearchResult:
    return SearchResult(
        title=result.title if title is None else title,
        url=result.url,
        snippet=result.snippet if snippet is None else snippet,
        source=result.source,
        published_at=result.published_at,
        rank=result.rank,
        score=result.score,
        metadata=dict(result.metadata) if metadata is None else metadata,
    )
