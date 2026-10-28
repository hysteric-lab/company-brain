#!/usr/bin/env bash
# Download a fixed slice of GitLab's public handbook into demo/corpus/.
# Fetched at run time, not vendored: see README "Demo corpus" for source and licence.
set -euo pipefail

# Pinned to one handbook commit so the line numbers quoted in README stay valid.
REV="129243bcffcf6cbc8c2e83f537f1836b99900a61"  # main on 2026-10-28
BASE="https://gitlab.com/gitlab-com/content-sites/handbook/-/raw/$REV/content/handbook"
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
