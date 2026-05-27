# Metasearch Enhancement Research

- date: 2026-05-27
- scope: next OSS techniques to strengthen the Katala/SearXNG-inspired research engine
- decision boundary: keep `katala-web-research` MIT-compatible; do not vendor AGPL SearXNG code

## Current Baseline

The engine already has:

- provider adapters: `ddg`, `github`, `openalex`, `searxng`, `brave`, `jina`
- `meta` fan-out with per-engine failure isolation
- normalized `SearchResult`
- Katala-style Gate -> Scorer -> Selector ranking
- token-budget and research-quality benchmark gates

## Highest-Value Additions

### 1. Rank Fusion Layer

Add explicit Reciprocal Rank Fusion before final Katala scoring.

Why:

- RRF combines ranks without trusting incompatible engine score scales.
- It fits metasearch better than raw-score averaging because DDG, GitHub, OpenAlex, SearXNG, and future local indexes do not expose comparable scores.
- It is simple enough to test deterministically.

Implementation shape:

```text
engine results -> per-engine rank lists -> RRF score -> source-quality score -> diversity selector
```

Recommended first patch:

- add `fusion.py` with `reciprocal_rank_fusion(result_lists, k=60)`
- preserve each engine's original rank in metadata
- add benchmark cases where a result appearing in two engines outranks a single-engine outlier

Primary sources:

- Cormack, Clarke, Buettcher, "Reciprocal Rank Fusion outperforms Condorcet and individual Rank Learning Methods": https://cormack.uwaterloo.ca/cormacksigir09-rrf.pdf
- Qdrant hybrid queries with RRF: https://qdrant.tech/documentation/search/hybrid-queries/
- Vespa hybrid search tutorial: https://docs.vespa.ai/en/learn/tutorials/hybrid-search

### 2. Engine Profiles And Query Rewriting

Add source profiles instead of one global `KWR_META_PROVIDERS` list.

Suggested profiles:

- `docs`: `ddg,searxng,github,jina`
- `scholarly`: `openalex,searxng,ddg`
- `code`: `github,searxng,ddg`
- `fresh`: `ddg,searxng,brave`
- `local`: `repos,sqlite_fts,ddg`

Each profile should rewrite the query differently:

- OpenAlex: paper-like terms, year filters, citation expansion
- GitHub: repo/package/framework terms
- SearXNG/DDG: broad web terms plus `site:` constraints when useful
- local corpus: exact project terms and filenames

Why:

- The current live benchmark shows OpenAlex can return broad/noisy scholarly results for agentic-search phrases.
- Profile-specific rewrites should improve recall without increasing global token output.

Local inputs:

- `/Users/s30519/work/agent-skills-private/skills/openalex-search/SKILL.md` already documents year, open-access, citation, author, and detail workflows.
- `/Users/s30519/work/research/vendor/mcp-searxng/README.md` exposes useful search parameters: pagination, language, safe search, time range, URL read, and content cache.

### 3. Self-Hosted SearXNG Adapter Hardening

Keep SearXNG as an external service adapter, not a vendored module.

Useful SearXNG features to expose:

- `engines`
- `categories`
- `language`
- `time_range`
- `safesearch`
- JSON format availability preflight
- engine health and latency tracking

Why:

- SearXNG has a large adapter catalog and configurable engine selection.
- The project is AGPL-3.0, so MIT compatibility is safest when integration stays over the HTTP API boundary.

Primary sources:

- SearXNG source/license: https://github.com/searxng/searxng
- SearXNG engine docs: https://docs.searxng.org/dev/engines/index.html
- SearXNG settings docs: https://docs.searxng.org/admin/settings/settings.html
- SearXNG Search API: https://docs.searxng.org/dev/search_api.html

### 4. Local Hybrid Retrieval

Strengthen local repo/capture search with lexical + vector retrieval, then fuse with RRF.

Low-risk path:

1. keep current SQLite FTS5 as the default lexical path
2. add an optional LanceDB or Qdrant index behind a provider boundary
3. fuse `sqlite_fts`, `vector`, and `web_meta` ranks
4. benchmark on fixed repo fixtures before live docs

Candidate OSS stacks:

- LanceDB: good Python fit, supports rerankers and hybrid reranking; keep optional.
- Qdrant: stronger multi-vector/sparse-dense API; heavier service dependency.
- Vespa/OpenSearch: powerful, but too heavy for the first local CLI integration.

Primary sources:

- LanceDB reranking: https://docs.lancedb.com/reranking
- Qdrant hybrid queries: https://qdrant.tech/documentation/search/hybrid-queries/
- Vespa hybrid search tutorial: https://docs.vespa.ai/en/learn/tutorials/hybrid-search

### 5. Contextual Indexing

Add document-level context to indexed chunks before search.

Why:

- Raw chunks lose document context.
- Contextual BM25/embeddings are a practical way to reduce retrieval misses.
- For this repo, contextual indexing should start offline and bounded to local repo docs, not live pages.

Safe first version:

- add deterministic metadata context, not LLM-generated context:
  - repo name
  - relative path
  - heading path
  - file type
  - nearest symbols
- only later add optional LLM contextualization behind a budget gate

Primary source:

- Anthropic Contextual Retrieval: https://www.anthropic.com/engineering/contextual-retrieval

### 6. Advanced Reranking Experiments

Run only after RRF and profile rewrites are benchmarked.

Candidates:

- SPLADE-like sparse expansion for exact-term plus semantic recall
- ColBERT-style late interaction for high-quality reranking
- HyDE for zero-shot dense retrieval on local corpus queries

Risks:

- higher dependency and model cost
- slower local verification
- benchmark drift if added before enough relevance labels exist

Primary sources:

- SPLADE v2: https://arxiv.org/abs/2109.10086
- ColBERTv2: https://arxiv.org/abs/2112.01488
- HyDE: https://arxiv.org/abs/2212.10496

## Benchmark Additions

Add these before heavy model-based retrieval:

- `fusion_duplicate_consensus`: same URL appears from multiple engines and should move up.
- `engine_outlier_penalty`: one high-rank noisy engine result should not dominate.
- `profile_scholarly`: OpenAlex should surface papers, not generic web docs.
- `profile_code`: GitHub/source docs should outrank generic blogs for implementation queries.
- `local_context`: same keyword in a matching repo/path should outrank a generic occurrence.
- `latency_budget`: meta search should stay under a configured p95 budget with failed engines.
- `token_budget_live_meta`: live meta output must stay bounded.

Evaluation metrics to track:

- Recall@K for known preferred URLs
- MRR@K for first useful source
- nDCG@10 once graded labels exist
- source diversity ratio
- host diversity ratio
- engine failure rate
- p95 latency
- approximate output tokens

BEIR is the right external benchmark family once a local retrieval index exists. Start with a small subset, because full BEIR integration is too large for the current CLI gate.

Primary source:

- BEIR paper: https://datasets-benchmarks-proceedings.neurips.cc/paper_files/paper/2021/file/65b9eea6e1cc6bb9f0cd2a47751a186f-Paper-round2.pdf

## Local Katala Transfer

Apply these Katala Match ideas directly:

- typed pipeline stages from `core/pipeline.py`
- diversity caps and discovery floor from `core/anti_bubble.py`
- failure taxonomy from `docs/LLM_OPTIMIZATION.md`
- inspectable score axes from connector/mediator docs

Search-specific mapping:

- `retrieval_miss`: preferred source absent from all providers
- `ranking_miss`: preferred source retrieved but below Top-K
- `context_overload`: Top-K contains too many near-duplicates
- `citation_miss`: source lacks stable URL/date/source type
- `tool_loop`: repeated engine retries without new evidence

## Recommended Order

1. RRF fusion layer with deterministic tests.
2. Engine profiles and query rewriting.
3. SearXNG HTTP adapter parameters and health scores.
4. Local contextual FTS metadata.
5. Optional LanceDB/Qdrant hybrid retrieval spike.
6. BEIR/small relevance-label benchmark.
7. SPLADE/ColBERT/HyDE experiments only after labels and budgets are stable.

## Adopt / Skip

- Adopt now: RRF, profiles, SearXNG parameter pass-through, contextual FTS metadata.
- Pilot next: LanceDB optional local hybrid index, OpenAlex citation expansion, MCP-style URL read cache.
- Defer: Qdrant/Vespa/OpenSearch service dependency, ColBERT/SPLADE model stack, online contextual bandit.
- Avoid: vendoring SearXNG AGPL source into the MIT repo.
