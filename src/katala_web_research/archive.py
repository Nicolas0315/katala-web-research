from __future__ import annotations

import sqlite3
from pathlib import Path

from .models import ArchiveHit, PageSnapshot, RepoDocument, RepoHit, SearchResult, utc_now_iso


DEFAULT_ARCHIVE = Path(".katala-web-research/archive.sqlite")


class Archive:
    def __init__(self, path: str | Path = DEFAULT_ARCHIVE) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def close(self) -> None:
        self.conn.close()

    def _init_schema(self) -> None:
        self.conn.executescript(
            """
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS runs (
              id INTEGER PRIMARY KEY,
              query TEXT NOT NULL,
              provider TEXT NOT NULL,
              created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS search_results (
              id INTEGER PRIMARY KEY,
              run_id INTEGER NOT NULL REFERENCES runs(id),
              rank INTEGER NOT NULL,
              score REAL NOT NULL,
              title TEXT NOT NULL,
              url TEXT NOT NULL,
              snippet TEXT NOT NULL,
              source TEXT NOT NULL,
              published_at TEXT
            );
            CREATE TABLE IF NOT EXISTS pages (
              id INTEGER PRIMARY KEY,
              url TEXT NOT NULL UNIQUE,
              title TEXT NOT NULL,
              content TEXT NOT NULL,
              source TEXT NOT NULL,
              fetched_at TEXT NOT NULL,
              status_code INTEGER,
              content_type TEXT
            );
            CREATE VIRTUAL TABLE IF NOT EXISTS pages_fts
              USING fts5(title, content, url UNINDEXED, content='pages', content_rowid='id');
            CREATE TABLE IF NOT EXISTS repo_documents (
              id INTEGER PRIMARY KEY,
              repo_path TEXT NOT NULL,
              repo_name TEXT NOT NULL,
              rel_path TEXT NOT NULL,
              title TEXT NOT NULL,
              content TEXT NOT NULL,
              kind TEXT NOT NULL,
              indexed_at TEXT NOT NULL,
              file_size INTEGER NOT NULL DEFAULT 0,
              file_mtime_ns INTEGER NOT NULL DEFAULT 0,
              content_sha256 TEXT NOT NULL DEFAULT '',
              UNIQUE(repo_path, rel_path)
            );
            CREATE VIRTUAL TABLE IF NOT EXISTS repo_documents_fts
              USING fts5(repo_name, rel_path, title, content, kind UNINDEXED, content='repo_documents', content_rowid='id');
            CREATE TRIGGER IF NOT EXISTS pages_ai AFTER INSERT ON pages BEGIN
              INSERT INTO pages_fts(rowid, title, content, url)
              VALUES (new.id, new.title, new.content, new.url);
            END;
            CREATE TRIGGER IF NOT EXISTS pages_ad AFTER DELETE ON pages BEGIN
              INSERT INTO pages_fts(pages_fts, rowid, title, content, url)
              VALUES('delete', old.id, old.title, old.content, old.url);
            END;
            CREATE TRIGGER IF NOT EXISTS pages_au AFTER UPDATE ON pages BEGIN
              INSERT INTO pages_fts(pages_fts, rowid, title, content, url)
              VALUES('delete', old.id, old.title, old.content, old.url);
              INSERT INTO pages_fts(rowid, title, content, url)
              VALUES (new.id, new.title, new.content, new.url);
            END;
            CREATE TRIGGER IF NOT EXISTS repo_documents_ai AFTER INSERT ON repo_documents BEGIN
              INSERT INTO repo_documents_fts(rowid, repo_name, rel_path, title, content, kind)
              VALUES (new.id, new.repo_name, new.rel_path, new.title, new.content, new.kind);
            END;
            CREATE TRIGGER IF NOT EXISTS repo_documents_ad AFTER DELETE ON repo_documents BEGIN
              INSERT INTO repo_documents_fts(repo_documents_fts, rowid, repo_name, rel_path, title, content, kind)
              VALUES('delete', old.id, old.repo_name, old.rel_path, old.title, old.content, old.kind);
            END;
            CREATE TRIGGER IF NOT EXISTS repo_documents_au AFTER UPDATE ON repo_documents BEGIN
              INSERT INTO repo_documents_fts(repo_documents_fts, rowid, repo_name, rel_path, title, content, kind)
              VALUES('delete', old.id, old.repo_name, old.rel_path, old.title, old.content, old.kind);
              INSERT INTO repo_documents_fts(rowid, repo_name, rel_path, title, content, kind)
              VALUES (new.id, new.repo_name, new.rel_path, new.title, new.content, new.kind);
            END;
            """
        )
        self._ensure_repo_document_columns()
        self.conn.commit()

    def _ensure_repo_document_columns(self) -> None:
        existing = {
            row["name"]
            for row in self.conn.execute("PRAGMA table_info(repo_documents)").fetchall()
        }
        migrations = {
            "file_size": "ALTER TABLE repo_documents ADD COLUMN file_size INTEGER NOT NULL DEFAULT 0",
            "file_mtime_ns": "ALTER TABLE repo_documents ADD COLUMN file_mtime_ns INTEGER NOT NULL DEFAULT 0",
            "content_sha256": "ALTER TABLE repo_documents ADD COLUMN content_sha256 TEXT NOT NULL DEFAULT ''",
        }
        for column, statement in migrations.items():
            if column not in existing:
                self.conn.execute(statement)

    def store_run(self, query: str, provider: str, results: list[SearchResult]) -> int:
        cur = self.conn.execute(
            "INSERT INTO runs(query, provider, created_at) VALUES (?, ?, ?)",
            (query, provider, utc_now_iso()),
        )
        run_id = int(cur.lastrowid)
        self.conn.executemany(
            """
            INSERT INTO search_results(
              run_id, rank, score, title, url, snippet, source, published_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    result.rank,
                    result.score,
                    result.title,
                    result.url,
                    result.snippet,
                    result.source,
                    result.published_at,
                )
                for result in results
            ],
        )
        self.conn.commit()
        return run_id

    def upsert_page(self, page: PageSnapshot) -> None:
        self.conn.execute(
            """
            INSERT INTO pages(url, title, content, source, fetched_at, status_code, content_type)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(url) DO UPDATE SET
              title=excluded.title,
              content=excluded.content,
              source=excluded.source,
              fetched_at=excluded.fetched_at,
              status_code=excluded.status_code,
              content_type=excluded.content_type
            """,
            (
                page.url,
                page.title,
                page.content,
                page.source,
                page.fetched_at,
                page.status_code,
                page.content_type,
            ),
        )
        self.conn.commit()

    def upsert_repo_document(self, document: RepoDocument) -> None:
        self.conn.execute(
            """
            INSERT INTO repo_documents(
              repo_path, repo_name, rel_path, title, content, kind, indexed_at,
              file_size, file_mtime_ns, content_sha256
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(repo_path, rel_path) DO UPDATE SET
              repo_name=excluded.repo_name,
              title=excluded.title,
              content=excluded.content,
              kind=excluded.kind,
              indexed_at=excluded.indexed_at,
              file_size=excluded.file_size,
              file_mtime_ns=excluded.file_mtime_ns,
              content_sha256=excluded.content_sha256
            """,
            (
                document.repo_path,
                document.repo_name,
                document.rel_path,
                document.title,
                document.content,
                document.kind,
                document.indexed_at,
                document.file_size,
                document.file_mtime_ns,
                document.content_sha256,
            ),
        )
        self.conn.commit()

    def upsert_repo_documents(self, documents: list[RepoDocument]) -> int:
        for document in documents:
            self.upsert_repo_document(document)
        return len(documents)

    def repo_document_metadata(self) -> dict[tuple[str, str], tuple[int, int, str]]:
        rows = self.conn.execute(
            "SELECT repo_path, rel_path, file_size, file_mtime_ns, content_sha256 FROM repo_documents"
        ).fetchall()
        return {
            (row["repo_path"], row["rel_path"]): (
                int(row["file_size"]),
                int(row["file_mtime_ns"]),
                str(row["content_sha256"]),
            )
            for row in rows
        }

    def query(self, terms: str, *, limit: int = 10) -> list[ArchiveHit]:
        rows = self.conn.execute(
            """
            SELECT p.url, p.title,
                   snippet(pages_fts, 1, '[', ']', '...', 18) AS snippet,
                   bm25(pages_fts) AS rank,
                   p.fetched_at
            FROM pages_fts
            JOIN pages p ON p.id = pages_fts.rowid
            WHERE pages_fts MATCH ?
            ORDER BY rank
            LIMIT ?
            """,
            (_fts_query(terms), limit),
        ).fetchall()
        return [
            ArchiveHit(
                url=row["url"],
                title=row["title"],
                snippet=row["snippet"],
                rank=float(row["rank"]),
                fetched_at=row["fetched_at"],
            )
            for row in rows
        ]

    def query_repos(self, terms: str, *, limit: int = 10) -> list[RepoHit]:
        rows = self.conn.execute(
            """
            SELECT d.repo_path, d.repo_name, d.rel_path, d.title,
                   snippet(repo_documents_fts, 3, '[', ']', '...', 18) AS snippet,
                   d.kind,
                   bm25(repo_documents_fts) AS rank,
                   d.indexed_at
            FROM repo_documents_fts
            JOIN repo_documents d ON d.id = repo_documents_fts.rowid
            WHERE repo_documents_fts MATCH ?
            ORDER BY rank
            LIMIT ?
            """,
            (_fts_query(terms), limit),
        ).fetchall()
        return [
            RepoHit(
                repo_path=row["repo_path"],
                repo_name=row["repo_name"],
                rel_path=row["rel_path"],
                title=row["title"],
                snippet=row["snippet"],
                kind=row["kind"],
                rank=float(row["rank"]),
                indexed_at=row["indexed_at"],
            )
            for row in rows
        ]


def _fts_query(terms: str) -> str:
    tokens = [token.replace('"', "") for token in terms.split() if token.strip()]
    if not tokens:
        return '""'
    return " OR ".join(f'"{token}"' for token in tokens)
