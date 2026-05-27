from __future__ import annotations

import re
from urllib.parse import urlparse

from .models import SearchResult


TOKEN_RE = re.compile(r"[A-Za-z0-9_+-]{2,}|[\u3040-\u30ff\u3400-\u9fff]{1,}")


def query_tokens(query: str) -> set[str]:
    return {token.lower() for token in TOKEN_RE.findall(query)}


def rank_results(query: str, results: list[SearchResult]) -> list[SearchResult]:
    tokens = query_tokens(query)
    seen: set[str] = set()
    ranked: list[SearchResult] = []
    for result in results:
        normalized = _dedupe_key(result.url)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        haystack = f"{result.title} {result.snippet}".lower()
        overlap = sum(1 for token in tokens if token in haystack)
        source_weight = 0.25 if result.source in {"github", "jina"} else 0.0
        result.score = round(overlap + source_weight + max(0, 20 - result.rank) / 100, 3)
        ranked.append(result)
    ranked.sort(key=lambda item: (-item.score, item.rank, item.url))
    for idx, result in enumerate(ranked, start=1):
        result.rank = idx
    return ranked


def _dedupe_key(url: str) -> str:
    parsed = urlparse(url)
    if not parsed.netloc:
        return ""
    path = parsed.path.rstrip("/") or "/"
    return f"{parsed.scheme.lower()}://{parsed.netloc.lower()}{path}"

