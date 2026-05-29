# Domain Validation And Benchmark Plan - 2026-05-28

This plan defines how to validate repository adoption ideas, implementation
behavior, and domain-category search quality for Katala Web Research.

## Goals

- Verify that upstream repository ideas are adopted through safe boundaries.
- Verify the current implementation through public CLI/API behavior.
- Benchmark deterministic search-quality behavior across multiple domain
  categories.
- Keep all default gates offline and fixture-driven.
- Make optional live checks explicit and separate from the deterministic gate.

## Validation Layers

### 1. Adoption Validation

Purpose: decide whether a cloned GitHub repository idea can be used as-is,
adapted, isolated, or skipped.

Checks:

- local clone exists and has remote origin/HEAD evidence
- license boundary is known before code reuse
- AGPL/GPL projects are reference-only unless isolated behind an external
  service or URL-template adapter
- package/runtime weight is appropriate for a CLI-first Python project
- transferable idea maps to an existing Katala surface: provider, feed source,
  crawl queue, archive schema, ranking, benchmark, or MCP tool

Current adoption decisions:

- RSSHub, FreshRSS, Folo, SearXNG, Firecrawl, Lightpanda: reference or external
  service boundary only.
- RSS-Bridge, Crawlee, Scrapling, crawlkit, OpenKB, cognee, supermemory,
  DeerFlow, open_deep_research, MCP server repos: inspectable implementation
  references, subject to license and dependency review.

Gate command:

```sh
rtk env PYTHONPATH=src python3 -m katala_web_research.cli repos scan \
  /Users/s30519/work/nicolas-starred-repos/repos \
  --archive /tmp/kwr-clone-applicability-2026-05-28.sqlite \
  --max-repos 80 \
  --max-files-per-repo 8 \
  --json
```

Pass condition: bounded scan completes, indexes relevant docs, and does not
read secrets, sessions, dependency folders, caches, or build outputs.

### 2. Implementation Validation

Purpose: verify behavior through public interfaces, not internals.

Checks:

- `kwr eval` returns deterministic domain-category scores.
- `kwr feeds add/refresh/query` works with local RSS fixture.
- `kwr search --provider feed` can query the feed archive.
- `kwr repos scan/query` can create and search a bounded local corpus.
- `kwr sources list` exposes trusted source registry recommendations.
- `kwr sources match` explains how a URL maps to source type, trust score,
  freshness, and bias caveat.
- metasearch fusion and provider health tests pass.
- generated Markdown reports stay parseable and compact.

Gate commands:

```sh
rtk env PYTHONPATH=src python3 -m unittest discover -s tests
rtk scripts/verify.sh
rtk git diff --check
```

Pass condition: all commands return 0.

### 3. Benchmark Validation

Purpose: measure search-quality regressions across domain categories.

Default benchmark:

```sh
rtk scripts/benchmark-research-quality.py \
  --iterations 30 \
  --out docs/research-quality-benchmark.md \
  --json-out /tmp/katala-web-research-domain-benchmark.json
```

Pass condition:

- `all_passed: true`
- every category score is at least 80
- token-budget benchmark rows pass
- no network is required

Optional live benchmark:

```sh
rtk op run --env-file=.env -- scripts/benchmark-research-quality.py \
  --iterations 10 \
  --live-openalex \
  --live-meta \
  --out docs/research-quality-benchmark.md
```

Live benchmark results are evidence only. They are not the default regression
gate because provider availability, API keys, network state, and external
indices can drift.

## Domain Categories

| Category | What It Tests | Representative Query | Expected Source Behavior |
| --- | --- | --- | --- |
| `platform_api_docs` | API/search feature questions | `agentic retrieval source quality` | official docs and primary code beat vendor blog posts |
| `ai_vendor_docs` | AI product docs | `Claude citations source documents` | vendor docs beat generic tutorials |
| `scholarly_research` | papers and benchmarks | `query decomposition retrieval augmented generation evaluation` | arXiv/ACL sources beat generic RAG posts |
| `metasearch_fusion` | RRF/consensus behavior | `agent search documentation rank fusion` | consensus official result beats single-engine outlier |
| `bias_aware_news` | source-bias comparison | `news coverage political bias comparison` | bias-comparison/source-rating references beat single-site commentary |
| `feed_monitoring` | release/feed monitoring | `Python release feed security notes` | official release docs beat rumor posts |
| `security_advisory` | vulnerabilities and advisories | `Node.js OpenSSL vulnerability advisory` | primary advisory/NVD beat secondary commentary |
| `legal_regulatory` | laws/regulations/guidance | `FTC endorsements disclosure business guidance` | `.gov` guidance beats marketing summaries |
| `open_source_code` | implementation research | `SearXNG engine adapter implementation` | primary repo/docs beat blog explanations |
| `product_release_freshness` | changelogs and releases | `OpenAI Agents SDK changelog release notes` | official docs/release sources beat recaps |

## Failure Triage

- Low category score: inspect the category case in `kwr eval --json`.
- Preferred source below discouraged source: check `source_quality.py`, query
  token overlap, and provider/source boosts.
- Token-budget failure: inspect `scripts/benchmark-token-budget.py` output and
  reduce stdout/report verbosity.
- Live benchmark failure: rerun deterministic benchmark first; live failures
  do not block unless the current task explicitly depends on that provider.

## Current Expected Next Implementation Slices

1. OPML import/export for feed source portability.
2. Feed source presets for RSSHub/RSS-Bridge/official feeds.
3. Registry-aware source recommendations in reports.
4. SQLite crawl queue with HTTP-only default execution.
5. Static extractor interface, with Scrapling evaluated as first candidate.
6. Bounded research loop over query/read/gap-analysis actions.
