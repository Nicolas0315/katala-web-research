from __future__ import annotations

import re
from html import unescape
from html.parser import HTMLParser
from urllib.parse import parse_qs, unquote, urlparse


SPACE_RE = re.compile(r"\s+")


def collapse_space(value: str) -> str:
    return SPACE_RE.sub(" ", unescape(value or "")).strip()


def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.netloc.endswith("duckduckgo.com") and parsed.path.startswith("/l/"):
        target = parse_qs(parsed.query).get("uddg", [""])[0]
        if target:
            return unquote(target)
    if url.startswith("//"):
        return "https:" + url
    return url


class SimpleHTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_parts: list[str] = []
        self.body_parts: list[str] = []
        self._skip_depth = 0
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag_lower = tag.lower()
        if tag_lower in {"script", "style", "noscript", "svg"}:
            self._skip_depth += 1
        if tag_lower == "title":
            self._in_title = True
        if tag_lower in {"p", "br", "li", "section", "article", "div", "h1", "h2", "h3"}:
            self.body_parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        tag_lower = tag.lower()
        if tag_lower in {"script", "style", "noscript", "svg"} and self._skip_depth:
            self._skip_depth -= 1
        if tag_lower == "title":
            self._in_title = False
        if tag_lower in {"p", "li", "section", "article", "div"}:
            self.body_parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        if self._in_title:
            self.title_parts.append(data)
            return
        text = collapse_space(data)
        if text:
            self.body_parts.append(text)
            self.body_parts.append(" ")

    @property
    def title(self) -> str:
        return collapse_space(" ".join(self.title_parts))

    @property
    def content(self) -> str:
        lines = [collapse_space(line) for line in "".join(self.body_parts).splitlines()]
        return "\n".join(line for line in lines if line)

