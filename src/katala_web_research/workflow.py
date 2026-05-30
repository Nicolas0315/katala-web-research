from __future__ import annotations

import contextlib
import os
from math import ceil

from .models import SearchResult
from .planner import SearchPlanStep, build_search_plan
from .providers import search
from .rank import rank_results


def search_with_plan(
    query: str,
    *,
    provider: str,
    limit: int,
    expand_queries: bool = False,
    max_subqueries: int = 4,
    archive_path: str | None = None,
    year: int | None = None,
) -> tuple[list[SearchResult], list[SearchPlanStep]]:
    with _archive_env(archive_path):
        if not expand_queries:
            return search(query, provider=provider, limit=limit), []

        plan = build_search_plan(query, max_subqueries=max_subqueries, year=year)
        if not plan:
            return search(query, provider=provider, limit=limit), []

        per_query_limit = max(2, ceil(max(limit, 1) / len(plan)) + 2)
        combined: list[SearchResult] = []
        for step in plan:
            combined.extend(search(step.query, provider=provider, limit=per_query_limit))
        return rank_results(query, combined)[:limit], plan


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
