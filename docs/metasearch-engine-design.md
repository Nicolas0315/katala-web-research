# Katala Metasearch Engine Design

This project does not vendor or fork SearXNG. SearXNG is AGPL-3.0, broad, and operationally useful as a self-hosted metasearch service. `katala-web-research` stays MIT-compatible by adopting the architectural boundary rather than copying implementation code.

## SearXNG Reference Points

- source: https://github.com/searxng/searxng
- engine docs: https://docs.searxng.org/dev/engines/index.html
- settings docs: https://docs.searxng.org/admin/settings/index.html

Useful patterns:

- many small engine adapters
- settings-driven engine selection
- normalized result objects
- per-engine failure isolation
- privacy-respecting self-host option
- categories and result types

## Katala Adaptation

The local design adds Katala-style decision discipline after metasearch retrieval:

```text
Source engines -> Normalize -> Gate -> Scorer -> Selector -> Report / Archive
```

Mapping:

- Source engines: `ddg`, `feed`, `github`, `openalex`, `searxng`, optional `brave` and `jina`
- Normalize: all engines return `SearchResult`
- Gate: drop unusable URLs and retracted scholarly candidates
- Scorer: source quality, query fit, freshness, primary-source bonus, provider boost
- Selector: host and source-type diversity caps
- SideEffect: archive captures and benchmark reports

## Why This Can Beat A Plain SearXNG Instance

SearXNG is strong at broad fan-out. The Katala layer adds research-specific judgment:

- OpenAlex is useful for scholarly candidates but can drift on broad terms; the selector prevents it from dominating.
- GitHub is useful for implementation evidence but can overfit to repositories; source-type caps reduce that.
- DDG/SearXNG are useful web coverage engines; source-quality scoring keeps generic articles below official and primary sources.
- Local repo evidence gives prior-art comparison that public metasearch engines cannot see.

## Current Engine

`kwr search --provider meta` fans out over `KWR_META_PROFILE` or explicit `KWR_META_PROVIDERS`.

Example:

```sh
KWR_META_PROVIDERS=ddg,github,openalex \
op run --env-file=.env -- kwr search "research agent evaluation metrics" --provider meta --limit 8
```

The default profile is `broad`:

```text
ddg,github,openalex,searxng
```

Available profiles:

- `broad`: default web, code, scholarly, and SearXNG mix
- `docs`: official/vendor documentation bias
- `scholarly`: OpenAlex-first paper discovery
- `code`: GitHub-first implementation discovery
- `fresh`: current web/news-like discovery
- `local`: feed archive plus low-dependency DDG/GitHub path
- `monitoring`: feed archive first, then low-dependency DDG/GitHub path

Engines that lack credentials or URLs fail closed and do not block the whole search.

Before final Katala scoring, `meta` applies health-aware Reciprocal Rank Fusion so a URL seen by multiple healthy engines gets a consensus boost without trusting incompatible engine score scales. Each result carries `meta_engine_runs` metadata with provider status, latency, result count, bounded health score, and error kind for failed engines.

## Next Engine Improvements

- Host/source quotas exposed as config
- Optional local SearXNG instance bootstrap, kept outside the MIT code path
