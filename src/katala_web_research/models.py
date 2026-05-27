from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(slots=True)
class SearchResult:
    title: str
    url: str
    snippet: str = ""
    source: str = ""
    published_at: str | None = None
    rank: int = 0
    score: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class PageSnapshot:
    url: str
    title: str
    content: str
    source: str
    fetched_at: str
    status_code: int | None = None
    content_type: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ArchiveHit:
    url: str
    title: str
    snippet: str
    rank: float
    fetched_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class RepoDocument:
    repo_path: str
    repo_name: str
    rel_path: str
    title: str
    content: str
    kind: str
    indexed_at: str
    context: str = ""
    file_size: int = 0
    file_mtime_ns: int = 0
    content_sha256: str = ""

    @property
    def document_url(self) -> str:
        return f"repo://{self.repo_name}/{self.rel_path}"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self) | {"document_url": self.document_url}


@dataclass(slots=True)
class RepoHit:
    repo_path: str
    repo_name: str
    rel_path: str
    title: str
    snippet: str
    kind: str
    rank: float
    indexed_at: str

    @property
    def document_url(self) -> str:
        return f"repo://{self.repo_name}/{self.rel_path}"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self) | {"document_url": self.document_url}
