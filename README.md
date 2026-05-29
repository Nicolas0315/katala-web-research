# katala-web-research

`katala-web-research` is a local-first CLI for research and investigation workflows:

- search across no-key and optional provider backends
- read URLs into clean text or Markdown-like snapshots
- collect top results into a SQLite archive with FTS5 search
- produce a small evidence report that is easy to commit, review, or hand off

It borrows the useful shape from local-first research and crawler patterns:

- `Agent-Reach`: small channel/provider contracts and Jina Reader as a clean web reader
- `x-tweet-fetcher`: no-key search fallback thinking and browser-free first pass
- `supacrawl`: local SQLite archive plus fast search
- `agent-research`: source evidence and verification discipline

`~/Documents/GitHub` is supported through `kwr repos scan`; start with bounded scans before indexing the full corpus.

## Install For Local Development

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
scripts/verify.sh
```

## Commands

Search the web with a no-key default provider:

```sh
kwr search "agent web research tools" --limit 5
kwr search "agent web research tools" --provider meta --limit 8
kwr search "agent web research tools" --provider meta --json
```

Read a URL:

```sh
kwr read https://example.com --json
```

Search, read the top pages, store them in a local archive, and write an evidence report:

```sh
kwr collect "OpenAI Agents SDK handoffs" --limit 8 --read-top 3 --report reports/agents-sdk-handoffs.md
```

Search the local archive:

```sh
kwr query "handoff"
```

Register and query RSS, Atom, or JSON Feed sources in the local archive:

```sh
kwr feeds add https://example.com/feed.xml --archive ~/.kwr/research.sqlite
kwr feeds refresh --archive ~/.kwr/research.sqlite
kwr feeds query "agent research" --archive ~/.kwr/research.sqlite
kwr search "agent research" --provider feed --archive ~/.kwr/research.sqlite
```

Inspect domain-specific trusted source and bias metadata:

```sh
kwr sources list --domain security --json
kwr sources list --domain news --query-type media_bias
kwr sources match https://www.cisa.gov/known-exploited-vulnerabilities-catalog --json
```

Plan a bounded research search before fetching pages:

```sh
kwr plan "agentic retrieval source quality" --year 2026
```

Index local Git repositories into the same archive:

```sh
kwr repos scan ~/Documents/GitHub --archive ~/.kwr/research.sqlite
kwr repos query "web research provider" --archive ~/.kwr/research.sqlite
```

Build a combined brief from web search plus the indexed local corpus:

```sh
kwr brief "web research provider architecture" --archive ~/.kwr/research.sqlite --out reports/web-research-provider.md
kwr brief "web research provider architecture" --expand-queries --archive ~/.kwr/research.sqlite --out reports/web-research-provider.md
```

Run a full investigation pass: web search, local repo lookup, selected page capture, archive, and report:

```sh
kwr investigate "web research provider architecture" --archive ~/.kwr/research.sqlite --out reports/web-research-provider-investigation.md
kwr investigate "web research provider architecture" --expand-queries --archive ~/.kwr/research.sqlite --out reports/web-research-provider-investigation.md
```

Check provider availability:

```sh
kwr doctor
```

Run deterministic research-quality evaluation:

```sh
kwr eval --out reports/research-quality.md
scripts/benchmark-research-quality.py --iterations 30 --out reports/research-quality-benchmark.md
```

Run the MCP stdio server:

```sh
kwr mcp
```

## Provider Posture

Default providers avoid secrets:

- `ddg`: DuckDuckGo HTML endpoint for general web search
- `feed`: local RSS/Atom/JSON Feed archive search
- `github`: GitHub REST search or `gh search repos` when the GitHub CLI is available
- `jina-reader`: clean URL reading through `https://r.jina.ai/`
- `direct`: direct HTTP fetch with a conservative text extractor

Optional providers use environment variables only:

- `JINA_API_KEY` for Jina search
- `GITHUB_TOKEN` for higher GitHub REST API limits
- `KWR_SEARXNG_URL` for a private SearXNG instance with JSON enabled
- `BRAVE_SEARCH_API_KEY` for Brave Web Search API
- `OPENALEX_API_KEY` for OpenAlex scholarly works search
- `KWR_META_PROFILE` for metasearch profiles: `broad`, `docs`, `scholarly`, `code`, `fresh`, `local`
- `KWR_META_PROVIDERS` to override profile providers, for example `ddg,github,openalex,searxng`
- `KWR_SEARXNG_CATEGORIES`, `KWR_SEARXNG_ENGINES`, `KWR_SEARXNG_LANGUAGE`, `KWR_SEARXNG_TIME_RANGE`, `KWR_SEARXNG_SAFESEARCH` for SearXNG API pass-through

The CLI never writes those values into archives, reports, logs, or config files.

`meta` search records per-engine run health in result metadata: status, latency, result count, health score, and error kind. It uses that health score in Reciprocal Rank Fusion so a slow or failing engine is observable and cannot dominate consensus ranking.

## Local Repository Corpus

`kwr repos scan` indexes README, AGENTS, Skill files, project manifests, and small text docs from Git repositories under a root path. It skips `.git`, `node_modules`, caches, raw downloads, logs, sessions, build outputs, and vendored directories.

The command is designed for a local repository corpus such as `~/Documents/GitHub`, but also works with any readable repository folder. If macOS blocks that folder with TCC permissions, grant terminal access and rerun the same command; no code change is needed.

## Research Briefs

`kwr brief` ranks web candidates by source quality heuristics and places local repository evidence next to them. Official docs and primary sources are surfaced before ordinary web pages, then the operator can use `kwr collect` to archive full pages for the final evidence trail.

## MCP Tools

The stdio server exposes:

- `kwr.plan`
- `kwr.search`
- `kwr.read`
- `kwr.query`
- `kwr.repos_query`
- `kwr.brief`
- `kwr.investigate`

It follows the MCP tool discovery and invocation surface: `initialize`, `tools/list`, and `tools/call`.

See [docs/mcp-config-examples.md](docs/mcp-config-examples.md) for client config examples.

## Verification

```sh
scripts/verify.sh
```

Developer shortcut:

```sh
make verify
```

The verifier compiles the package, runs unit tests, and checks that common raw/runtime artifacts are not tracked.

Completion evidence is tracked in [docs/completion-audit.md](docs/completion-audit.md).

GitHub Flow and contribution expectations are documented in
[docs/github-flow.md](docs/github-flow.md) and [CONTRIBUTING.md](CONTRIBUTING.md).

## Documentation Map

- [docs/search-capability.md](docs/search-capability.md): how search quality is improved.
- [docs/research-flow.md](docs/research-flow.md): research workflow and flowchart.
- [docs/operations.md](docs/operations.md): routine operation and token-budget benchmarks.
- [docs/rl-and-evaluation.md](docs/rl-and-evaluation.md): reinforcement-learning path and reward design.
- [docs/research-quality-benchmark.md](docs/research-quality-benchmark.md): benchmark log.
- [docs/domain-validation-benchmark-plan-2026-05-28.md](docs/domain-validation-benchmark-plan-2026-05-28.md): adoption, implementation, and domain-category benchmark design.
- [docs/trusted-source-registry-2026-05-29.md](docs/trusted-source-registry-2026-05-29.md): domain-specific trusted source and bias metadata registry.
- [docs/metasearch-engine-design.md](docs/metasearch-engine-design.md): SearXNG-inspired Katala metasearch design.
- [docs/metasearch-enhancement-research-2026-05-27.md](docs/metasearch-enhancement-research-2026-05-27.md): next OSS techniques to strengthen metasearch.
- [docs/metasearch-implementation-plan-2026-05-27.md](docs/metasearch-implementation-plan-2026-05-27.md): implementation plan and verification boundary.
- [docs/feed-provider-implementation-plan-2026-05-28.md](docs/feed-provider-implementation-plan-2026-05-28.md): RSS/Atom/JSON Feed provider implementation plan.
- [docs/design.md](docs/design.md): architecture and contracts.
- [docs/source-evidence.md](docs/source-evidence.md): source evidence and implementation decisions.
- [docs/mcp-config-examples.md](docs/mcp-config-examples.md): MCP client configuration examples.
- [docs/github-management.md](docs/github-management.md): GitHub publication and routine operation.
- [docs/github-flow.md](docs/github-flow.md): branch, PR, verification, and merge flow.
- [docs/completion-audit.md](docs/completion-audit.md): completion evidence.
