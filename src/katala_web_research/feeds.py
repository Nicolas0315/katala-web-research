from __future__ import annotations

import json
from dataclasses import dataclass
from email.utils import parsedate_to_datetime
from urllib.parse import urljoin
from xml.etree import ElementTree

from .http import fetch_url
from .models import FeedItem, FeedSource, utc_now_iso
from .text import SimpleHTMLTextExtractor, collapse_space, normalize_url


@dataclass(slots=True)
class FeedParseResult:
    source: FeedSource
    items: list[FeedItem]


def fetch_and_parse_feed(url: str) -> FeedParseResult:
    fetched_at = utc_now_iso()
    response = fetch_url(
        url,
        headers={
            "Accept": "application/rss+xml, application/atom+xml, application/feed+json, application/json, text/xml, */*"
        },
    )
    return parse_feed_text(response.text, source_url=url, fetched_at=fetched_at)


def parse_feed_text(text: str, *, source_url: str, fetched_at: str | None = None) -> FeedParseResult:
    fetched_at = fetched_at or utc_now_iso()
    stripped = text.lstrip("\ufeff").lstrip()
    if stripped.startswith("{"):
        return _parse_json_feed(stripped, source_url=source_url, fetched_at=fetched_at)
    try:
        root = ElementTree.fromstring(stripped)
    except ElementTree.ParseError as exc:
        raise ValueError(f"invalid feed XML: {exc}") from exc
    root_name = _local_name(root.tag).lower()
    if root_name == "feed":
        return _parse_atom(root, source_url=source_url, fetched_at=fetched_at)
    if root_name not in {"rss", "rdf"} and _first_child(root, "channel") is None and not _children(root, "item"):
        raise ValueError(f"unsupported feed XML root: {_local_name(root.tag)}")
    return _parse_rss(root, source_url=source_url, fetched_at=fetched_at)


def _parse_json_feed(text: str, *, source_url: str, fetched_at: str) -> FeedParseResult:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON feed: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("invalid JSON feed: root must be an object")
    source_title = collapse_space(str(payload.get("title") or source_url))
    source = FeedSource(
        url=source_url,
        title=source_title,
        kind="json",
        last_fetched_at=fetched_at,
        status="ok",
        health_score=1.0,
    )
    items = []
    for item in payload.get("items") or []:
        if not isinstance(item, dict):
            continue
        item_url = _item_url(source_url, str(item.get("url") or item.get("external_url") or ""))
        if not item_url:
            continue
        title = collapse_space(str(item.get("title") or item_url))
        summary = _clean_text(
            str(
                item.get("summary")
                or item.get("content_text")
                or item.get("content_html")
                or ""
            )
        )
        items.append(
            FeedItem(
                source_url=source_url,
                url=item_url,
                title=title,
                summary=summary,
                source_title=source_title,
                published_at=_normalize_date(item.get("date_published") or item.get("date_modified")),
                fetched_at=fetched_at,
            )
        )
    source.last_item_count = len(items)
    return FeedParseResult(source=source, items=items)


def _parse_rss(root: ElementTree.Element, *, source_url: str, fetched_at: str) -> FeedParseResult:
    channel = _first_child(root, "channel")
    if channel is None:
        channel = root
    source_title = _child_text(channel, "title") or source_url
    source = FeedSource(
        url=source_url,
        title=source_title,
        kind="rss",
        last_fetched_at=fetched_at,
        status="ok",
        health_score=1.0,
    )
    items = []
    for item in _children(root, "item") + ([] if channel is root else _children(channel, "item")):
        item_url = _item_url(
            source_url,
            _child_text(item, "link") or _rss_guid_url(source_url, item),
        )
        if not item_url:
            continue
        title = _child_text(item, "title") or item_url
        summary = _clean_text(
            _child_text(item, "description")
            or _child_text(item, "encoded")
            or _child_text(item, "summary")
        )
        items.append(
            FeedItem(
                source_url=source_url,
                url=item_url,
                title=title,
                summary=summary,
                source_title=source_title,
                published_at=_normalize_date(_child_text(item, "pubDate") or _child_text(item, "date")),
                fetched_at=fetched_at,
            )
        )
    source.last_item_count = len(items)
    return FeedParseResult(source=source, items=items)


def _parse_atom(root: ElementTree.Element, *, source_url: str, fetched_at: str) -> FeedParseResult:
    source_title = _child_text(root, "title") or source_url
    source = FeedSource(
        url=source_url,
        title=source_title,
        kind="atom",
        last_fetched_at=fetched_at,
        status="ok",
        health_score=1.0,
    )
    items = []
    for entry in _children(root, "entry"):
        item_url = _item_url(source_url, _atom_link(entry) or _url_like_child_text(entry, "id"))
        if not item_url:
            continue
        title = _child_text(entry, "title") or item_url
        summary = _clean_text(
            _child_text(entry, "summary")
            or _child_text(entry, "content")
        )
        items.append(
            FeedItem(
                source_url=source_url,
                url=item_url,
                title=title,
                summary=summary,
                source_title=source_title,
                published_at=_normalize_date(_child_text(entry, "published") or _child_text(entry, "updated")),
                fetched_at=fetched_at,
            )
        )
    source.last_item_count = len(items)
    return FeedParseResult(source=source, items=items)


def _atom_link(entry: ElementTree.Element) -> str:
    fallback = ""
    for child in entry:
        if _local_name(child.tag) != "link":
            continue
        href = child.attrib.get("href", "")
        if not href:
            continue
        rel = child.attrib.get("rel", "alternate")
        if rel == "alternate":
            return href
        fallback = fallback or href
    return fallback


def _rss_guid_url(source_url: str, item: ElementTree.Element) -> str:
    guid = _first_child(item, "guid")
    if guid is None:
        return ""
    is_permalink = guid.attrib.get("isPermaLink", "true").strip().lower()
    value = collapse_space("".join(guid.itertext()))
    if is_permalink == "false" or not _looks_like_url(value):
        return ""
    return _item_url(source_url, value)


def _url_like_child_text(element: ElementTree.Element, name: str) -> str:
    value = _child_text(element, name)
    return value if _looks_like_url(value) else ""


def _item_url(source_url: str, value: str) -> str:
    value = collapse_space(value)
    if not value:
        return ""
    if "://" not in value and not value.startswith("//"):
        value = urljoin(source_url, value)
    return normalize_url(value)


def _looks_like_url(value: str) -> bool:
    return "://" in value or value.startswith(("/", "//"))


def _normalize_date(value: object) -> str | None:
    if not value:
        return None
    text = collapse_space(str(value))
    if not text:
        return None
    try:
        parsed = parsedate_to_datetime(text)
    except (TypeError, ValueError):
        return text
    return parsed.isoformat()


def _child_text(element: ElementTree.Element, name: str) -> str:
    child = _first_child(element, name)
    if child is None:
        return ""
    return collapse_space("".join(child.itertext()))


def _first_child(element: ElementTree.Element, name: str) -> ElementTree.Element | None:
    for child in element:
        if _local_name(child.tag) == name:
            return child
    return None


def _children(element: ElementTree.Element, name: str) -> list[ElementTree.Element]:
    return [child for child in element if _local_name(child.tag) == name]


def _local_name(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", 1)[1]
    return tag.split(":", 1)[-1]


def _clean_text(value: str) -> str:
    if "<" not in value or ">" not in value:
        return collapse_space(value)
    parser = SimpleHTMLTextExtractor()
    parser.feed(value)
    parser.close()
    return collapse_space(parser.content)
