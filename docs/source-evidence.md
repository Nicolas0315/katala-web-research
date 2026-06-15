# Source Evidence

- retrieved_at: 2026-05-27
- local root: `katala-web-research`

## Local Repos

- `Agent-Reach`: channel-style provider split, Jina Reader URL reading, Exa/mcporter optional search posture.
- `x-tweet-fetcher`: no-key web search fallback strategy and direct HTTP/browser separation.
- `supacrawl`: local SQLite archive and FTS-oriented inspection flow.
- `agent-research`: source evidence, raw artifact guard, and verification pattern.

The local GitHub checkout folder was requested as an input corpus. It was readable on the continuation pass on 2026-05-27. A bounded scan verified the adapter against 3 repos and 14 indexed documents:

- `firefox`
- `issuebot`
- `prompts.chat`

Verification commands:

```sh
PYTHONPATH=src python3 -m katala_web_research.cli repos scan ~/Documents/GitHub --archive /tmp/kwr-documents-github-head.sqlite --max-repos 3 --max-files-per-repo 5 --json
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
- GitHub REST Search API code search: `https://docs.github.com/en/rest/search/search?apiVersion=2022-11-28#search-code`
  - Retrieved: 2026-06-15
  - Local version/config: provider sends `X-GitHub-Api-Version: 2022-11-28` and `Accept: application/vnd.github.text-match+json`.
  - Decision: add `github_code` as an explicit token-gated provider rather than merging code snippets into repository discovery results. Page through code search with the official `page` query parameter, and treat invalid syntax HTTP 422 responses as empty results.
  - Verification command: `PYTHONPATH=src python -m unittest tests.test_providers`.
  - Risk: code search auth/rate limits can make this provider unavailable; `provider_status` reports it `off` without `GITHUB_TOKEN`.
  - Rollback: remove `github_code` from `PROVIDERS` and from the `code` metasearch profile.
  - Next refresh: 2026-07-15
- Model Context Protocol specification: `https://modelcontextprotocol.info/specification/2025-11-25`
  - Decision: expose the toolkit through stdio JSON-RPC with `initialize`, `tools/list`, and `tools/call`, keeping tools read-oriented and user-controlled.
- SearXNG Search API docs: `https://docs.searxng.org/dev/search_api.html`
  - Decision: support optional `KWR_SEARXNG_URL` provider using `format=json`.
- SearXNG source repository: `https://github.com/searxng/searxng`
  - Retrieved: 2026-05-27
  - Decision: do not vendor or fork SearXNG because its source is AGPL-3.0; reuse the metasearch architecture boundary in MIT-compatible local code.
- SearXNG engine and settings docs: `https://docs.searxng.org/dev/engines/index.html`, `https://docs.searxng.org/admin/settings/settings.html`
  - Retrieved: 2026-05-27
  - Decision: model each backend as a small adapter and keep engine selection in environment/config.
- OpenAlex API authentication docs: `https://developers.openalex.org/api-reference/authentication`
  - Retrieved: 2026-05-27
  - Decision: require `OPENALEX_API_KEY`, support 1Password `op://` references, and keep concrete credentials out of tracked files.
- OpenAlex filtering docs: `https://developers.openalex.org/guides/filtering`
  - Retrieved: 2026-06-15
  - Decision: map `OPENALEX_FROM_DATE` and `OPENALEX_TO_DATE` to official `from_publication_date` and `to_publication_date` convenience filters, combined with existing language/year filters in one `filter=` parameter.
  - Verification command: `PYTHONPATH=src python -m unittest tests.test_providers`.
  - Risk: OpenAlex accepts richer filter syntax than Katala exposes; Katala only validates and passes `YYYY-MM-DD` dates for now.
  - Rollback: unset `OPENALEX_FROM_DATE` and `OPENALEX_TO_DATE`, or remove their helper calls from `_openalex_params`.
  - Next refresh: 2026-07-15
- OpenAlex Works schema docs: `https://developers.openalex.org/api-reference/works/get-a-single-work`
  - Retrieved: 2026-06-15
  - Decision: retain OpenAlex `primary_location`, `best_oa_location`, and `content_url` links in result metadata so downstream readers can choose landing pages, PDFs, or OpenAlex cached content.
  - Verification command: `PYTHONPATH=src python -m unittest tests.test_providers`.
  - Risk: some works omit PDF or OA location fields; metadata is sparse and only non-empty fields are stored.
  - Rollback: remove `_openalex_metadata` assignment from `OpenAlexSearch.search`.
  - Next refresh: 2026-07-15
- OpenAlex paging docs: `https://developers.openalex.org/guides/page-through-results`
  - Retrieved: 2026-06-15
  - Decision: use official cursor paging (`cursor=*`, then `meta.next_cursor`) for bounded multi-page scholarly candidate retrieval.
  - Verification command: `PYTHONPATH=src python -m unittest tests.test_providers`.
  - Risk: cursor paging should not be used to bulk-download OpenAlex; Katala stops at the requested limit.
  - Rollback: remove cursor handling from `OpenAlexSearch.search` and return to a single `per_page <= 100` request.
  - Next refresh: 2026-07-15
- OpenAlex full-text and abstract filter docs: `https://developers.openalex.org/guides/recipes`, `https://developers.openalex.org/download/full-text-pdfs`, `https://developers.openalex.org/api-reference/works/get-a-single-work`
  - Retrieved: 2026-06-15
  - Decision: map `OPENALEX_HAS_PDF` and `OPENALEX_HAS_ABSTRACT` to official `has_content.pdf` and `has_abstract` filters for candidate filtering only.
  - Verification command: `PYTHONPATH=src python -m unittest tests.test_providers`.
  - Risk: `has_content.pdf:true` finds downloadable-content candidates; actual content API downloads may require API key and usage costs. Katala search does not download content here.
  - Rollback: unset `OPENALEX_HAS_PDF` and `OPENALEX_HAS_ABSTRACT`, or remove their helper calls from `_openalex_params`.
  - Next refresh: 2026-07-15
- Brave Search API docs: `https://api-dashboard.search.brave.com/app/documentation/web-search/get-started`
  - Decision: support optional `BRAVE_SEARCH_API_KEY` provider for the official Web Search API endpoint.

## Metasearch Evidence Record

- local config: `.env` is ignored; `.env.example` contains only placeholder 1Password reference shape.
- decision: `meta` fans out across `KWR_META_PROFILE` or `KWR_META_PROVIDERS`, isolates engine failures, normalizes into `SearchResult`, applies Reciprocal Rank Fusion, then applies Katala-style Gate -> Scorer -> Selector ranking.
- verification command: `op run --env-file=.env -- scripts/benchmark-research-quality.py --iterations 30 --live-openalex --live-meta --out docs/research-quality-benchmark.md`
- risk: OpenAlex broad queries can return noisy scholarly candidates; GitHub-heavy themes can dominate unless source quotas and query rewriting improve.
- rollback: set `KWR_PROVIDER=ddg` or remove `meta,openalex` from `KWR_META_PROVIDERS`.
- next refresh: 2026-06-27

## Design Consequence

The MVP keeps the core loop small:

1. search provider returns ranked URLs
2. reader captures pages as text
3. archive stores runs and pages in SQLite FTS5
4. repository scanner indexes local GitHub corpus docs into SQLite FTS5
5. MCP stdio server exposes the same search/read/query/brief capabilities to coding agents
6. brief/report emits reviewable Markdown with URLs, local evidence, and fetch metadata

This avoids a heavy crawler, avoids browser/session secrets, and leaves provider replacement straightforward.
