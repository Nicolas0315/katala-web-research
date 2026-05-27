# Metasearch Implementation Plan

- date: 2026-05-27
- goal: move every identified enhancement forward without adding unsafe dependencies or leaking secrets
- current scope: implement the low-dependency core; track heavier experiments in GitHub

## Boundary

Ship now:

- Reciprocal Rank Fusion for metasearch consensus.
- Engine profiles and query rewriting.
- SearXNG HTTP parameter pass-through.
- Deterministic local repo context metadata for FTS.
- Benchmark cases for fusion, profiles, and local context.

Track as follow-up:

- LanceDB/Qdrant optional hybrid retrieval.
- BEIR or BEIR-like external benchmark subset.
- SPLADE, ColBERT, HyDE, and learned reranking.
- Online contextual bandit or reinforcement learning.

Do not do:

- Do not vendor AGPL SearXNG source into this MIT repo.
- Do not commit `.env`, API keys, session files, SQLite archives, or raw logs.
- Do not add mandatory model or vector database dependencies to the default CLI path.

## Work Breakdown

### Phase 1: Fusion Core

Deliverables:

- `src/katala_web_research/fusion.py`
- deterministic tests for duplicate consensus and noisy outlier handling
- `meta` provider uses fusion before final Katala scoring

Acceptance:

- a URL appearing across two engines outranks a single-engine outlier
- per-engine failures still do not fail the whole metasearch run
- output remains bounded by `--limit`

### Phase 2: Engine Profiles

Deliverables:

- profile resolver for `KWR_META_PROFILE`
- default providers per profile
- lightweight query rewrite per provider

Profiles:

- `broad`: `ddg,github,openalex,searxng`
- `docs`: `ddg,searxng,github,jina`
- `scholarly`: `openalex,searxng,ddg`
- `code`: `github,searxng,ddg`
- `fresh`: `ddg,searxng,brave`
- `local`: `ddg,github`

Acceptance:

- `KWR_META_PROVIDERS` still overrides the profile
- unknown profile fails closed to `broad`
- provider-specific query rewriting is deterministic and testable

### Phase 3: SearXNG Adapter Hardening

Deliverables:

- optional env pass-through for `categories`, `engines`, `language`, `time_range`, `safesearch`
- provider status mentions configured profile and SearXNG options
- tests verify query parameter construction

Acceptance:

- unset env preserves current behavior
- configured env values are encoded into the SearXNG `/search` URL

### Phase 4: Contextual Local FTS

Deliverables:

- deterministic context prefix for repo documents
- context metadata column stored with documents
- FTS indexes context plus content

Context fields:

- repo name
- relative path
- kind
- title
- first markdown heading path when available

Acceptance:

- repo query can match deterministic context terms
- old archives migrate forward
- incremental metadata skipping still works

### Phase 5: Evaluation And Operations

Deliverables:

- benchmark cases for fusion/profile/context
- docs updated with operation examples
- `scripts/verify.sh` remains the main gate

Acceptance:

- unit tests pass
- token benchmark passes
- research-quality benchmark passes
- `gitleaks` passes
- GitHub Actions CI passes

### Phase 6: GitHub Organization

Deliverables:

- branch/commit/PR or direct push depending on current repo policy and operator intent
- GitHub issues for heavier follow-up tracks
- CI result attached in final summary

Issue buckets:

- `research`: BEIR, SPLADE, ColBERT, HyDE
- `enhancement`: hybrid retrieval, profile tuning
- `benchmark`: relevance labels and live latency budget
- `security`: secret and dependency boundary checks

## Verification Commands

```sh
PYTHONPATH=src python3 -m unittest discover -s tests
./scripts/verify.sh
gitleaks dir . --no-banner --redact --exit-code 1
git diff --check
```

## Rollback

- Revert the final commit if implementation behavior regresses.
- Set `KWR_PROVIDER=ddg` to bypass metasearch.
- Set `KWR_META_PROVIDERS=ddg,github` to avoid optional live providers.
- Use a fresh archive path for repo scans if archive migration is suspect.
