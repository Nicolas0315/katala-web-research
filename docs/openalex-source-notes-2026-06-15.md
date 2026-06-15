# OpenAlex Source Notes

date: 2026-06-15
source: SearXNG `searx/engines/openalex.py`
local object store: `C:\Users\ogosh\work\firecrawl-research\mirrors\github-searxng\searxng`
commit: `cf1410a`

Observed engine shape:
- Uses the official OpenAlex Works endpoint.
- Does not require an API key.
- Supports optional `mailto` for OpenAlex polite pool behavior.
- Uses `search`, `per-page`, `sort=relevance_score:desc`, and selected scholarly result fields.
- Reconstructs abstracts from `abstract_inverted_index` and maps bibliographic metadata into paper results.

Katala adaptation chosen now:
- OpenAlex provider no longer requires `OPENALEX_API_KEY`.
- `OPENALEX_API_KEY` remains supported when configured.
- Added optional `OPENALEX_MAILTO` pass-through.
- Added optional `OPENALEX_LANGUAGE`; values such as `en-US` are mapped to OpenAlex `filter=language:en`, matching SearXNG's engine behavior.
- Added optional `OPENALEX_YEAR`; four-digit values are mapped to OpenAlex `filter=publication_year:<year>` and are combined with the language filter when both are set.
- Added optional `OPENALEX_FROM_DATE` and `OPENALEX_TO_DATE`; `YYYY-MM-DD` values are mapped to official OpenAlex `from_publication_date` and `to_publication_date` convenience filters.
- Added optional `OPENALEX_HAS_PDF` and `OPENALEX_HAS_ABSTRACT`; boolean-like values map to official `has_content.pdf:true|false` and `has_abstract:true|false` filters.
- OpenAlex results retain `primary_location`, `best_oa_location`, `content_url`, DOI, citation, and access-status metadata when returned, including landing page and PDF URLs.
- OpenAlex provider uses official cursor paging (`cursor=*`, then `meta.next_cursor`) when Katala requests more than one 100-result page. This is bounded to the requested candidate count, not used for bulk dataset download.
- Provider status now reports OpenAlex as available by default because the official API is public.

Verification:
- `tests.test_providers.ProviderTests.test_openalex_provider_parses_work_results` covers no-key operation and location/content metadata retention.
- `tests.test_providers.ProviderTests.test_openalex_provider_adds_optional_key_and_mailto` covers optional parameter pass-through, including language, publication-year, publication-date range, PDF availability, and abstract availability filter mapping.
- `tests.test_providers.ProviderTests.test_openalex_provider_rejects_invalid_date_filter_before_fetch` covers local date validation.
- `tests.test_providers.ProviderTests.test_openalex_provider_rejects_invalid_boolean_filter_before_fetch` covers local boolean filter validation.
- `tests.test_providers.ProviderTests.test_openalex_provider_fetches_multiple_cursor_pages_for_large_limits` covers cursor paging.

Next candidates:
- Consider exposing OpenAlex `open_access.is_oa` or `best_oa_location.license` filters if downstream workflows need license-aware candidate pools.
