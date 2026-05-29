# Research Quality Benchmark Log

- date: 2026-05-29
- scope: deterministic local evaluation plus optional OpenAlex/meta live checks
- network required: no for deterministic eval; yes for `--live-openalex` or `--live-meta`
- gate command: `scripts/verify.sh`

## Deterministic Multi-Run Evaluation

- iterations: 10
- case_count: 10
- min_score: 94
- max_score: 94
- mean_score: 94
- all_passed: true

## Domain Category Scores

- ai_vendor_docs: min=100 max=100 mean=100
- bias_aware_news: min=80 max=80 mean=80
- feed_monitoring: min=100 max=100 mean=100
- legal_regulatory: min=100 max=100 mean=100
- metasearch_fusion: min=100 max=100 mean=100
- open_source_code: min=100 max=100 mean=100
- platform_api_docs: min=80 max=80 mean=80
- product_release_freshness: min=100 max=100 mean=100
- scholarly_research: min=100 max=100 mean=100
- security_advisory: min=80 max=80 mean=80

## Themes

- agentic retrieval source quality
- Claude citations source documents
- query decomposition retrieval augmented generation evaluation
- agent search documentation rank fusion
- Python release feed security notes
- Node.js OpenSSL vulnerability advisory
- FTC endorsements disclosure business guidance
- SearXNG engine adapter implementation
- OpenAI Agents SDK changelog release notes
- news coverage political bias comparison

## Token Budget Benchmark

- ok `plan` approx_tokens=52 budget=350 chars=182
- ok `eval` approx_tokens=1455 budget=1600 chars=5091
- ok `repos_scan` approx_tokens=69 budget=700 chars=241
- ok `repos_query` approx_tokens=270 budget=1400 chars=942
- ok `brief_no_web` approx_tokens=567 budget=800 chars=1983
- ok `investigate_no_web` approx_tokens=700 budget=1400 chars=2449

## Live OpenAlex

- ok `agentic retrieval source quality` count=5 top_score=3.43 top=https://doi.org/10.1371/journal.pmed.1000100
- ok `Claude citations source documents` count=5 top_score=3.71 top=https://doi.org/10.5281/zenodo.19442251
- ok `query decomposition retrieval augmented generation evaluation` count=5 top_score=1.44 top=https://doi.org/10.1038/s41592-019-0686-2

## Live Meta

- ok `agentic retrieval source quality` count=5 sources={'github': 4, 'ddg': 1} top_score=6.395 top=https://github.com/pamela-ballesteros/RAG_AgenticAI
- ok `Claude citations source documents` count=5 sources={'github': 4, 'ddg': 1} top_score=6.518 top=https://github.com/claycantrell/claude-research-scaffold
- ok `query decomposition retrieval augmented generation evaluation` count=5 sources={'github': 1, 'ddg': 4} top_score=8.169 top=https://github.com/eeshaal2/ParaHopRAG

## Interpretation

This benchmark applies the Katala-style Gate -> Scorer -> Selector discipline to research search: fail closed on unusable/retracted candidates, score with source and relevance features, then select with diversity caps so one host or source class cannot dominate every result.
