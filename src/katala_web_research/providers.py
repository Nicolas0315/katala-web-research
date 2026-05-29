from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, replace
from html.parser import HTMLParser
from typing import Protocol
from urllib.parse import quote_plus, urlencode

from .archive import Archive, DEFAULT_ARCHIVE
from .fusion import fuse_and_rank
from .http import FetchError, fetch_url
from .models import SearchResult
from .rank import rank_results
from .text import collapse_space, normalize_url


class SearchProvider(Protocol):
    name: str

    def search(self, query: str, *, limit: int = 10) -> list[SearchResult]:
        ...


class DuckDuckGoSearch:
    name = "ddg"

    def search(self, query: str, *, limit: int = 10) -> list[SearchResult]:
        url = "https://html.duckduckgo.com/html/?" + urlencode({"q": query})
        response = fetch_url(url, headers={"Accept": "text/html"})
        parser = _DuckDuckGoHTMLParser()
        parser.feed(response.text)
        parser.close()
        results = parser.results[:limit]
        for idx, result in enumerate(results, start=1):
            result.rank = idx
        return rank_results(query, results)


class GitHubRepoSearch:
    name = "github"

    def search(self, query: str, *, limit: int = 10) -> list[SearchResult]:
        if shutil.which("gh"):
            gh_results = self._search_with_gh(query, limit)
            if gh_results:
                return rank_results(query, gh_results)
        return rank_results(query, self._search_with_rest(query, limit))

    def _search_with_gh(self, query: str, limit: int) -> list[SearchResult]:
        cmd = [
            "gh",
            "search",
            "repos",
            query,
            "--limit",
            str(limit),
            "--json",
            "fullName,description,url,stargazersCount,updatedAt,isFork",
        ]
        completed = subprocess.run(cmd, text=True, capture_output=True, check=False)
        if completed.returncode != 0:
            return []
        items = json.loads(completed.stdout or "[]")
        return [
            SearchResult(
                title=item.get("fullName") or item.get("url") or "",
                url=item.get("url") or "",
                snippet=_github_snippet(item),
                source=self.name,
                published_at=item.get("updatedAt"),
                rank=idx,
            )
            for idx, item in enumerate(items, start=1)
            if item.get("url")
        ]

    def _search_with_rest(self, query: str, limit: int) -> list[SearchResult]:
        url = "https://api.github.com/search/repositories?" + urlencode(
            {"q": query, "sort": "stars", "order": "desc", "per_page": min(limit, 30)}
        )
        headers = {"Accept": "application/vnd.github+json"}
        token = os.environ.get("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        response = fetch_url(url, headers=headers)
        payload = json.loads(response.text)
        results = []
        for idx, item in enumerate(payload.get("items", []), start=1):
            results.append(
                SearchResult(
                    title=item.get("full_name") or item.get("html_url") or "",
                    url=item.get("html_url") or "",
                    snippet=_github_snippet(
                        {
                            "description": item.get("description"),
                            "stargazersCount": item.get("stargazers_count"),
                            "updatedAt": item.get("updated_at"),
                            "isFork": item.get("fork"),
                        }
                    ),
                    source=self.name,
                    published_at=item.get("updated_at"),
                    rank=idx,
                )
            )
        return results


class FeedSearch:
    name = "feed"

    def search(self, query: str, *, limit: int = 10) -> list[SearchResult]:
        archive = Archive(os.environ.get("KWR_ARCHIVE", str(DEFAULT_ARCHIVE)))
        try:
            hits = archive.query_feeds(query, limit=limit)
        finally:
            archive.close()
        results = [
            SearchResult(
                title=hit.title,
                url=hit.url,
                snippet=hit.snippet,
                source=self.name,
                published_at=hit.published_at,
                rank=idx,
                metadata={
                    "source_url": hit.source_url,
                    "source_title": hit.source_title,
                    "fetched_at": hit.fetched_at,
                    "archive_rank": hit.rank,
                },
            )
            for idx, hit in enumerate(hits, start=1)
        ]
        return rank_results(query, results)


class JinaSearch:
    name = "jina"

    def search(self, query: str, *, limit: int = 10) -> list[SearchResult]:
        token = os.environ.get("JINA_API_KEY")
        if not token:
            raise FetchError("JINA_API_KEY is required for Jina search")
        url = "https://s.jina.ai/?" + urlencode({"q": query})
        response = fetch_url(
            url,
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        )
        payload = json.loads(response.text)
        data = payload.get("data", payload if isinstance(payload, list) else [])
        results = []
        for idx, item in enumerate(data[:limit], start=1):
            results.append(
                SearchResult(
                    title=item.get("title") or item.get("url") or "",
                    url=item.get("url") or "",
                    snippet=item.get("description") or item.get("content") or "",
                    source=self.name,
                    published_at=item.get("publishedTime") or item.get("published_at"),
                    rank=idx,
                )
            )
        return rank_results(query, results)


class SearxngSearch:
    name = "searxng"

    def search(self, query: str, *, limit: int = 10) -> list[SearchResult]:
        base_url = os.environ.get("KWR_SEARXNG_URL", "").rstrip("/")
        if not base_url:
            raise FetchError("KWR_SEARXNG_URL is required for SearXNG search")
        url = base_url + "/search?" + urlencode(_searxng_params(query))
        response = fetch_url(url, headers={"Accept": "application/json"})
        payload = json.loads(response.text)
        results = []
        for idx, item in enumerate(payload.get("results", [])[:limit], start=1):
            results.append(
                SearchResult(
                    title=item.get("title") or item.get("url") or "",
                    url=item.get("url") or "",
                    snippet=item.get("content") or "",
                    source=self.name,
                    published_at=item.get("publishedDate"),
                    rank=idx,
                )
            )
        return rank_results(query, results)


class BraveSearch:
    name = "brave"

    def search(self, query: str, *, limit: int = 10) -> list[SearchResult]:
        token = os.environ.get("BRAVE_SEARCH_API_KEY")
        if not token:
            raise FetchError("BRAVE_SEARCH_API_KEY is required for Brave search")
        url = "https://api.search.brave.com/res/v1/web/search?" + urlencode(
            {"q": query, "count": min(limit, 20)}
        )
        response = fetch_url(
            url,
            headers={
                "Accept": "application/json",
                "X-Subscription-Token": token,
            },
        )
        payload = json.loads(response.text)
        web_results = (payload.get("web") or {}).get("results", [])
        results = []
        for idx, item in enumerate(web_results[:limit], start=1):
            results.append(
                SearchResult(
                    title=item.get("title") or item.get("url") or "",
                    url=item.get("url") or "",
                    snippet=item.get("description") or "",
                    source=self.name,
                    published_at=item.get("age"),
                    rank=idx,
                )
            )
        return rank_results(query, results)


class OpenAlexSearch:
    name = "openalex"

    def search(self, query: str, *, limit: int = 10) -> list[SearchResult]:
        token = _secret_env("OPENALEX_API_KEY")
        if not token:
            raise FetchError("OPENALEX_API_KEY is required for OpenAlex search")
        url = "https://api.openalex.org/works?" + urlencode(
            {
                "api_key": token,
                "search": query,
                "per_page": min(limit, 100),
                "sort": "relevance_score:desc",
                "select": ",".join(
                    [
                        "id",
                        "doi",
                        "title",
                        "display_name",
                        "publication_year",
                        "publication_date",
                        "type",
                        "cited_by_count",
                        "is_retracted",
                        "open_access",
                        "primary_location",
                        "abstract_inverted_index",
                    ]
                ),
            }
        )
        response = fetch_url(url, headers={"Accept": "application/json"})
        payload = json.loads(response.text)
        results = []
        for idx, item in enumerate(payload.get("results", [])[:limit], start=1):
            results.append(
                SearchResult(
                    title=item.get("display_name") or item.get("title") or item.get("id") or "",
                    url=_openalex_url(item),
                    snippet=_openalex_snippet(item),
                    source=self.name,
                    published_at=item.get("publication_date") or _year_as_date(item.get("publication_year")),
                    rank=idx,
                )
            )
        return rank_results(query, results)


class MetaSearch:
    name = "meta"

    def search(self, query: str, *, limit: int = 10) -> list[SearchResult]:
        profile = _meta_profile()
        provider_names = [name for name in _meta_provider_names(profile) if name in PROVIDERS]
        if not provider_names:
            return []
        result_lists: list[list[SearchResult]] = []
        runs: list[_MetaEngineRun] = []
        per_engine_limit = max(2, min(limit, 8))
        with ThreadPoolExecutor(max_workers=min(len(provider_names), 4)) as executor:
            futures = {
                executor.submit(
                    _run_meta_provider,
                    name,
                    _rewrite_query_for_provider(query, provider=name, profile=profile),
                    per_engine_limit,
                ): name
                for name in provider_names
            }
            for future in as_completed(futures):
                try:
                    results, run = future.result()
                except Exception as exc:
                    run = _MetaEngineRun(
                        provider=futures[future],
                        status="error",
                        latency_ms=0,
                        result_count=0,
                        health_score=0.0,
                        error_kind=exc.__class__.__name__,
                    )
                    results = []
                runs.append(run)
                if results:
                    result_lists.append(results)
        ranked = fuse_and_rank(
            query,
            result_lists,
            limit=limit,
            engine_health={run.provider: run.health_score for run in runs},
        )
        return [
            _annotate_meta_result(
                result,
                profile=profile,
                provider_names=provider_names,
                runs=runs,
            )
            for result in ranked
        ]


@dataclass(slots=True, frozen=True)
class _MetaEngineRun:
    provider: str
    status: str
    latency_ms: int
    result_count: int
    health_score: float
    error_kind: str = ""

    def to_dict(self) -> dict[str, str | int | float]:
        return asdict(self)


META_PROFILES: dict[str, tuple[str, ...]] = {
    "broad": ("ddg", "github", "openalex", "searxng"),
    "docs": ("ddg", "searxng", "github", "jina"),
    "scholarly": ("openalex", "searxng", "ddg"),
    "code": ("github", "searxng", "ddg"),
    "fresh": ("ddg", "searxng", "brave"),
    "local": ("feed", "ddg", "github"),
    "monitoring": ("feed", "ddg", "github"),
}


PROVIDERS: dict[str, SearchProvider] = {
    "brave": BraveSearch(),
    "ddg": DuckDuckGoSearch(),
    "feed": FeedSearch(),
    "github": GitHubRepoSearch(),
    "meta": MetaSearch(),
    "openalex": OpenAlexSearch(),
    "jina": JinaSearch(),
    "searxng": SearxngSearch(),
}


def _run_meta_provider(
    provider: str, rewritten_query: str, limit: int
) -> tuple[list[SearchResult], _MetaEngineRun]:
    started = time.perf_counter()
    try:
        results = get_provider(provider).search(rewritten_query, limit=limit)
        latency_ms = _elapsed_ms(started)
        status = "ok" if results else "empty"
        run = _MetaEngineRun(
            provider=provider,
            status=status,
            latency_ms=latency_ms,
            result_count=len(results),
            health_score=_meta_engine_health_score(
                status=status,
                result_count=len(results),
                latency_ms=latency_ms,
                requested=limit,
            ),
        )
        return [_annotate_engine_result(result, run) for result in results], run
    except Exception as exc:
        latency_ms = _elapsed_ms(started)
        run = _MetaEngineRun(
            provider=provider,
            status="error",
            latency_ms=latency_ms,
            result_count=0,
            health_score=0.0,
            error_kind=exc.__class__.__name__,
        )
        return [], run


def _annotate_engine_result(result: SearchResult, run: _MetaEngineRun) -> SearchResult:
    metadata = dict(result.metadata)
    metadata["engine_health_score"] = run.health_score
    metadata["engine_latency_ms"] = run.latency_ms
    metadata["engine_result_count"] = run.result_count
    return replace(result, metadata=metadata)


def _annotate_meta_result(
    result: SearchResult,
    *,
    profile: str,
    provider_names: list[str],
    runs: list[_MetaEngineRun],
) -> SearchResult:
    metadata = dict(result.metadata)
    metadata["meta_profile"] = profile
    metadata["meta_providers"] = list(provider_names)
    metadata["meta_engine_runs"] = [
        run.to_dict() for run in sorted(runs, key=lambda item: item.provider)
    ]
    return replace(result, metadata=metadata)


def _elapsed_ms(started: float) -> int:
    return max(0, round((time.perf_counter() - started) * 1000))


def _meta_engine_health_score(
    *,
    status: str,
    result_count: int,
    latency_ms: int,
    requested: int,
) -> float:
    if status == "error":
        return 0.0
    if status == "empty":
        return 0.35
    useful_ratio = min(result_count / max(requested, 1), 1.0)
    score = 0.75 + 0.25 * useful_ratio
    if latency_ms >= 5_000:
        score -= 0.25
    elif latency_ms >= 2_000:
        score -= 0.15
    elif latency_ms >= 1_000:
        score -= 0.05
    return round(max(0.1, min(score, 1.0)), 3)


def get_provider(name: str) -> SearchProvider:
    if name not in PROVIDERS:
        known = ", ".join(sorted(PROVIDERS))
        raise ValueError(f"unknown provider {name!r}; expected one of: {known}")
    return PROVIDERS[name]


def search(query: str, *, provider: str = "ddg", limit: int = 10) -> list[SearchResult]:
    return get_provider(provider).search(query, limit=limit)


def provider_status() -> list[dict[str, str]]:
    return [
        {"provider": "ddg", "status": "ok", "detail": "no-key HTML search fallback"},
        {
            "provider": "feed",
            "status": "ok",
            "detail": "local RSS/Atom/JSON Feed archive; set KWR_ARCHIVE to override path",
        },
        {"provider": "github", "status": "ok", "detail": "gh CLI or GitHub REST; GITHUB_TOKEN optional"},
        {
            "provider": "jina",
            "status": "ok" if os.environ.get("JINA_API_KEY") else "off",
            "detail": "JINA_API_KEY optional; reader does not require it",
        },
        {
            "provider": "searxng",
            "status": "ok" if os.environ.get("KWR_SEARXNG_URL") else "off",
            "detail": "KWR_SEARXNG_URL optional; uses /search?q=...&format=json",
        },
        {
            "provider": "brave",
            "status": "ok" if os.environ.get("BRAVE_SEARCH_API_KEY") else "off",
            "detail": "BRAVE_SEARCH_API_KEY optional; uses Brave Web Search API",
        },
        {
            "provider": "openalex",
            "status": "ok" if _secret_env("OPENALEX_API_KEY") else "off",
            "detail": "OPENALEX_API_KEY optional; uses scholarly works search",
        },
        {
            "provider": "meta",
            "status": "ok",
            "detail": f"health-aware metasearch fan-out; profile={_meta_profile()} providers={','.join(_meta_provider_names(_meta_profile()))}",
        },
    ]


def _meta_profile() -> str:
    value = os.environ.get("KWR_META_PROFILE", "broad").strip().lower()
    return value if value in META_PROFILES else "broad"


def _meta_provider_names(profile: str) -> list[str]:
    raw = os.environ.get("KWR_META_PROVIDERS", "").strip()
    if raw:
        return [name.strip() for name in raw.split(",") if name.strip() and name.strip() != "meta"]
    return list(META_PROFILES.get(profile, META_PROFILES["broad"]))


def _rewrite_query_for_provider(query: str, *, provider: str, profile: str) -> str:
    if provider == "openalex":
        if profile == "scholarly":
            return f"{query} paper benchmark evaluation"
        if profile == "broad":
            return f"{query} scholarly research"
    if provider == "github" and profile == "code":
        return f"{query} implementation library"
    if provider in {"ddg", "searxng"} and profile == "docs":
        return f"{query} official documentation"
    if provider in {"ddg", "searxng", "brave"} and profile == "fresh":
        return f"{query} latest"
    return query


def _searxng_params(query: str) -> dict[str, str]:
    params = {"q": query, "format": "json"}
    env_to_param = {
        "KWR_SEARXNG_CATEGORIES": "categories",
        "KWR_SEARXNG_ENGINES": "engines",
        "KWR_SEARXNG_LANGUAGE": "language",
        "KWR_SEARXNG_TIME_RANGE": "time_range",
        "KWR_SEARXNG_SAFESEARCH": "safesearch",
    }
    for env_name, param_name in env_to_param.items():
        value = os.environ.get(env_name, "").strip()
        if value:
            params[param_name] = value
    return params


class _DuckDuckGoHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.results: list[SearchResult] = []
        self._in_title = False
        self._in_snippet = False
        self._current_title: list[str] = []
        self._current_url = ""
        self._current_snippet: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = dict(attrs)
        classes = set((attr.get("class") or "").split())
        if tag == "a" and "result__a" in classes:
            self._flush()
            self._in_title = True
            self._current_url = normalize_url(attr.get("href") or "")
        elif "result__snippet" in classes:
            self._in_snippet = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._in_title:
            self._in_title = False
        if tag in {"a", "div"} and self._in_snippet:
            self._in_snippet = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self._current_title.append(data)
        elif self._in_snippet:
            self._current_snippet.append(data)

    def close(self) -> None:
        self._flush()
        super().close()

    def _flush(self) -> None:
        title = collapse_space(" ".join(self._current_title))
        if title and self._current_url:
            self.results.append(
                SearchResult(
                    title=title,
                    url=self._current_url,
                    snippet=collapse_space(" ".join(self._current_snippet)),
                    source="ddg",
                )
            )
        self._current_title = []
        self._current_url = ""
        self._current_snippet = []


def _github_snippet(item: dict) -> str:
    parts = []
    if item.get("description"):
        parts.append(str(item["description"]))
    if item.get("stargazersCount") is not None:
        parts.append(f"stars={item['stargazersCount']}")
    if item.get("updatedAt"):
        parts.append(f"updated={item['updatedAt']}")
    if item.get("isFork"):
        parts.append("fork=true")
    return " | ".join(parts)


def _secret_env(name: str) -> str:
    value = os.environ.get(name, "")
    if not value.startswith("op://"):
        return value
    if not shutil.which("op"):
        return ""
    completed = subprocess.run(["op", "read", value], text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        return ""
    return completed.stdout.strip()


def _openalex_url(item: dict) -> str:
    primary_location = item.get("primary_location") or {}
    if primary_location.get("landing_page_url"):
        return str(primary_location["landing_page_url"])
    if item.get("doi"):
        return str(item["doi"])
    return str(item.get("id") or "")


def _openalex_snippet(item: dict) -> str:
    parts = []
    abstract = _abstract_from_inverted_index(item.get("abstract_inverted_index"))
    if abstract:
        parts.append(abstract[:420])
    if item.get("publication_year"):
        parts.append(f"year={item['publication_year']}")
    if item.get("type"):
        parts.append(f"type={item['type']}")
    if item.get("cited_by_count") is not None:
        parts.append(f"citations={item['cited_by_count']}")
    if item.get("is_retracted"):
        parts.append("retracted=true")
    open_access = item.get("open_access") or {}
    if open_access.get("is_oa") is not None:
        parts.append(f"oa={str(open_access.get('is_oa')).lower()}")
    primary_location = item.get("primary_location") or {}
    source = primary_location.get("source") or {}
    if source.get("display_name"):
        parts.append(f"source={source['display_name']}")
    return " | ".join(parts)


def _abstract_from_inverted_index(value: object) -> str:
    if not isinstance(value, dict):
        return ""
    positions: list[tuple[int, str]] = []
    for word, indexes in value.items():
        if not isinstance(word, str) or not isinstance(indexes, list):
            continue
        for index in indexes:
            if isinstance(index, int):
                positions.append((index, word))
    return " ".join(word for _idx, word in sorted(positions))


def _year_as_date(value: object) -> str | None:
    if isinstance(value, int):
        return f"{value}-01-01"
    return None
