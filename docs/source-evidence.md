# Source Evidence

- retrieved_at: 2026-05-27
- local root: `/Users/s30519/work/katala-web-research`

## Local Repos

- `/Users/s30519/work/Agent-Reach`: channel-style provider split, Jina Reader URL reading, Exa/mcporter optional search posture.
- `/Users/s30519/work/x-tweet-fetcher`: no-key web search fallback strategy and direct HTTP/browser separation.
- `/Users/s30519/work/supacrawl`: local SQLite archive and FTS-oriented inspection flow.
- `/Users/s30519/work/agent-research`: source evidence, raw artifact guard, and verification pattern.

`/Users/s30519/Documents/GitHub` was requested as an input corpus. It was readable on the continuation pass on 2026-05-27. A bounded scan verified the adapter against 3 repos and 14 indexed documents:

- `/Users/s30519/Documents/GitHub/firefox`
- `/Users/s30519/Documents/GitHub/issuebot`
- `/Users/s30519/Documents/GitHub/prompts.chat`

Verification commands:

```sh
PYTHONPATH=src python3 -m katala_web_research.cli repos scan /Users/s30519/Documents/GitHub --archive /tmp/kwr-documents-github-head.sqlite --max-repos 3 --max-files-per-repo 5 --json
PYTHONPATH=src python3 -m katala_web_research.cli repos query prompt --archive /tmp/kwr-documents-github-head.sqlite --limit 5
PYTHONPATH=src python3 -m katala_web_research.cli brief prompt --archive /tmp/kwr-documents-github-head.sqlite --no-web --repo-limit 3 --out /tmp/kwr-documents-github-brief.md
```

## External Primary Sources

- Jina Reader: `https://jina.ai/en-US/reader/`
  - Decision: use `https://r.jina.ai/<url>` as the clean-reader first pass and fall back to direct HTTP when unavailable.
- Exa docs: `https://docs.exa.ai/`
  - Decision: keep Exa/Jina semantic search as optional API-key provider; no key is stored.
- Firecrawl docs: `https://docs.firecrawl.dev/`
  - Decision: do not make Firecrawl a default dependency; leave it as a future provider because it is API-service oriented.
- GitHub REST Search API: `https://docs.github.com/en/rest/search/search`
  - Decision: support GitHub repo search through `gh` first, REST fallback second, and optional `GITHUB_TOKEN`.
- Model Context Protocol specification: `https://modelcontextprotocol.info/specification/2025-11-25`
  - Decision: expose the toolkit through stdio JSON-RPC with `initialize`, `tools/list`, and `tools/call`, keeping tools read-oriented and user-controlled.
- SearXNG Search API docs: `https://docs.searxng.org/dev/search_api.html`
  - Decision: support optional `KWR_SEARXNG_URL` provider using `format=json`.
- Brave Search API docs: `https://api-dashboard.search.brave.com/app/documentation/web-search/get-started`
  - Decision: support optional `BRAVE_SEARCH_API_KEY` provider for the official Web Search API endpoint.

## Design Consequence

The MVP keeps the core loop small:

1. search provider returns ranked URLs
2. reader captures pages as text
3. archive stores runs and pages in SQLite FTS5
4. repository scanner indexes local GitHub corpus docs into SQLite FTS5
5. MCP stdio server exposes the same search/read/query/brief capabilities to coding agents
6. brief/report emits reviewable Markdown with URLs, local evidence, and fetch metadata

This avoids a heavy crawler, avoids browser/session secrets, and leaves provider replacement straightforward.
