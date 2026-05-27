#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

usage() {
  cat <<'USAGE'
Usage:
  scripts/kwr-research-cycle.sh "research query" [out.md]

Environment:
  KWR_ARCHIVE         SQLite archive path. Default: ~/.kwr/research.sqlite
  KWR_REPO_ROOT       Local repository corpus root. Default: /Users/s30519/Documents/GitHub
  KWR_MAX_REPOS       Bounded repo scan count. Default: 200
  KWR_MAX_FILES       Files per repo. Default: 40
  KWR_WEB_LIMIT       Web search result count. Default: 8
  KWR_REPO_LIMIT      Local repo result count. Default: 6
  KWR_READ_TOP        Number of top web pages to capture. Default: 2
  KWR_PROVIDER        Search provider. Default: ddg
  KWR_READER          Reader. Default: auto

This script refreshes the local corpus incrementally and writes a Markdown
investigation report. It does not commit, push, or store secrets.
USAGE
}

if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ] || [ "$#" -lt 1 ]; then
  usage
  exit 0
fi

query="$1"
archive="${KWR_ARCHIVE:-$HOME/.kwr/research.sqlite}"
repo_root="${KWR_REPO_ROOT:-/Users/s30519/Documents/GitHub}"
max_repos="${KWR_MAX_REPOS:-200}"
max_files="${KWR_MAX_FILES:-40}"
web_limit="${KWR_WEB_LIMIT:-8}"
repo_limit="${KWR_REPO_LIMIT:-6}"
read_top="${KWR_READ_TOP:-2}"
provider="${KWR_PROVIDER:-ddg}"
reader="${KWR_READER:-auto}"

if [ "$#" -ge 2 ]; then
  out="$2"
else
  slug="$(printf '%s' "$query" | tr '[:upper:]' '[:lower:]' | tr -cs 'a-z0-9' '-' | sed 's/^-//;s/-$//' | cut -c1-80)"
  mkdir -p reports
  out="reports/${slug:-investigation}.md"
fi

mkdir -p "$(dirname "$archive")" "$(dirname "$out")"

echo "== refresh local corpus =="
PYTHONPATH=src python3 -m katala_web_research.cli repos scan "$repo_root" \
  --archive "$archive" \
  --max-repos "$max_repos" \
  --max-files-per-repo "$max_files"

echo "== investigate =="
PYTHONPATH=src python3 -m katala_web_research.cli investigate "$query" \
  --archive "$archive" \
  --provider "$provider" \
  --reader "$reader" \
  --web-limit "$web_limit" \
  --repo-limit "$repo_limit" \
  --read-top "$read_top" \
  --out "$out"

echo "archive: $archive"
echo "report: $out"

