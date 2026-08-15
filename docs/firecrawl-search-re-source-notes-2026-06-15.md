# Firecrawl Search Source RE Notes

date: 2026-06-15

Read source paths:
- `apps/api/src/search/execute.ts`
- `apps/api/src/search/v2/index.ts`
- `apps/api/src/search/v2/fireEngine-v2.ts`
- `apps/api/src/search/v2/searxng.ts`
- `apps/api/src/search/scrape.ts`
- `apps/api/src/search/highlights.ts`
- `apps/api/src/lib/search-query-builder.ts`

Observed search architecture:
- `executeSearch` requests `limit * 2` upstream candidates, then trims each result type back to the requested limit.
- Query building supports category/domain filters such as GitHub, research sites, PDF, include domains, and exclude domains.
- Provider selection prefers Firecrawl's Fire Engine when configured, falls back to SearXNG when configured, then falls back to DuckDuckGo.
- Search can optionally scrape returned web/news/image results, merge the page document back into the normalized result, and charge/track search vs scrape credits separately.
- Highlight generation can replace provider snippets with query-relevant excerpts from an existing index, gated by feature flag and required environment.
- SearXNG pagination fetches enough pages to satisfy requested result count, then trims to the request limit.

Katala adaptation chosen now:
- Add a local-first `enrich_search_results` workflow step: search first, optionally read the top N results with the existing reader, attach read metadata, replace the thin snippet with page text, then re-rank.
- Expose it as `kwr search --enrich-top N --reader auto|jina|direct`.
- Keep the default side-effect-free search behavior unchanged by making `--enrich-top 0` the default.
- Add a Firecrawl-style query builder for `kwr search`: `--category github|research|pdf`, `--include-domain`, and `--exclude-domain`.
- Annotate matching results with `metadata.query_category` so downstream report/ranking code can inspect why a result matched the query intent.
- Add archive-backed highlights: `kwr search --highlight-top N` looks up the top N result URLs in the local SQLite `pages` archive, replaces thin provider snippets with query-matching page excerpts, marks `metadata.highlight_status`, and re-ranks.
- Add candidate buffer control: `kwr search`, `kwr brief`, and `kwr investigate` can fetch more provider candidates than the final limit before Katala ranking trims results. CLI default mirrors Firecrawl's `limit * 2` shape via `--candidate-multiplier 2`.
- Add SearXNG pagination: when the requested provider limit exceeds one SearXNG page, the provider requests later pages with `pageno` and then lets Katala ranking handle the merged candidate set.

Why this fits Katala:
- It mirrors Firecrawl's useful `search -> scrape/read -> merge -> rank` shape without copying Firecrawl implementation code.
- It remains local-first and provider-agnostic; Jina/direct readers are already in the codebase.
- Failures are observable through `read_status` and `read_error_kind` metadata rather than hidden or fatal.

Next candidates:
- Add image/news typed result support only if Katala callers need those result classes.
- Benchmark candidate multiplier defaults per profile before exposing profile-specific defaults.
