# GitHub Management

This project is ready to manage as a standalone GitHub repository.

## Suggested First Publication

```sh
cd katala-web-research
git init
git add .
git status --short
scripts/verify.sh
git commit -m "Create local-first web research toolkit"
gh repo create katala-web-research --private --source . --remote origin --push
```

Only run the commands above when repository creation, commit, and push are intended.

## Routine Checks

```sh
scripts/verify.sh
PYTHONPATH=src python3 -m katala_web_research.cli doctor
```

MCP client examples live in `docs/mcp-config-examples.md`.
Completion evidence lives in `docs/completion-audit.md`.

## Corpus Bootstrap

```sh
PYTHONPATH=src python3 -m katala_web_research.cli repos scan \
  ~/Documents/GitHub \
  --archive ~/.kwr/research.sqlite \
  --max-repos 200 \
  --max-files-per-repo 40

PYTHONPATH=src python3 -m katala_web_research.cli brief \
  "web research provider architecture" \
  --archive ~/.kwr/research.sqlite \
  --out reports/web-research-provider.md
```

The archive and reports are local runtime outputs. Keep SQLite files and generated raw evidence out of Git unless intentionally curating a small Markdown report.

Subsequent `repos scan` runs are incremental by default. Use `--no-incremental` only when you intentionally want to re-read all selected candidate files.
