# Search Capability Model

This document explains how `katala-web-research` improves search and research quality beyond a plain web query.

## Core Idea

The tool improves access to better information by combining five layers:

1. provider diversity
2. local prior-art corpus
3. source-quality ranking
4. page capture into a reusable archive
5. agent-facing retrieval through CLI and MCP

The result is not just "more search results". The result is a repeatable pipeline that can find, rank, capture, and re-query evidence.

## 1. Provider Diversity

The search surface supports multiple backends with different failure modes:

- `ddg`: no-key default web search for a cheap first pass.
- `github`: GitHub CLI or GitHub REST repository search for primary code sources.
- `jina`: optional semantic web search through `JINA_API_KEY`.
- `searxng`: optional private metasearch through `KWR_SEARXNG_URL`.
- `brave`: optional Brave Web Search API through `BRAVE_SEARCH_API_KEY`.

Provider outputs are normalized into one `SearchResult` shape:

- title
- URL
- snippet
- source
- published date when available
- rank
- score

This lets the rest of the system rank, archive, and report results without caring which provider produced them.

## 2. Local Prior-Art Corpus

`kwr repos scan` turns local Git repositories into a searchable prior-art corpus. The intended high-value root is:

```sh
~/Documents/GitHub
```

The scanner indexes small, reviewable files:

- `README*`
- `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`
- `SKILL.md`
- `pyproject.toml`, `package.json`, `go.mod`, `Cargo.toml`
- small docs and config files

It skips runtime-heavy or sensitive paths:

- `.git`
- dependency folders
- build outputs
- raw downloads
- logs
- sessions
- caches

This improves search because the system can compare new web candidates against local repo knowledge, prior tools, implementation patterns, and agent instructions that are already on the machine.

## 3. Incremental Corpus Refresh

The scanner stores file metadata:

- file size
- mtime
- SHA-256

Repeated scans skip unchanged documents. This makes a large `Documents/GitHub` corpus practical to refresh before research without re-reading everything.

Verified behavior:

```text
first bounded scan: indexed_documents: 13
second bounded scan: indexed_documents: 0, skipped_unchanged: 13
```

## 4. Source-Quality Ranking

Raw result order is not trusted as final quality. `source_quality.py` classifies URLs into quality bands:

- official docs
- primary code
- primary research
- institutional
- vendor docs
- ordinary web

`kwr brief` and `kwr investigate` use this classification so that official and primary sources are surfaced before generic articles when scores are otherwise close.

Example verified outcome:

```sh
kwr investigate "OpenAI Agents SDK handoffs" --web-limit 3 --read-top 1
```

The official OpenAI Developers orchestration/handoffs page was ranked ahead of ordinary web/blog results and captured into the archive.

## 5. Page Capture And Reuse

Search results are volatile. `kwr collect` and `kwr investigate` capture selected pages into SQLite:

- clean text through Jina Reader when available
- direct HTTP fallback
- page title
- reader source
- fetched timestamp
- status/content metadata when available

Captured pages are indexed with SQLite FTS5, so later research can use:

```sh
kwr query "handoffs" --archive ~/.kwr/research.sqlite
```

This turns transient search results into reusable local evidence.

## 6. Integrated Investigation

`kwr investigate` is the main workflow command. It performs:

1. web search
2. local repo evidence lookup
3. source-quality sorting
4. selected page capture
5. SQLite archive write
6. Markdown investigation report

This is the command to use when the goal is "research this well", not just "search this string".

## 7. Agent Access Through MCP

`kwr mcp` exposes the same functions as MCP tools:

- `kwr.search`
- `kwr.read`
- `kwr.query`
- `kwr.repos_query`
- `kwr.brief`
- `kwr.investigate`

This improves practical search ability because Codex, Claude Code, Gemini CLI, or another MCP client can ask the same local archive and provider layer instead of relying only on each agent's built-in web behavior.

## Quality Boundaries

The system improves retrieval and evidence handling, but final claims still need source review:

- source-quality scoring is heuristic
- provider freshness metadata may be incomplete
- captured content may omit dynamic browser-only sections
- authenticated/social scraping is intentionally out of scope

The safe pattern is: search broadly, rank sources, capture selected pages, compare against local corpus, then verify claims before publication.
