"""Print the final answer from a Claude Code stream-json transcript."""
import json
import sys

final = ""
for line in open(sys.argv[1]):
    line = line.strip()
    if not line:
        continue
    try:
        ev = json.loads(line)
    except json.JSONDecodeError:
        continue
    if ev.get("type") == "result":
        final = ev.get("result", "") or final
print(final)
