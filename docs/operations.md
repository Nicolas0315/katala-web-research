# Operations

This is the day-to-day operating surface for `katala-web-research`.

## Normal Research Cycle

Use the wrapper script when you want the standard flow:

```sh
scripts/kwr-research-cycle.sh "OpenAI Agents SDK handoffs"
```

It performs:

1. incremental scan of `~/Documents/GitHub`
2. bounded query decomposition
3. web search
4. local repository evidence lookup
5. selected page capture
6. SQLite archive write
7. Markdown investigation report

Defaults:

- archive: `~/.kwr/research.sqlite`
- report: `reports/<query-slug>.md`
- provider: `ddg`
- reader: `auto`
- web results: 8
- repo hits: 6
- captured pages: 2
- expanded queries: enabled

## Useful Overrides

```sh
KWR_MAX_REPOS=50 KWR_MAX_FILES=20 \
scripts/kwr-research-cycle.sh "browser automation research" reports/browser-automation.md
```

```sh
KWR_PROVIDER=github KWR_READ_TOP=0 \
scripts/kwr-research-cycle.sh "agent research tools"
```

Run local metasearch across configured engines:

```sh
KWR_PROVIDER=meta KWR_META_PROVIDERS=ddg,github,openalex \
op run --env-file=.env -- scripts/kwr-research-cycle.sh "research agent evaluation metrics"
```

Disable query decomposition when you need a single exact query:

```sh
KWR_EXPAND_QUERIES=0 scripts/kwr-research-cycle.sh "exact release title"
```

## Token Budget Benchmark

Run the deterministic local benchmark:

```sh
scripts/benchmark-token-budget.py
```

Run against the real `Documents/GitHub` corpus:

```sh
scripts/benchmark-token-budget.py --root ~/Documents/GitHub
```

Run the optional live web benchmark:

```sh
scripts/benchmark-token-budget.py --root ~/Documents/GitHub --live-web
```

The benchmark estimates tokens from emitted text and generated reports. It fails when output exceeds the defined budget. This is a practical guard against accidentally dumping full captured pages or huge JSON payloads into agent context.

## Output Discipline

- Prefer `--out <file>` for `brief` and `investigate`; stdout stays short.
- Use `kwr plan` before expensive investigations when you want to inspect the fan-out.
- Keep `--read-top` small, usually `1-3`.
- Use `kwr query` for follow-up retrieval instead of re-running large web captures.
- Use `kwr repos scan` incrementally before important research.
- Use `--json` only for automation that will consume structured output; JSON can include larger payloads.

## Verification

```sh
scripts/verify.sh
scripts/benchmark-token-budget.py
PYTHONPATH=src python3 -m katala_web_research.cli eval --out /tmp/kwr-eval.md
```
