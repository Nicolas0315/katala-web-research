from __future__ import annotations

from urllib.parse import urlparse


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
PRIMARY_RESEARCH_HOSTS = {"arxiv.org", "openreview.net", "pubmed.ncbi.nlm.nih.gov", "doi.org"}


def classify_url(url: str) -> tuple[str, int]:
    host = urlparse(url).netloc.lower().removeprefix("www.")
    if host in OFFICIAL_DOC_HOSTS:
        return "official-docs", 100
    if host in PRIMARY_CODE_HOSTS:
        return "primary-code", 85
    if host in PRIMARY_RESEARCH_HOSTS:
        return "primary-research", 85
    if host.endswith(".gov") or host.endswith(".edu"):
        return "institutional", 75
    if "docs" in host or "developer" in host:
        return "vendor-docs", 70
    return "web", 50

