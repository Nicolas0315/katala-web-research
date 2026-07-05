# Star Repo Search / Feed Application

Date: 2026-06-30

## Scope

This note records how the starred-repo scraping research applies to `katala-web-research` while `x-tweet-fetcher` is unavailable in the local Windows worktree.

The useful application is fixture-backed search/feed normalization, not live X/Twitter, browser, Nitter, or crawler execution.

## Mapping

- `searxng/searxng`: already maps to `SearxngSearch` JSON result normalization, optional parameter validation, pagination, and `kwr doctor --check-searxng` preflight semantics.
- `DIYgod/RSSHub`, `RSS-Bridge/rss-bridge`, `RSSNext/Folo`, `FreshRSS/FreshRSS`: map to local RSS/Atom/JSON Feed parsing and archived feed search, without deploying or polling those services from this repo.
- `firecrawl/firecrawl`: maps to the existing search/read/enrich pattern, candidate multiplier, archive highlights, and query category/domain filters; it does not justify adding Firecrawl runtime or external API usage here.
- `public-clis/twitter-cli`, Nitter, Camofox, and browser-agent candidates: saved output or snapshot vocabulary only. Do not run CLIs, browsers, Nitter searches, or account-backed X/Twitter flows from this lane.

## Local Verification

Executed with `PYTHONPATH=src`:

- `py -3 -m unittest tests.test_feeds tests.test_providers tests.test_cli_search`
  - Result: passed, 40 tests.
- `py -3 -m py_compile src\katala_web_research\providers.py src\katala_web_research\feeds.py tests\test_feeds.py tests\test_providers.py tests\test_cli_search.py`
  - Result: passed.
- `git diff --check`
  - Result: passed.

## Boundaries

- No live X/Twitter, Nitter, browser, Camofox, social CLI, account, cookie, session, or profile access.
- No SearXNG, RSSHub, RSS-Bridge, Folo, FreshRSS, Firecrawl, or crawler service deployment.
- No API keys, browser profiles, downloaded private pages, or raw session logs in repo files.
- Optional providers must stay behind environment variables or explicit CLI subcommands.

## Decision

Use `katala-web-research` as the local substitute for search/feed fixture hardening while `x-tweet-fetcher` is not present. Keep X/Twitter-specific saved response work blocked until the target repo exists locally or M5Max access is cleared.
