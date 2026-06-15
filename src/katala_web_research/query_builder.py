from __future__ import annotations

from dataclasses import dataclass, field
from urllib.parse import urlparse

DEFAULT_RESEARCH_DOMAINS = (
    "arxiv.org",
    "pubmed.ncbi.nlm.nih.gov",
    "nature.com",
    "science.org",
    "ieee.org",
    "acm.org",
    "springer.com",
    "wiley.com",
    "sciencedirect.com",
    "plos.org",
    "biorxiv.org",
    "medrxiv.org",
)


@dataclass(slots=True, frozen=True)
class SearchQueryBuild:
    query: str
    category_domains: dict[str, str] = field(default_factory=dict)
    pdf_requested: bool = False


def build_search_query(
    query: str,
    *,
    categories: list[str] | None = None,
    include_domains: list[str] | None = None,
    exclude_domains: list[str] | None = None,
) -> SearchQueryBuild:
    category_domains: dict[str, str] = {}
    filters: list[str] = []
    pdf_requested = False

    for category in categories or []:
        normalized = category.strip().lower()
        if normalized == "github":
            filters.append("site:github.com")
            category_domains["github.com"] = "github"
        elif normalized == "research":
            research_filters = []
            for domain in DEFAULT_RESEARCH_DOMAINS:
                research_filters.append(f"site:{domain}")
                category_domains[domain] = "research"
            filters.append("(" + " OR ".join(research_filters) + ")")
        elif normalized == "pdf":
            filters.append("filetype:pdf")
            pdf_requested = True

    include_filter = _domain_or_filter(include_domains or [])
    if include_filter:
        filters.append(include_filter)

    for domain in _clean_domains(exclude_domains or []):
        filters.append(f"-site:{domain}")

    if not filters:
        return SearchQueryBuild(query=query, category_domains=category_domains, pdf_requested=pdf_requested)
    return SearchQueryBuild(
        query=" ".join([query.strip(), *filters]).strip(),
        category_domains=category_domains,
        pdf_requested=pdf_requested,
    )


def categorize_url(
    url: str,
    *,
    category_domains: dict[str, str],
    pdf_requested: bool = False,
) -> str | None:
    parsed = urlparse(url)
    host = parsed.netloc.lower().removeprefix("www.")
    if not host:
        return None
    if pdf_requested and parsed.path.lower().endswith(".pdf"):
        return "pdf"
    if host == "github.com" or host.endswith(".github.com"):
        return "github"
    for domain, category in category_domains.items():
        normalized = domain.lower().removeprefix("www.")
        if host == normalized or host.endswith("." + normalized):
            return category
    return None


def _domain_or_filter(domains: list[str]) -> str:
    cleaned = _clean_domains(domains)
    if not cleaned:
        return ""
    if len(cleaned) == 1:
        return f"site:{cleaned[0]}"
    return "(" + " OR ".join(f"site:{domain}" for domain in cleaned) + ")"


def _clean_domains(domains: list[str]) -> list[str]:
    cleaned: list[str] = []
    for value in domains:
        domain = value.strip().lower()
        if not domain:
            continue
        if "://" in domain:
            domain = urlparse(domain).netloc.lower()
        domain = domain.removeprefix("www.").strip("/")
        if domain and domain not in cleaned:
            cleaned.append(domain)
    return cleaned
