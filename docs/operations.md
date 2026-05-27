# Operations

This is the day-to-day operating surface for `katala-web-research`.

## Normal Research Cycle

Use the wrapper script when you want the standard flow:

```sh
scripts/kwr-research-cycle.sh "OpenAI Agents SDK handoffs"
```

It performs:

1. incremental scan of `/Users/s30519/Documents/GitHub`
2. web search
3. local repository evidence lookup
4. selected page capture
5. SQLite archive write
6. Markdown investigation report

Defaults:

- archive: `~/.kwr/research.sqlite`
- report: `reports/<query-slug>.md`
- provider: `ddg`
- reader: `auto`
- web results: 8
- repo hits: 6
- captured pages: 2

## Useful Overrides

```sh
KWR_MAX_REPOS=50 KWR_MAX_FILES=20 \
scripts/kwr-research-cycle.sh "browser automation research" reports/browser-automation.md
```

```sh
KWR_PROVIDER=github KWR_READ_TOP=0 \
scripts/kwr-research-cycle.sh "agent research tools"
```

## Token Budget Benchmark

Run the deterministic local benchmark:

```sh
scripts/benchmark-token-budget.py
```

Run against the real `Documents/GitHub` corpus:

```sh
scripts/benchmark-token-budget.py --root /Users/s30519/Documents/GitHub
```

Run the optional live web benchmark:

```sh
scripts/benchmark-token-budget.py --root /Users/s30519/Documents/GitHub --live-web
```

The benchmark estimates tokens from emitted text and generated reports. It fails when output exceeds the defined budget. This is a practical guard against accidentally dumping full captured pages or huge JSON payloads into agent context.

## Output Discipline

- Prefer `--out <file>` for `brief` and `investigate`; stdout stays short.
- Keep `--read-top` small, usually `1-3`.
- Use `kwr query` for follow-up retrieval instead of re-running large web captures.
- Use `kwr repos scan` incrementally before important research.
- Use `--json` only for automation that will consume structured output; JSON can include larger payloads.

## Verification

```sh
scripts/verify.sh
scripts/benchmark-token-budget.py
```

