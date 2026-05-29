# Contributing

Katala Web Research uses a small GitHub Flow:

1. Create a feature branch from `main`.
2. Keep changes scoped to one behavior or documentation slice.
3. Run `make verify`.
4. Push the branch and open a pull request.
5. Wait for CI and review before merging.

Do not commit API keys, cookies, browser profiles, raw session logs, downloaded
private pages, SQLite archives, or runtime outputs.

## Local Setup

```sh
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -e .
make verify
```

This project has no required runtime dependencies. Optional live provider checks
use environment variables from `.env` through 1Password:

```sh
op run --env-file=.env -- make benchmark-live
```

## Common Commands

```sh
make test
make verify
make benchmark
make doctor
make sources
```

## Pull Request Expectations

- Keep deterministic tests offline by default.
- Put reusable design decisions under `docs/`.
- Update `docs/research-quality-benchmark.md` only after running the benchmark
  command that produced it.
- Add or update tests for public CLI/API behavior.
- Explain live-provider checks separately from deterministic gates.
