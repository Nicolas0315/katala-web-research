# Local FTS Search Notes

date: 2026-06-15
scope: Katala local repo corpus search

Observed local engine shape:
- `repo_documents_fts` uses SQLite FTS5 over `repo_name`, `rel_path`, `title`, `context`, and `content`.
- Corpus scanning already builds deterministic context from repo name, relative path, file kind, title, and markdown headings.
- `query_repos` ranks with SQLite FTS5 `bm25(...)` and returns lower BM25 values first.

Katala adaptation chosen now:
- Weight repo metadata fields above body content in repo FTS ranking:
  - `repo_name`: 2.0
  - `rel_path`: 1.6
  - `title`: 2.4
  - `context`: 1.8
  - `content`: 1.0
- This mirrors common search-engine field boosting while staying inside the existing SQLite FTS boundary.
- Add query-time repo corpus filters:
  - `kwr repos query ... --repo NAME`
  - `kwr repos query ... --path TEXT`
  - inline operators: `repo:NAME path:TEXT search terms`

Verification:
- `tests.test_archive.ArchiveTests.test_repo_query_weights_title_above_body` fixes the expected title-over-body behavior.
- `tests.test_archive.ArchiveTests.test_repo_query_can_filter_by_repo_and_path` fixes scoped repo/path retrieval.
- `tests.test_archive.ArchiveTests.test_repo_query_accepts_inline_repo_and_path_filters` fixes inline operator parsing.
- `tests.test_cli_repos.CliReposTests.test_repos_query_accepts_repo_and_path_filters` covers CLI wiring.
- `tests.test_cli_repos.CliReposTests.test_repos_query_accepts_inline_repo_and_path_filters` covers inline CLI use.

Next candidates:
- Add a small benchmark fixture for repo search relevance before tuning weights further.
- Consider quoted inline filters only if operators need spaces in repo or path filters.
