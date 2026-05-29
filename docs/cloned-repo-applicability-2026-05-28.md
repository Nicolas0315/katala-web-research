# Cloned Repository Applicability Survey - 2026-05-28

This survey checks already-cloned GitHub repositories under `/Users/s30519/work`
for ideas that can improve Katala Web Research search, monitoring, crawling,
and research loops.

## Scope

Local clone roots checked:

- `/Users/s30519/work/vendor`
- `/Users/s30519/work/research/vendor`
- `/Users/s30519/work/nicolas-starred-repos/repos`
- `/Users/s30519/work/repo-applicability-2026-05-14/repos`
- `/Users/s30519/work/repo-applicability-2026-05-15/repos`
- `/Users/s30519/work/repo-applicability-2026-05-20/repos`
- `/Users/s30519/work/mizchi-adoption-2026-05-21/repos`
- `/Users/s30519/work/steipete-stars/repos`
- `/Users/s30519/work/claude-skill-sources/repos`
- `/Users/s30519/work/claude/claude-skill-sources/repos`
- `/Users/s30519/work/codex/codex-skills-topic/repos`

Local findings:

- Git repositories found: 2,909
- Name-filter candidates found: 220
- Bounded dogfood scan: `kwr repos scan` indexed 468 documents from the first
  80 repos in `/Users/s30519/work/nicolas-starred-repos/repos`.
- `kwr repos query "RSS DeepResearch WebThinker MCP feed search"` returned
  relevant hits for `RUC-NLPIR_WebThinker`, `RSS-Bridge_rss-bridge`,
  `FreshRSS_FreshRSS`, `stepfun-ai_StepDeepResearch`, and RSS-Bridge docs.

No `git fetch` was run. Dates below are local clone commit dates, not confirmed
upstream freshness.

## Adoption Rules

- Direct code reuse is acceptable only after license verification.
- AGPL/GPL projects are reference-only unless isolated as an external service,
  URL template, or operator-owned runtime.
- Prefer small Katala-native adapters over vendoring large runtimes.
- Keep authentication, cookies, browser profiles, and social scraping state out
  of the shared archive.
- Favor SQLite archive extensions and CLI/MCP surfaces that can be tested with
  fixtures before adding heavy dependencies.

## Highest-Value Candidates

| Area | Repo | Local evidence | License boundary | Katala applicability |
| --- | --- | --- | --- | --- |
| Feed routes | `DIYgod_RSSHub` | `lib/routes`, local HEAD `2026-05-11` | AGPL | Route catalog reference only. Use public RSSHub URLs as feed sources; do not vendor route code. |
| Feed bridges | `RSS-Bridge_rss-bridge` | `bridges`, `formats`, docs; local HEAD `2026-05-06` | `UNLICENSE` | Good model for per-site bridge metadata, bridge health, and public instance docs. |
| Feed aggregator | `FreshRSS_FreshRSS` | local HEAD `2026-05-11` | AGPL | Reference for OPML import/export, source management, read/unread state; not a code source. |
| Feed product | `RSSNext_Folo` | local HEAD available, package workspace | AGPL | Reference for feed UX and source grouping; not near-term backend code. |
| Metasearch | `searxng_searxng` | `searx/engines`, `searx/search`, local HEAD `2026-05-10` | AGPL | Continue service-adapter boundary. Useful for engine config, result categories, and failure isolation. |
| SearXNG MCP | `mcp-searxng` | package manifest, local HEAD `2026-05-15` | MIT | Small adapter reference for exposing SearXNG through MCP. |
| Crawl frontier | `apify_crawlee` | `packages/basic-crawler`, `packages/http-crawler`, `packages/playwright-crawler`, local HEAD `2026-05-11` | Apache-2.0 | Strongest reference for queue, retry, session, robots, and browser/http crawler split. |
| Web extraction | `firecrawl_firecrawl` | local HEAD `2026-05-11` | AGPL | Service boundary only. Useful conceptually for scrape/map/crawl modes and cache scopes. |
| Web extraction | `D4Vinci_Scrapling` | Python package, local HEAD `2026-05-11` | BSD | Candidate dependency or reference for robust static HTML extraction. |
| Browser lane | `vercel-labs_agent-browser` | package workspace, local HEAD `2026-05-07` | Apache-2.0 | Reference for agent-controlled browser sessions and screenshots, not default crawling. |
| Browser runtime | `lightpanda-io_browser` | Zig browser, local HEAD `2026-05-11` | AGPL | External optional renderer only; do not embed. |
| Crawl library | `openclaw_crawlkit` | Go module, local HEAD `2026-05-11` | MIT | Small clean reference for crawl job modeling and CLI ergonomics. |
| Knowledge base | `VectifyAI_OpenKB` | Python project, local HEAD `2026-05-11` | Apache-2.0 | Reference for local knowledge base compilation and chunk metadata. |
| Agent memory | `topoteretes_cognee` | Python project, local HEAD `2026-05-08` | Apache-2.0 | Reference for graph/memory layer; likely later than core crawl/feed work. |
| Agent memory | `supermemoryai_supermemory` | package workspace, local HEAD `2026-05-11` | MIT | Reference for memory API shape and user-facing memory search. |
| Vector search | `sqlite-vec` | local HEAD `2026-04-08` | no local license file found | Investigate license before use. Potential optional SQLite vector extension. |
| Research loop | `bytedance_deer-flow` | local HEAD `2026-05-11` | MIT | Strong reference for multi-step deep research orchestration and report state. |
| Research loop | `Alibaba-NLP_DeepResearch` | requirements-based Python repo, local HEAD `2026-02-27` | Apache-2.0 | Reference for query expansion/evaluation; likely too model-specific for direct code. |
| Research loop | `jina-ai_node-DeepResearch` | package workspace, local HEAD `2026-05-01` | Apache-2.0 | Useful reference for Node-style research state machine and batch eval hooks. |
| Research loop | `RUC-NLPIR_WebThinker` | README says search, page exploration, report drafting; local HEAD `2025-12-08` | MIT | Concept reference for autonomous search/read/report loops. |
| Research loop | `open_deep_research` | Python project, local HEAD `2026-04-28` | MIT | Reference for budgeted research loops and LangGraph-style state transitions. |
| MCP surface | `modelcontextprotocol_servers` | package workspace, local HEAD `2026-04-17` | Apache-2.0 | Reference for MCP server packaging, tool names, and test layout. |
| MCP surface | `github_github-mcp-server` | Go module, local HEAD `2026-05-11` | MIT | Reference for robust GitHub tool boundaries and pagination patterns. |
| MCP browser | `microsoft_playwright-mcp` | package workspace, local HEAD `2026-05-07` | Apache-2.0 | Reference for browser tool contracts, screenshots, and deterministic testable actions. |

## Recommended Implementation Order

1. Feed source catalog and discovery
   - Add a small curated source preset layer for RSSHub public routes,
     RSS-Bridge public hosts, official product blogs, release feeds, and
     standards feeds.
   - Add OPML import/export before a UI or heavy feed reader behavior.
   - Archive source health fields already fit this path.

2. Crawl frontier in the existing SQLite archive
   - Add `crawl_jobs`, `crawl_attempts`, and `crawl_pages` tables.
   - Keep the default lane HTTP-only.
   - Add explicit job states: `queued`, `fetching`, `captured`, `failed`,
     `skipped`.
   - Borrow Crawlee concepts: request queue, retry budget, robots decision,
     content hash, and per-host rate limits.

3. Optional extractor interface
   - Start with direct HTTP plus current reader fallback.
   - Add a narrow extractor plugin interface before adding browser runtimes.
   - Evaluate Scrapling as the first candidate because it is Python and BSD.
   - Keep Firecrawl and Lightpanda as external service/runtime adapters only.

4. Research budget loop
   - Extend `kwr investigate` with a bounded loop:
     query plan -> search -> read top evidence -> gap analysis -> next query.
   - Stop by max queries, max reads, duplicate-source saturation, and source
     quality coverage.
   - Use DeerFlow, Jina node-DeepResearch, WebThinker, and open_deep_research as
     orchestration references, not as direct imports.

5. Local corpus ranking upgrade
   - Keep FTS5 as the default.
   - Add optional vector search only after license and packaging checks for
     `sqlite-vec` or an alternative.
   - Capture chunk metadata compatible with future graph/memory layers:
     repo, path, heading, source class, captured_at, content_hash.

6. MCP expansion
   - Add MCP tools for `feeds.refresh`, `feeds.query`, `repos.scan`, and
     `investigate`.
   - Follow MCP server repo naming and schema patterns, but keep Katala tool
     names stable and small.

## Do Not Start With

- Vendoring RSSHub, SearXNG, Firecrawl, Lightpanda, FreshRSS, or Folo.
- Running a browser crawl as the default collection path.
- Storing cookies, browser profiles, auth sessions, or third-party account state
  in the archive.
- Adding vector search before the archive schema and ranking contract are stable.
- Running broad recursive scans of all cloned repo contents without a bounded
  max repo/file limit.

## Next Concrete Work Items

P0:

- `kwr feeds import-opml` and `kwr feeds export-opml`.
- `kwr feeds presets list/add` for curated RSSHub/RSS-Bridge/official source
  templates.
- `kwr crawl enqueue/run/status` with SQLite queue tables and fixture-based
  tests.

P1:

- `kwr investigate --research-budget` bounded query/read loop.
- `kwr extract` plugin boundary with one static HTML extractor candidate.
- MCP tool additions for feeds and repo scan.

P2:

- Optional vector index for local repo/page chunks.
- External service adapters for Firecrawl or Lightpanda.
- Graph/memory layer inspired by OpenKB, cognee, and supermemory.

## Verification Commands Run

```sh
rtk python3 - <<'PY'
# Read-only candidate inventory over clone roots.
PY
```

Result: 2,909 git repositories found; 220 name-filter candidates.

```sh
rtk env PYTHONPATH=src python3 -m katala_web_research.cli repos scan \
  /Users/s30519/work/nicolas-starred-repos/repos \
  --archive /tmp/kwr-clone-applicability-2026-05-28.sqlite \
  --max-repos 80 \
  --max-files-per-repo 8 \
  --json
```

Result: 468 documents indexed; warning: `max_repos reached: 80`.

```sh
rtk env PYTHONPATH=src python3 -m katala_web_research.cli repos query \
  "RSS DeepResearch WebThinker MCP feed search" \
  --archive /tmp/kwr-clone-applicability-2026-05-28.sqlite \
  --limit 10 \
  --json
```

Result: relevant hits included WebThinker, RSS-Bridge, FreshRSS,
StepDeepResearch, and RSS-Bridge docs.
