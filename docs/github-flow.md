# GitHub Flow

This repository uses PR-based GitHub Flow.

## Branches

- `main`: protected integration branch.
- `feature/<topic>`: feature, benchmark, provider, and documentation work.
- `fix/<topic>`: bug fixes.
- `chore/<topic>`: maintenance-only changes.

Do not push working changes directly to `main`. Push a branch and open a pull
request.

## Required Local Gate

Run:

```sh
make verify
```

This covers compile, unit tests, CLI smoke tests, feed fixture smoke, token
budget benchmark, deterministic research-quality benchmark, and tracked artifact
guards.

Optional live gate:

```sh
op run --env-file=.env -- make benchmark-live
```

Live benchmark output is evidence, not the default CI gate, because API keys,
network state, and external indices can drift.

## PR Shape

Use this structure:

- Summary: what changed.
- Verification: exact commands and outcomes.
- Risk: external services, licensing, data handling, or benchmark drift.
- Follow-up: concrete next slice if work remains.

## Merge Rule

Merge after:

- local `make verify` passes,
- GitHub Actions pass,
- review concerns are resolved,
- no secrets or runtime artifacts are included.

Use squash merge for normal feature branches and delete the branch after merge.
