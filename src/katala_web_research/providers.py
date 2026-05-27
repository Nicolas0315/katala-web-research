from __future__ import annotations

import json
import os
import shutil
import subprocess
from html.parser import HTMLParser
from typing import Protocol
from urllib.parse import quote_plus, urlencode

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
        url = base_url + "/search?" + urlencode({"q": query, "format": "json"})
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


PROVIDERS: dict[str, SearchProvider] = {
    "brave": BraveSearch(),
    "ddg": DuckDuckGoSearch(),
    "github": GitHubRepoSearch(),
    "jina": JinaSearch(),
    "searxng": SearxngSearch(),
}


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
    ]


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
