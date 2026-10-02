#!/usr/bin/env bash
# Blinded agent test: does Claude Code check for degree bias when nobody asks?
#
# Each run is a fresh headless Claude Code session in an empty directory that holds
# only the two data files under neutral names. The prompt never mentions degree,
# hubs, bias, BIND or PHANTOM.
#   arm "tool"    : PHANTOM MCP server connected (not mentioned in the prompt)
#   arm "control" : no MCP servers
#
# Usage: eval/run_blinded.sh <n_runs_per_arm> [model]
# Output: eval/runs/<arm>_<i>/  (transcript.json, answer.md)
set -euo pipefail
N=${1:-3}
MODEL=${2:-}
REPO=$(cd "$(dirname "$0")/.." && pwd)
PY=$(command -v python3)
PROMPT=$(cat "$REPO/eval/neutral_prompt.txt")
OUT="$REPO/eval/runs"
mkdir -p "$OUT"

cat > "$OUT/phantom_mcp.json" <<EOF
{"mcpServers":{"phantom":{"command":"$PY","args":["-m","phantom_audit.server"],"cwd":"$REPO",
 "env":{"PYTHONPATH":"$REPO"}}}}
EOF
echo '{"mcpServers":{}}' > "$OUT/empty_mcp.json"

run_one () {
  local arm=$1 i=$2 cfg=$3
  local d; d=$(mktemp -d)
  cp "$REPO/data/dscript_human_v1_subset_yprob.tsv" "$d/scores.tsv"
  cp "$REPO/data/human_test_labeled.tsv" "$d/labels.tsv"
  local rd="$OUT/${arm}_${i}"; mkdir -p "$rd"
  ( cd "$d" && claude -p "$PROMPT" ${MODEL:+--model "$MODEL"} \
      --mcp-config "$cfg" --strict-mcp-config \
      --dangerously-skip-permissions --output-format stream-json --verbose \
      > "$rd/transcript.json" 2> "$rd/stderr.txt" ) || true
  python3 "$REPO/eval/extract_answer.py" "$rd/transcript.json" > "$rd/answer.md" || true
  rm -rf "$d"
}

for i in $(seq 1 "$N"); do
  run_one tool "$i" "$OUT/phantom_mcp.json" &
  run_one control "$i" "$OUT/empty_mcp.json" &
done
wait
python3 "$REPO/eval/score_runs.py" "$OUT"
