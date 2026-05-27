#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "== compile =="
PYTHONPATH=src python3 -m compileall -q src tests

echo "== unit tests =="
PYTHONPATH=src python3 -m unittest discover -s tests

echo "== cli smoke =="
PYTHONPATH=src python3 -m katala_web_research.cli doctor >/tmp/katala-web-research-doctor.txt
grep -q "sqlite_fts5: ok" /tmp/katala-web-research-doctor.txt
rm -f /tmp/katala-web-research-doctor.txt

echo "== token budget benchmark =="
scripts/benchmark-token-budget.py

echo "== tracked artifact guard =="
if git rev-parse --show-toplevel >/dev/null 2>&1; then
  tracked_sensitive="$(git ls-files -- . | grep -E '(^|/)(raw|downloads|sessions|logs?)/|\.env($|\.)|\.jsonl$|\.sqlite(-shm|-wal)?$|\.log$|__pycache__|\.pyc|\.DS_Store' | grep -vE '(^|/)\.env\.example$' || true)"
  if [ -n "$tracked_sensitive" ]; then
    echo "Refusing: tracked raw/runtime/sensitive artifact found" >&2
    echo "$tracked_sensitive" >&2
    exit 1
  fi
fi

echo "katala-web-research verification passed"
