# Research Quality Benchmark Log

- date: 2026-05-27
- scope: deterministic local evaluation plus token-budget benchmark
- network required: no for deterministic eval; yes only for optional live web benchmark
- gate command: `scripts/verify.sh`

## Deterministic Evaluation

Command:

```sh
PYTHONPATH=src python3 -m katala_web_research.cli eval --json
```

Observed result:

```text
score: 93
min_score: 80
passed: true
cases: 3
```

Covered cases:

- `agentic_retrieval_prefers_official_and_primary`
- `citations_prefers_vendor_docs`
- `papers_surface_primary_research`

## Token Budget Benchmark

Command:

```sh
scripts/benchmark-token-budget.py
```

Observed result:

```text
ok plan: approx_tokens=52 budget=350 chars=182
ok eval: approx_tokens=447 budget=900 chars=1563
ok repos_scan: approx_tokens=69 budget=700 chars=241
ok repos_query: approx_tokens=264 budget=1400 chars=921
ok brief_no_web: approx_tokens=554 budget=800 chars=1937
ok investigate_no_web: approx_tokens=687 budget=1400 chars=2403
```

## Live Expanded Benchmark

Command:

```sh
scripts/benchmark-token-budget.py --root ~/Documents/GitHub --query "agentic retrieval" --live-web
```

Observed result:

```text
ok plan: approx_tokens=63 budget=350 chars=218
ok eval: approx_tokens=447 budget=900 chars=1563
ok repos_scan: approx_tokens=59 budget=700 chars=205
ok repos_query: approx_tokens=0 budget=1400 chars=0
ok brief_no_web: approx_tokens=190 budget=800 chars=664
ok investigate_no_web: approx_tokens=324 budget=1400 chars=1134
ok investigate_live_web: approx_tokens=1408 budget=4500 chars=4926
```

## Interpretation

The current gate verifies that bounded query planning and source-quality reranking improve source selection without expanding output beyond budget. This gives a stable baseline for later learning-to-rank or bandit experiments.
