# RL And Evaluation Roadmap

This repository should not jump directly to online reinforcement learning. Research workflows can overfit to noisy rewards such as clickability, SEO-heavy pages, or verbose reports. The safe progression is:

1. deterministic offline evaluation
2. structured action logs
3. learning-to-rank on fixed judgments
4. contextual bandits for provider and read-top selection
5. preference learning or offline RL only after enough reviewed traces exist

## Action Surface

The learnable policy can eventually choose:

- query plan shape
- provider selection
- candidate reranking
- read-top selection
- stopping point
- token allocation

The current implementation keeps these actions explicit through:

- `kwr plan`
- `kwr brief --expand-queries`
- `kwr investigate --expand-queries`
- `kwr eval`
- `scripts/benchmark-token-budget.py`

## Reward Signals

Use a composite reward. Do not reward raw clicks or result count alone.

Recommended positive signals:

- official or primary source coverage
- expected good URL in top results
- citation/capture availability
- local corpus agreement
- contradiction discovery
- freshness when the task is time-sensitive

Recommended penalties:

- discouraged source above preferred source
- missing official or primary source
- token budget overrun
- excessive page capture
- duplicate URLs
- stale pages for current API or product questions

## Current Offline Benchmark

`kwr eval` runs fixed cases with known preferred and discouraged sources. It scores:

- query-plan intent coverage
- preferred URL terms in top candidates
- top source-quality band
- discouraged source ordering

This is intentionally small and deterministic. It is a regression gate, not a full relevance benchmark.

## Next Learning Step

The next practical learning feature is a simple learning-to-rank dataset:

```json
{
  "query": "agentic retrieval source quality",
  "url": "https://learn.microsoft.com/en-us/azure/search/agentic-retrieval-overview",
  "features": {
    "source_quality": 100,
    "query_overlap": 3,
    "is_primary": true,
    "is_fresh": false
  },
  "label": 1
}
```

A contextual bandit should come after this, using `kwr eval` and human-reviewed reports as offline validation before any automatic online adaptation.
