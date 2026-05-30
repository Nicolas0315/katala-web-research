# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- ruff + mypy linting config in `pyproject.toml` (advisory mypy, blocking ruff).
- CI Python matrix expanded to 3.11 and 3.12.
- Fixture-based DDG HTML parser regression test (`tests/fixtures/sample.duckduckgo.html`).
- `.env` secret-pattern guard in `scripts/verify.sh` (rejects `sk-`, `ghp_`, `AKIA`, private key headers).
- PyPI classifiers and `[project.optional-dependencies]` groups in `pyproject.toml`.
- `CHANGELOG.md` (this file).

### Fixed
- Removed unused `quote_plus` import from `providers.py` (ruff F401).

## [0.1.0] - 2026-05-27

### Added
- Local-first research toolkit: `kwr search`, `kwr read`, `kwr collect`, `kwr brief`,
  `kwr investigate`, `kwr query`, `kwr archive`, `kwr plan`, `kwr eval`, `kwr sources`,
  `kwr feeds`, `kwr doctor` commands.
- SQLite FTS5 archive for search results and page snapshots.
- Multi-provider search: DuckDuckGo HTML, SearXNG, Brave Search API, OpenAlex,
  GitHub Code Search, Jina AI reader, local feed archive.
- Metasearch engine layer with Reciprocal Rank Fusion and per-provider health scoring.
- Query-profile rewriting (`scholarly`, `broad`, `code`, `docs`, `fresh`).
- Research quality evaluation harness (`kwr eval`, `scripts/benchmark-research-quality.py`).
- Token-budget benchmark (`scripts/benchmark-token-budget.py`).
- Source quality registry with 60+ trusted domains across 12 categories.
- RSS/Atom/JSON Feed ingestion pipeline (`kwr feeds add`, `kwr feeds refresh`).
- Feed evidence integration in research briefs and investigation reports.
- MCP server interface for agent integration.
- `scripts/verify.sh` end-to-end verification script covering compile, unit tests,
  CLI smoke tests, and tracked-artifact guard.
- GitHub Actions CI workflow.
- Contribution guide, PR template, and issue templates.

[Unreleased]: https://github.com/katala-os/katala-web-research/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/katala-os/katala-web-research/releases/tag/v0.1.0
