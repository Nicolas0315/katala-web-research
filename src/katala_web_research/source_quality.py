from __future__ import annotations

from urllib.parse import urlparse

from .models import SearchResult


OFFICIAL_DOC_HOSTS = {
    "docs.github.com",
    "developers.openai.com",
    "platform.openai.com",
    "docs.anthropic.com",
    "ai.google.dev",
    "cloud.google.com",
    "learn.microsoft.com",
    "developer.mozilla.org",
}

PRIMARY_CODE_HOSTS = {"github.com", "gitlab.com", "sourceforge.net"}
PRIMARY_RESEARCH_HOSTS = {
    "aclanthology.org",
    "arxiv.org",
    "doi.org",
    "openreview.net",
    "pubmed.ncbi.nlm.nih.gov",
    "semanticscholar.org",
}
ACCOUNTABLE_HOST_SUFFIXES = (".edu", ".gov")


def classify_url(url: str) -> tuple[str, int]:
    host = urlparse(url).netloc.lower().removeprefix("www.")
    if host in OFFICIAL_DOC_HOSTS:
        return "official-docs", 100
    if host in PRIMARY_CODE_HOSTS:
        return "primary-code", 85
    if host in PRIMARY_RESEARCH_HOSTS:
        return "primary-research", 85
    if host.endswith(ACCOUNTABLE_HOST_SUFFIXES):
        return "institutional", 75
    if "docs" in host or "developer" in host:
        return "vendor-docs", 70
    return "web", 50


def source_quality_score(query: str, result: SearchResult) -> float:
    from .rank import query_tokens

    _label, base_quality = classify_url(result.url)
    tokens = query_tokens(query)
    haystack = f"{result.title} {result.snippet}".lower()
    overlap = sum(1 for token in tokens if token in haystack)
    primary_bonus = 0.4 if base_quality >= 85 else 0.0
    title_bonus = 0.2 if any(token in result.title.lower() for token in tokens) else 0.0
    freshness_bonus = _freshness_bonus(result.published_at)
    return round(base_quality / 100 + overlap + primary_bonus + title_bonus + freshness_bonus, 3)


def _freshness_bonus(published_at: str | None) -> float:
    if not published_at:
        return 0.0
    if published_at.startswith("2026"):
        return 0.3
    if published_at.startswith("2025"):
        return 0.15
    return 0.0
