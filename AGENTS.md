# katala-web-research

@/Users/s30519/work/agent-context/AGENTS.MD

## Project Delta

- This repository is a local-first web research access toolkit.
- Do not store API keys, cookies, browser profiles, raw session logs, or downloaded private pages in the repo.
- Networked commands are opt-in through CLI subcommands such as `search`, `read`, and `collect`.
- Persisted research state belongs in the user-selected SQLite archive path, not in tracked source files.
- Keep provider integrations small and replaceable. Prefer official APIs or stable public endpoints over page-shape scraping.

## Verification

Run:

```sh
scripts/verify.sh
```

