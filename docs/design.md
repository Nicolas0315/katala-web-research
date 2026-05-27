# Design

## Goal

Strengthen research and investigation workflows by improving access to high-signal web information while keeping the system local-first, auditable, and easy to manage in GitHub.

## Requirements From The Request

- Use applicable local repositories as prior art.
- Include real web search and URL reading.
- Improve access to optimal information, not just raw search hits.
- Produce a GitHub-manageable development artifact.
- Keep the implementation verifiable.

## Architecture

```text
query
  -> provider search
  -> ranking and dedupe
  -> URL reader
  -> SQLite archive with FTS5
  -> Markdown evidence report

local Git root
  -> repository scanner
  -> README / AGENTS / Skill / manifest / docs extraction
  -> SQLite archive with FTS5
  -> local repo query

brief query
  -> web search candidates
  -> local repository evidence
  -> source quality classification
  -> Markdown research brief

agent client
  -> MCP stdio
  -> kwr.search / kwr.read / kwr.query / kwr.repos_query / kwr.brief / kwr.investigate

investigate query
  -> web candidates sorted by source quality
  -> local repository evidence
  -> selected page captures
  -> SQLite archive
  -> Markdown investigation report
```

## Provider Contract

Each search provider returns:

- `title`
- `url`
- `snippet`
- `source`
- `published_at`
- `rank`
- `score`

The provider does not write archives and does not own ranking policy. This mirrors the small-channel shape used by Agent-Reach while keeping the research archive independent.

## Reader Contract

Readers return:

- canonical URL
- title
- content
- reader source
- fetched timestamp
- status and content type when available

The default reader tries Jina Reader first, then direct HTTP. This gives a clean-text path for ordinary pages and a dependency-free fallback for local verification.

## Archive Contract

The archive is a user-selected SQLite file. It stores:

- search runs
- search results
- captured pages
- repository documents
- FTS5 index over page title and content
- FTS5 index over repository name, path, title, and content
- file size, mtime, and SHA-256 metadata for incremental scans

No tokens, cookies, browser profile paths, or raw session logs are stored.

## Repository Corpus Contract

The local corpus scanner finds Git repositories under a root and indexes small, reviewable source documents:

- `README*`
- `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`
- `SKILL.md`
- `pyproject.toml`, `package.json`, `go.mod`, `Cargo.toml`
- small `.md`, `.txt`, `.rst`, `.toml`, `.json`, `.yaml`, `.yml` docs

It skips `.git`, dependency folders, caches, build outputs, raw downloads, logs, and sessions. This makes `/Users/s30519/Documents/GitHub` useful as a research prior-art corpus without copying entire repos or private runtime artifacts into Git.

Subsequent scans skip unchanged files by comparing stored size, mtime, and SHA-256 metadata. This keeps a large `Documents/GitHub` corpus practical for repeated research refreshes.

## Current Limits

- No browser automation in MVP.
- No authenticated social scraping in MVP.
- `/Users/s30519/Documents/GitHub` is readable in the current session, but full scans can be large. Use bounded `--max-repos` and `--max-files-per-repo` first.
- Search result freshness is only provider metadata plus ranking, not a full temporal verifier.
- Source quality scoring is heuristic; final claims still need source review.

## Next Development Slices

1. Add a provider plugin interface for Firecrawl, Tavily, and other paid/custom backends.
2. Add stronger citation-quality scoring that accounts for retrieval date and source type.
3. Add a small hosted dashboard only if CLI/MCP usage proves insufficient.
