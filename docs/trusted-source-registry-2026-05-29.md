# Trusted Source Registry - 2026-05-29

Katala Web Research can use the cross-domain source taxonomy as a first-class
enhancement. The right shape is a trusted source registry, not a single global
truth score.

## Why This Matters

Search quality differs by question type:

- legal questions need primary law, regulators, and case law
- medical questions need reviews, trials, guidelines, and original papers
- security questions need vulnerability databases, exploited-vulnerability
  catalogs, vendor advisories, and researcher reports
- news questions need source comparison, political framing, ownership, and
  fact-check context
- economics questions need official statistics and dataset revision awareness
- technical questions need official docs, standards, release notes, and source
  repositories

A domain list alone is not enough. Katala needs source metadata that tells the
ranker what a source is good for, when it goes stale, and what bias or caveat
the operator should keep in view.

## Current Implementation

The seed registry lives in:

```text
src/katala_web_research/data/source_registry.json
```

Public interfaces:

```sh
kwr sources list --domain security --json
kwr sources list --domain news --query-type media_bias
kwr sources match https://www.cisa.gov/known-exploited-vulnerabilities-catalog --json
```

The registry reader is:

```text
src/katala_web_research/source_registry.py
```

`source_quality.py` now consults the registry before falling back to built-in
host heuristics. If a URL matches a registry host or URL prefix, the registry
source type and trust score are used for ranking.

`kwr brief` and `kwr investigate` now include registry metadata for matched web
candidates:

- `registry_source`
- `registry_domain`
- `registry_freshness`
- `registry_update_cadence`
- `registry_trust_score`
- `bias_caveat`

Operator overlays can extend or override the seed registry without editing
package data:

```sh
KWR_SOURCE_REGISTRY_OVERLAY=~/work/docs/source-registry-overlay.json \
kwr sources list --domain custom_domain --json
```

The overlay file uses the same JSON shape as the seed file and is merged by
`domain`, `source_type`, and `name`.

## Registry Fields

Each source entry includes:

- `domain`
- `source_type`
- `query_types`
- `url`
- `hosts`
- `url_prefixes`
- `best_for`
- `freshness`
- `trust_score`
- `bias_caveat`
- `update_cadence`
- `avoid_for`

This lets Katala distinguish "good for discovery" from "good as final evidence".

## Seed Domains

Current seed domains:

- `news`
- `fact_check`
- `scholarly`
- `medicine`
- `law_jp`
- `security`
- `economics`
- `custom_search`

Examples:

- `security/exploited_vulnerability`: CISA Known Exploited Vulnerabilities
  Catalog.
- `medicine/systematic_review`: Cochrane Library.
- `law_jp/primary_law`: e-Gov Law Search.
- `news/bias_compare`: Ground News.
- `custom_search/custom_ranking_rules`: Brave Goggles.

The seed registry is an operator-curated routing layer. It is not legal,
medical, financial, or security advice, and it does not remove the need to read
the underlying source.

## Benchmark Coverage

`kwr eval` includes a `bias_aware_news` case:

```text
news coverage political bias comparison
```

Expected behavior: bias-comparison sources such as Ground News and source-rating
references outrank a generic single-site commentary post for that query type.

The benchmark also covers:

- platform API docs
- AI vendor docs
- scholarly research
- metasearch fusion
- feed monitoring
- security advisories
- legal/regulatory guidance
- open-source implementation research
- product release freshness

## Next Enhancements

1. Add per-domain freshness deadlines so stale source classes trigger warning
   labels.
2. Add negative source rules for SEO spam, hallucinated mirrors, parked domains,
   and unreviewed content farms.
3. Add source recommendation blocks to `kwr plan` output.
4. Add registry export/import validation so private overlays can be linted
   before use.
