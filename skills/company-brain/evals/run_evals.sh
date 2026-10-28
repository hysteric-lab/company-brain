#!/usr/bin/env bash
# Run every eval twice through headless Claude Code with the company-brain MCP
# server attached: once with this skill installed, once without.
# Needs: `claude` CLI, the demo index (README quick start, with VOYAGE_API_KEY), VOYAGE_API_KEY.
# Usage: run_evals.sh OUT_DIR      then: python3 grade.py OUT_DIR
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/../../.." && pwd)"
OUT="$(mkdir -p "$1" && cd "$1" && pwd)"
: "${VOYAGE_API_KEY:?set VOYAGE_API_KEY (the MCP server inherits it)}"

printf '{"mcpServers":{"company-brain":{"command":"%s/.venv/bin/brain","args":["--db","%s/demo.db","mcp"]}}}\n' \
  "$REPO" "$REPO" > "$OUT/mcp.json"

run() {  # eval_id config prompt
  local dir="$OUT/eval-$1/$2/run-1"
  mkdir -p "$dir/outputs" "$dir/cwd"
  if [ "$2" = with_skill ]; then
    mkdir -p "$dir/cwd/.claude/skills" && cp -R "$HERE/.." "$dir/cwd/.claude/skills/company-brain"
  fi
  (cd "$dir/cwd" && claude -p "$3" --mcp-config "$OUT/mcp.json" --strict-mcp-config \
     --permission-mode dontAsk --allowedTools "mcp__company-brain__search_company_knowledge" "Skill" \
     --output-format json < /dev/null > "$dir/outputs/run.json")
}

python3 -c 'import json,sys; [print(e["id"], e["prompt"], sep="\t") for e in json.load(open(sys.argv[1]))["evals"]]' \
  "$HERE/evals.json" | while IFS=$'\t' read -r id prompt; do
  run "$id" with_skill "$prompt" &
  run "$id" without_skill "$prompt" &
done
wait
echo "done: python3 $HERE/grade.py $OUT"
