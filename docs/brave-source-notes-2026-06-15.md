# Brave Search Source Notes

date: 2026-06-15
local object store: `C:\Users\ogosh\work\firecrawl-research\mirrors\github-searxng\searxng`
commit: `cf1410a`
official docs: `https://api-dashboard.search.brave.com/api-reference/web/search/post`

Read source paths:
- `searx/engines/braveapi.py`
- `searx/engines/brave.py`
- `searx/settings.yml`

Observed engine shape:
- SearXNG has both official API (`braveapi.py`) and HTML-scraping (`brave.py`) engines.
- The official API engine requires an API key, sends `q`, `count`, and `offset`, and maps SearXNG time ranges to Brave API date freshness values.
- The HTML engine controls safesearch, region, and UI language through cookies and documents Brave's limited locale behavior.
- Brave's current official API documentation names the date-age parameter `freshness` and supports `pd`, `pw`, `pm`, `py`, or a custom `YYYY-MM-DDtoYYYY-MM-DD` range.
- Official API parameters include `country`, `search_lang`, `ui_lang`, `count`, `offset`, `safesearch`, and `freshness`.

Katala adaptation chosen now:
- Keep Katala on the official Brave Web Search API path, not HTML scraping.
- Add `BRAVE_SEARCH_COUNTRY`, `BRAVE_SEARCH_LANG`, and `BRAVE_UI_LANG` pass-through for localized search control.
- Add `BRAVE_FRESHNESS` with day/week/month/year aliases mapped to Brave's official `pd`/`pw`/`pm`/`py` values, plus custom date-range pass-through.
- Add `BRAVE_SAFESEARCH` validation for official values: `off`, `moderate`, and `strict`.
- Keep `count` capped at Brave's official maximum of 20.
- Add paging with Brave's official `offset` parameter when Katala asks for more than 20 Brave candidates, capped at the documented maximum offset of 9.

Verification:
- `tests.test_providers.ProviderTests.test_brave_provider_passes_optional_api_parameters` covers query parameter mapping.
- `tests.test_providers.ProviderTests.test_brave_provider_fetches_multiple_pages_for_large_limits` covers paging.
- `tests.test_providers.ProviderTests.test_brave_provider_rejects_invalid_filters_before_fetch` covers local validation.

Next candidates:
- Expose Brave `result_filter=web` if paid-plan enrichments create noisy mixed result payloads.
