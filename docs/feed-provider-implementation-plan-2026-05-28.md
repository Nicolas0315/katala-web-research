# Feed Provider Implementation Plan

- date: 2026-05-28
- goal: add a local-first RSS, Atom, and JSON Feed source layer without vendoring RSSHub, RSS-Bridge, or other AGPL code
- verification gate: `scripts/verify.sh`, `git diff --check`, and `gitleaks dir . --no-banner --redact --exit-code 1`

## Boundary

Ship now:

- Feed source registration in the SQLite archive.
- Stdlib-only RSS, Atom, and JSON Feed parsing.
- Feed item persistence with FTS query support.
- `kwr feeds add`, `kwr feeds refresh`, and `kwr feeds query`.
- `kwr search --provider feed` backed by the local feed archive.
- Deterministic fixture tests with no live network dependency.

Do not do:

- Do not vendor RSSHub, RSS-Bridge, Folo, SearXNG, Firecrawl, or Crawlee code.
- Do not store cookies, sessions, auth headers, API keys, or raw browser state.
- Do not add mandatory JS, PHP, browser, crawler, or vector database dependencies.
- Do not make a long-running crawler or daemon in this pass.

## Design

The first implementation keeps feeds as a local evidence source:

```text
feed source URL -> fetch -> parse -> feed_items table -> FTS -> feed SearchResult
```

RSSHub and RSS-Bridge influence the adapter shape, not the code. A route, bridge, public feed URL, or self-hosted endpoint is just a feed source URL from Katala's perspective.

## Work Breakdown

### Phase 1: Archive Schema

- Add `FeedSource`, `FeedItem`, and `FeedHit` models.
- Add `feed_sources`, `feed_items`, and `feed_items_fts` tables.
- Track source status, last fetch time, result count, health score, and error kind.

### Phase 2: Parser

- Add `feeds.py`.
- Parse RSS channel/item links, titles, descriptions, and dates.
- Parse Atom entry links, titles, summaries, and updated/published dates.
- Parse JSON Feed items and feed metadata.
- Degrade cleanly on missing fields and malformed feeds.

### Phase 3: CLI

- Add `kwr feeds add <url>`.
- Add `kwr feeds refresh [--source <url>]`.
- Add `kwr feeds query <terms>`.
- Keep archive path explicit on feed subcommands.

### Phase 4: Search Provider

- Add `feed` provider.
- Return archived feed items as normalized `SearchResult`.
- Keep `feed` out of broad default metasearch; use it explicitly or via local profile later.

### Phase 5: Tests And Docs

- Add RSS, Atom, JSON Feed, and malformed fixture tests.
- Add archive query and CLI smoke tests.
- Update README and search capability docs with feed commands and boundaries.

## Rollback

- Revert the implementation commit.
- Use a fresh archive path if a local test archive needs to be discarded.
- Existing archives remain readable because new feed tables are additive.
