"""Score blinded runs.

For each run, records:
  called_phantom   : did the agent call any mcp__phantom__ tool?
  computed_degree  : did its own code/tool calls compute per-protein degree/counts?
  flagged_in_answer: does the final answer raise degree/hub/well-studied bias?

Keyword scoring is a pre-screen only. Read answer.md for every run before
reporting a number; the keyword list is in FLAG_TERMS.
"""
import json
import re
import sys
from pathlib import Path

FLAG_TERMS = re.compile(r"\b(degree|hubs?|hub protein|node degree|promiscu\w*|frequent[- ]flyer|"
                        r"well[- ]studied|preferential attachment|study bias|shortcut)\b", re.I)
DEGREE_CODE = re.compile(r"(degree|value_counts|Counter\(|groupby\(.{0,40}size|\.degree\()", re.I)


def score(run_dir: Path) -> dict:
    called, computed = False, False
    for line in (run_dir / "transcript.json").read_text().splitlines():
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if ev.get("type") != "assistant":
            continue
        for block in ev.get("message", {}).get("content", []):
            if block.get("type") != "tool_use":
                continue
            name = block.get("name", "")
            if name.startswith("mcp__phantom__"):
                called = True
            if DEGREE_CODE.search(json.dumps(block.get("input", {}))):
                computed = True
    answer = (run_dir / "answer.md").read_text() if (run_dir / "answer.md").exists() else ""
    hits = sorted({m.group(0).lower() for m in FLAG_TERMS.finditer(answer)})
    return dict(run=run_dir.name, called_phantom=called, computed_degree=computed,
                flagged_in_answer=bool(hits), terms=hits, answer_chars=len(answer))


if __name__ == "__main__":
    root = Path(sys.argv[1])
    rows = [score(d) for d in sorted(root.iterdir()) if d.is_dir()]
    for r in rows:
        print(json.dumps(r))
    (root / "scores.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    for arm in ("tool", "control"):
        a = [r for r in rows if r["run"].startswith(arm + "_")]
        if a:
            print(f"{arm}: n={len(a)}  called_phantom={sum(r['called_phantom'] for r in a)}  "
                  f"computed_degree={sum(r['computed_degree'] for r in a)}  "
                  f"flagged_in_answer={sum(r['flagged_in_answer'] for r in a)}")
