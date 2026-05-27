from __future__ import annotations

from urllib.parse import urlparse

from .http import FetchError, fetch_url
from .models import PageSnapshot, utc_now_iso
from .text import SimpleHTMLTextExtractor


def read_url(url: str, *, reader: str = "auto") -> PageSnapshot:
    _require_http_url(url)
    if reader not in {"auto", "jina", "direct"}:
        raise ValueError("reader must be one of: auto, jina, direct")
    if reader in {"auto", "jina"}:
        try:
            return read_with_jina(url)
        except FetchError:
            if reader == "jina":
                raise
    return read_direct(url)


def read_with_jina(url: str) -> PageSnapshot:
    jina_url = "https://r.jina.ai/" + url
    response = fetch_url(jina_url, headers={"Accept": "text/plain"})
    content = response.text.strip()
    title = _title_from_markdown(content) or url
    return PageSnapshot(
        url=url,
        title=title,
        content=content,
        source="jina-reader",
        fetched_at=utc_now_iso(),
        status_code=response.status,
        content_type=response.headers.get("content-type"),
    )


def read_direct(url: str) -> PageSnapshot:
    response = fetch_url(url, headers={"Accept": "text/html, text/plain;q=0.9, */*;q=0.5"})
    content_type = response.headers.get("content-type", "")
    text = response.text
    if "html" in content_type.lower() or "<html" in text[:500].lower():
        parser = SimpleHTMLTextExtractor()
        parser.feed(text)
        title = parser.title or url
        content = parser.content
    else:
        title = url
        content = text.strip()
    return PageSnapshot(
        url=response.url,
        title=title,
        content=content,
        source="direct",
        fetched_at=utc_now_iso(),
        status_code=response.status,
        content_type=content_type,
    )


def _require_http_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("only http and https URLs are supported")


def _title_from_markdown(content: str) -> str:
    for line in content.splitlines():
        stripped = line.strip("# ").strip()
        if stripped:
            return stripped[:160]
    return ""

