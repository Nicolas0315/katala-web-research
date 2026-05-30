from __future__ import annotations

from dataclasses import replace

from .models import SearchResult
from .rank import _dedupe_key, rank_results


def reciprocal_rank_fusion(
    result_lists: list[list[SearchResult]],
    *,
    rrf_k: int = 60,
    engine_health: dict[str, float] | None = None,
) -> list[SearchResult]:
    engine_health = engine_health or {}
    scores: dict[str, float] = {}
    best: dict[str, SearchResult] = {}
    engine_ranks: dict[str, dict[str, int]] = {}
    engine_health_by_key: dict[str, dict[str, float]] = {}

    for engine_index, results in enumerate(result_lists, start=1):
        for fallback_rank, result in enumerate(results, start=1):
            key = _dedupe_key(result.url)
            if not key:
                continue
            source = result.source or f"engine_{engine_index}"
            engine_rank = result.rank or fallback_rank
            health_score = _engine_health_score(source, result, engine_health)
            scores[key] = scores.get(key, 0.0) + health_score / (rrf_k + engine_rank)
            engine_ranks.setdefault(key, {})[source] = min(
                engine_rank, engine_ranks.get(key, {}).get(source, engine_rank)
            )
            by_source = engine_health_by_key.setdefault(key, {})
            by_source[source] = max(by_source.get(source, health_score), health_score)
            current = best.get(key)
            if current is None or engine_rank < (current.rank or fallback_rank):
                best[key] = replace(result, metadata=dict(result.metadata))

    fused = []
    for key, result in best.items():
        metadata = dict(result.metadata)
        metadata["rrf_score"] = round(scores[key], 6)
        metadata["engine_ranks"] = dict(sorted(engine_ranks[key].items()))
        metadata["engine_health"] = dict(sorted(engine_health_by_key[key].items()))
        metadata["source_count"] = len(engine_ranks[key])
        fused.append(replace(result, metadata=metadata))

    fused.sort(
        key=lambda item: (
            -float(item.metadata.get("rrf_score", 0.0)),
            item.rank,
            item.url,
        )
    )
    for idx, result in enumerate(fused, start=1):
        result.rank = idx
    return fused


def fuse_and_rank(
    query: str,
    result_lists: list[list[SearchResult]],
    *,
    limit: int = 10,
    rrf_k: int = 60,
    engine_health: dict[str, float] | None = None,
) -> list[SearchResult]:
    return rank_results(
        query,
        reciprocal_rank_fusion(result_lists, rrf_k=rrf_k, engine_health=engine_health),
    )[:limit]


def _engine_health_score(
    source: str, result: SearchResult, engine_health: dict[str, float]
) -> float:
    raw = engine_health.get(source, result.metadata.get("engine_health_score", 1.0))
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return 1.0
    return max(0.0, min(value, 1.0))
