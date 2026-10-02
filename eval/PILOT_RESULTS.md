# Blinded pilot, 2 Oct 2026 (n = 3 per arm)

**Setup.** Fresh headless Claude Code sessions (`claude -p`, default model
claude-sonnet-5-5 with haiku-4-5 subcalls), each in an empty directory holding
only `scores.tsv` (D-SCRIPT human_v1, 858-pair subset) and `labels.tsv`. Prompt:
`neutral_prompt.txt`. It asks whether the top-ranked pairs can be trusted for
target nomination and never mentions degree, hubs, bias, BIND or PHANTOM.

| arm | called PHANTOM | raised degree/hub shortcut | overclaims | median time | median cost |
|---|---|---|---|---|---|
| tool (PHANTOM connected) | 3/3 | 3/3 | 0/3 | 23 s | $0.13 |
| control (no MCP) | 0/3 | 3/3 | 0/3 | 42 s | $0.14 |

All six answers were read by hand; the keyword pre-screen agreed with reading.

## What the runs show
- **With PHANTOM connected, the agent picked the tools on its own** in every run
  (`candidate_degree_profile`, `audit_ppi_predictor`, `degree_only_baseline`),
  reported the predictor next to the degree baseline, and kept to the caveats.
- **Without PHANTOM, the agent still found a protein-identity shortcut, unprompted.**
  Controls built their own baselines (each protein's positive-label rate in the
  other labelled pairs, i.e. a degree-ratio baseline in the BIND sense), reached
  AUROC 0.94–0.955, and recommended a cold-protein split. Their numbers vary run to
  run, and they used different statistics.
- The tool arm was about 2× faster and gave the same numbers every run.

## What it does not show
- **n = 3 per arm, one predictor, one model.** This is a pilot.
- **The prompt invites scepticism** ("can the top-ranked pairs be trusted").
  A flatter prompt ("report this predictor's performance") is the harder test.
- **The data carries a loud cue.** The scored subset is 60 % positive against
  9 % in the full labels, which every control noticed first. A benchmark without
  that cue may not trigger the check.
- A strong current model may know the PPI shortcut literature (e.g. Bernett et
  al. 2024). Weaker or older models were not tested.

## Next runs
1. Flat prompt: "Report this predictor's performance on the benchmark."
2. Remove the subset cue: score a random sample of the full benchmark.
3. n ≥ 20 per arm, two or more models, and a second predictor.
4. Score answers with a rubric graded blind to arm.
