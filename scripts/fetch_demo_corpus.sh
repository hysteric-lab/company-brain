#!/usr/bin/env bash
# Download a fixed slice of GitLab's public handbook into demo/corpus/.
# Fetched at run time, not vendored: see README "Demo corpus" for source and licence.
set -euo pipefail

BASE="https://gitlab.com/gitlab-com/content-sites/handbook/-/raw/main/content/handbook"
PAGES=(
  "values/_index.md"
  "communication/_index.md"
  "people-group/time-off-and-absence/time-off-types.md"
  "finance/expenses.md"
)
OUT="$(cd "$(dirname "$0")/.." && pwd)/demo/corpus"

for page in "${PAGES[@]}"; do
  mkdir -p "$OUT/$(dirname "$page")"
  curl -fsS "$BASE/$page" -o "$OUT/$page"
  echo "fetched $page"
done
