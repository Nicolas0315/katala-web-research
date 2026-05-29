# Search Capability Model

This document explains how `katala-web-research` improves search and research quality beyond a plain web query.

## Core Idea

The tool improves access to better information by combining six layers:

1. bounded query planning
2. provider diversity
3. local prior-art corpus
4. source-quality ranking
5. page capture into a reusable archive
6. agent-facing retrieval through CLI and MCP
7. trusted source registry for domain-specific source and bias metadata

The result is not just "more search results". The result is a repeatable pipeline that can find, rank, capture, and re-query evidence.

## 1. Bounded Query Planning

`kwr plan` decomposes a broad research question into a small deterministic set of intents:

- baseline query
- official documentation query
- primary-source query for code, papers, and benchmarks
- critique/evaluation query

`kwr brief --expand-queries` and `kwr investigate --expand-queries` use that plan, merge results, dedupe URLs, and rerank the combined candidate pool. The default plan is capped so the workflow does not turn one user question into an unbounded crawl.

## 2. Provider Diversity

The search surface supports multiple backends with different failure modes:

- `ddg`: no-key default web search for a cheap first pass.
- `feed`: local RSS/Atom/JSON Feed archive search for monitored sources.
- `github`: GitHub CLI or GitHub REST repository search for primary code sources.
- `jina`: optional semantic web search through `JINA_API_KEY`.
- `searxng`: optional private metasearch through `KWR_SEARXNG_URL`.
- `brave`: optional Brave Web Search API through `BRAVE_SEARCH_API_KEY`.
- `openalex`: optional scholarly works search through `OPENALEX_API_KEY`.
- `meta`: local metasearch fan-out through `KWR_META_PROVIDERS`.

Provider outputs are normalized into one `SearchResult` shape:

- title
- URL
- snippet
- source
- published date when available
- rank
- score

This lets the rest of the system rank, archive, and report results without caring which provider produced them.

The `meta` provider applies the useful SearXNG pattern without embedding SearXNG itself: each engine remains a small adapter, outputs are normalized, per-engine failures are isolated, Reciprocal Rank Fusion rewards cross-engine consensus, and final ranking is handled by the Katala-style Gate -> Scorer -> Selector layer.

`meta` also records per-engine run health in each JSON result:

- status: `ok`, `empty`, or `error`
- latency in milliseconds
- result count
- bounded health score
- error kind, without raw secrets or session data

That health score weights the fusion layer, so a slow, empty, or failing engine is visible to the operator and contributes less than a healthy engine.

`KWR_META_PROFILE` selects source mix and deterministic query rewriting:

- `broad`: default web, code, scholarly, and SearXNG mix
- `docs`: official/vendor documentation bias
- `scholarly`: OpenAlex-first paper discovery
- `code`: GitHub-first implementation discovery
- `fresh`: current web discovery
- `local`: low-dependency DDG/GitHub path

`KWR_META_PROVIDERS` still overrides the profile when an exact engine list is required.

## 3. Feed Monitoring Sources

`kwr feeds` adds RSS, Atom, and JSON Feed sources as local-first research inputs:

```sh
kwr feeds add https://example.com/feed.xml --archive ~/.kwr/research.sqlite
kwr feeds refresh --archive ~/.kwr/research.sqlite
kwr feeds query "agent research" --archive ~/.kwr/research.sqlite
kwr search "agent research" --provider feed --archive ~/.kwr/research.sqlite
```

The feed layer is intentionally small. It borrows the adapter idea from RSSHub and RSS-Bridge, but it does not vendor their code or require their runtimes. Public RSSHub routes, RSS-Bridge bridges, official product feeds, and ordinary blog feeds all enter Katala as source URLs and are normalized into archived feed items.

Feed search improves recurring research because it can monitor known high-signal sources before broad web search. The source health fields track refresh status, item count, and error kind without storing cookies, sessions, API keys, or browser state.

## 4. Local Prior-Art Corpus

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

## 5. Incremental Corpus Refresh

The scanner stores file metadata:

- file size
- mtime
- SHA-256
- deterministic context metadata: repo name, path, kind, title, and heading path

Repeated scans skip unchanged documents. This makes a large `Documents/GitHub` corpus practical to refresh before research without re-reading everything.

Verified behavior:

```text
first bounded scan: indexed_documents: 13
second bounded scan: indexed_documents: 0, skipped_unchanged: 13
```

## 6. Source-Quality Ranking

Raw result order is not trusted as final quality. `source_quality.py` classifies URLs into quality bands:

- official docs
- primary code
- primary research
- institutional
- vendor docs
- ordinary web

`kwr brief` and `kwr investigate` combine this classification with query overlap, primary-source bonuses, title matches, limited freshness signals, and provider-native boosts. This keeps official docs and primary research from being buried by broad blog results that merely repeat the query terms.

The trusted source registry extends this from host heuristics to domain-specific
source metadata. Registry entries include domain, source type, query types,
freshness, trust score, bias caveat, update cadence, and avoid-for notes. For
example, security queries can route NVD and CISA KEV differently, while news
queries can surface bias-comparison sources without treating them as final
truth.

```sh
kwr sources list --domain security --json
kwr sources list --domain news --query-type media_bias
kwr sources match https://www.cisa.gov/known-exploited-vulnerabilities-catalog --json
```

Matched sources are also surfaced in generated briefs and investigation reports
with registry source name, freshness, update cadence, trust score, and caveat.

Example verified outcome:

```sh
kwr investigate "OpenAI Agents SDK handoffs" --web-limit 3 --read-top 1
```

The official OpenAI Developers orchestration/handoffs page was ranked ahead of ordinary web/blog results and captured into the archive.

## 7. Page Capture And Reuse

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

Investigation reports also include an evidence matrix that shows source class, quality score, capture status, ranking score, and URL for each selected candidate.

## 8. Integrated Investigation

`kwr investigate` is the main workflow command. It performs:

1. optional query planning
2. web search
3. local repo evidence lookup
4. source-quality sorting
5. selected page capture
6. SQLite archive write
7. Markdown investigation report

This is the command to use when the goal is "research this well", not just "search this string".

## 9. Agent Access Through MCP

`kwr mcp` exposes the same functions as MCP tools:

- `kwr.search`
- `kwr.plan`
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
