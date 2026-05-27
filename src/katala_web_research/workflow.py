from __future__ import annotations

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
) -> tuple[list[SearchResult], list[SearchPlanStep]]:
    if not expand_queries:
        return search(query, provider=provider, limit=limit), []

    plan = build_search_plan(query, max_subqueries=max_subqueries)
    if not plan:
        return [], []

    per_query_limit = max(2, ceil(max(limit, 1) / len(plan)) + 2)
    combined: list[SearchResult] = []
    for step in plan:
        combined.extend(search(step.query, provider=provider, limit=per_query_limit))
    return rank_results(query, combined)[:limit], plan
