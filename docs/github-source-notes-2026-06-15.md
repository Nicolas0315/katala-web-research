# GitHub Search Source Notes

date: 2026-06-15
source: SearXNG `searx/engines/github.py` and `searx/engines/github_code.py`
commit: `cf1410a`

Observed engine shape:
- Repository search uses GitHub's official REST repository search endpoint.
- Results preserve package-style metadata: owner, language, topics, stars, license, homepage, and clone URL.
- GitHub code search sends `X-GitHub-Api-Version: 2022-11-28`.
- Code search requests text-match metadata and normalizes fragments for display.

Katala adaptation chosen now:
- GitHub REST provider sends `X-GitHub-Api-Version: 2022-11-28`.
- GitHub repository results keep richer metadata:
  - `package_name`
  - `maintainer`
  - `language`
  - `topics`
  - `stars`
  - `license_name`
  - `license_url`
  - `homepage`
  - `source_code_url`
- Snippets now include language, license, and topics when available.
- Added a separate `github_code` provider for code-result snippets.
- `github_code` requires `GITHUB_TOKEN`, requests `application/vnd.github.text-match+json`, sends `X-GitHub-Api-Version: 2022-11-28`, and preserves repository/path/fragment metadata.
- `github_code` pages through GitHub's `page` parameter when Katala asks for more than 100 code candidates.
- Invalid code-search syntax that GitHub returns as HTTP 422 is treated as an empty result set, matching SearXNG's engine behavior.
- `github_code` is exposed through `kwr search --provider github_code`.
- `github_code` is exposed through the MCP provider enum for `kwr.search`, `kwr.brief`, and `kwr.investigate`.
- The `code` metasearch profile now fans out to `github_code` before repository search.

Verification:
- `tests.test_providers.ProviderTests.test_github_rest_provider_keeps_repo_metadata` covers REST metadata and API version header.
- `tests.test_providers.ProviderTests.test_github_code_provider_requires_token` covers local auth gating.
- `tests.test_providers.ProviderTests.test_github_code_provider_keeps_code_metadata` covers text-match metadata parsing and headers.
- `tests.test_providers.ProviderTests.test_github_code_provider_fetches_multiple_pages_for_large_limits` covers paging.
- `tests.test_providers.ProviderTests.test_github_code_provider_returns_empty_for_invalid_query` covers invalid query handling.
- `tests.test_cli_search.CliSearchTests.test_search_accepts_github_code_provider` covers CLI provider routing.
- `tests.test_mcp_server.McpServerTests.test_search_tool_lists_github_code_provider` covers MCP provider discovery.

Next candidates:
- Consider `GITHUB_TOKEN` via `op://` only if a concrete workflow needs it; current provider keeps token handling simple.
