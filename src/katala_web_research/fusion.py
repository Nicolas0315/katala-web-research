from __future__ import annotations

from dataclasses import replace

from .models import SearchResult
from .rank import _dedupe_key, rank_results


def reciprocal_rank_fusion(
    result_lists: list[list[SearchResult]], *, rrf_k: int = 60
) -> list[SearchResult]:
    scores: dict[str, float] = {}
    best: dict[str, SearchResult] = {}
    engine_ranks: dict[str, dict[str, int]] = {}

    for engine_index, results in enumerate(result_lists, start=1):
        for fallback_rank, result in enumerate(results, start=1):
            key = _dedupe_key(result.url)
            if not key:
                continue
            source = result.source or f"engine_{engine_index}"
            engine_rank = result.rank or fallback_rank
            scores[key] = scores.get(key, 0.0) + 1 / (rrf_k + engine_rank)
            engine_ranks.setdefault(key, {})[source] = min(
                engine_rank, engine_ranks.get(key, {}).get(source, engine_rank)
            )
            current = best.get(key)
            if current is None or engine_rank < (current.rank or fallback_rank):
                best[key] = replace(result, metadata=dict(result.metadata))

    fused = []
    for key, result in best.items():
        metadata = dict(result.metadata)
        metadata["rrf_score"] = round(scores[key], 6)
        metadata["engine_ranks"] = dict(sorted(engine_ranks[key].items()))
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
    query: str, result_lists: list[list[SearchResult]], *, limit: int = 10, rrf_k: int = 60
) -> list[SearchResult]:
    return rank_results(query, reciprocal_rank_fusion(result_lists, rrf_k=rrf_k))[:limit]
