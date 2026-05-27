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
```

Run the MCP stdio server:

```sh
kwr mcp
```

## Provider Posture

Default providers avoid secrets:

- `ddg`: DuckDuckGo HTML endpoint for general web search
- `github`: GitHub REST search or `gh search repos` when the GitHub CLI is available
- `jina-reader`: clean URL reading through `https://r.jina.ai/`
- `direct`: direct HTTP fetch with a conservative text extractor

Optional providers use environment variables only:

- `JINA_API_KEY` for Jina search
- `GITHUB_TOKEN` for higher GitHub REST API limits
- `KWR_SEARXNG_URL` for a private SearXNG instance with JSON enabled
- `BRAVE_SEARCH_API_KEY` for Brave Web Search API

The CLI never writes those values into archives, reports, logs, or config files.

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

The verifier compiles the package, runs unit tests, and checks that common raw/runtime artifacts are not tracked.

Completion evidence is tracked in [docs/completion-audit.md](docs/completion-audit.md).

## Documentation Map

- [docs/search-capability.md](docs/search-capability.md): how search quality is improved.
- [docs/research-flow.md](docs/research-flow.md): research workflow and flowchart.
- [docs/operations.md](docs/operations.md): routine operation and token-budget benchmarks.
- [docs/rl-and-evaluation.md](docs/rl-and-evaluation.md): reinforcement-learning path and reward design.
- [docs/research-quality-benchmark.md](docs/research-quality-benchmark.md): benchmark log.
- [docs/design.md](docs/design.md): architecture and contracts.
- [docs/source-evidence.md](docs/source-evidence.md): source evidence and implementation decisions.
- [docs/mcp-config-examples.md](docs/mcp-config-examples.md): MCP client configuration examples.
- [docs/github-management.md](docs/github-management.md): GitHub publication and routine operation.
- [docs/completion-audit.md](docs/completion-audit.md): completion evidence.
