# SearXNG Source Notes

date: 2026-06-15
commit: `cf1410a`

Checkout note:
- `git clone --depth 1 https://github.com/searxng/searxng.git ...` succeeded at object fetch but failed to checkout on Windows because the repository contains paths with `:socket`.
- Source was read through `git show` and `git grep` against `HEAD`; no SearXNG source is vendored into this MIT repository.

Read source paths:
- `searx/webadapter.py`
- `searx/results.py`
- `searx/search/__init__.py`
- `searx/search/models.py`
- `searx/search/processors/abstract.py`
- `searx/search/processors/online.py`
- `docs/dev/search_api.rst`

Observed search architecture:
- Request parsing validates `pageno`, `language`, `safesearch`, and `time_range` before building the `SearchQuery`.
- Search processors skip engines when query conditions are unsupported, including unsupported pagination or time range filters.
- Search fan-out tracks timeout and unresponsive engines in the result container.
- Result merging keeps the contributing engine set and positions; scoring rewards multi-engine agreement and earlier positions.
- The JSON API exposes `categories`, `engines`, `language`, `pageno`, `time_range`, `format`, and `safesearch`.

Katala adaptation chosen now:
- Keep SearXNG behind the existing HTTP provider boundary.
- Validate `KWR_SEARXNG_TIME_RANGE` and `KWR_SEARXNG_SAFESEARCH` locally before making HTTP requests.
- Preserve pass-through for instance-specific `categories`, `engines`, and `language` values because those depend on the configured SearXNG instance.
- Preserve each provider's original rank as `metadata.provider_rank` before Katala final ranking overwrites `rank`, matching SearXNG's useful separation between source positions and final merged order.
- Add `kwr doctor --check-searxng` to probe the configured SearXNG `/search?...format=json` endpoint and verify that the response contains a JSON `results` list.
- Add `KWR_HTTP_TIMEOUT_SECONDS` so operators can bound provider and reader HTTP calls without changing code.

Next candidates:
- Compare timeout defaults against live provider latency before adding profile-specific timeout defaults.
