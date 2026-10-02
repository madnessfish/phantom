# PHANTOM as an agent

PHANTOM ships an MCP server. Connecting it to an LLM agent (Claude Code or
Claude Science) gives you a PHANTOM agent: you ask in plain English, and the
agent decides which audit tools to call, runs them, and writes the report. This
is the same construction as Paper2Agent (Miao et al., *Nature* 2026): validated
paper code exposed as MCP tools, driven by an off-the-shelf agent.

```
you ──"is this PPI predictor safe for target nomination?"──▶ Claude Code / Claude Science
                                                              │ chooses tools
                                                              ▼
                                         PHANTOM MCP server (phantom_audit/server.py)
                                         ├─ candidate_degree_profile
                                         ├─ score_degree_correlation
                                         ├─ degree_only_baseline
                                         ├─ audit_ppi_predictor
                                         ├─ resources: README, report, interpretation rules
                                         └─ prompt: audit_ppi_predictor_workflow
```

## Install

```bash
git clone https://github.com/madnessfish/phantom && cd phantom
pip install -e ".[test]"
python -m pytest tests -q        # 5 tests; reproduces results/ exactly via the MCP protocol
```

## Claude Code

The repo's `.mcp.json` registers the server for anyone who opens Claude Code in
this folder. To use it from any folder:

```bash
claude mcp add phantom -- phantom-mcp
```

Optional: copy `skills/phantom-degree-audit/` into `~/.claude/skills/` so the
agent knows when to reach for the audit.

## Claude Science

Claude Science takes MCP connectors in the standard client format and skills as
folders containing a `SKILL.md`.

1. Add an MCP connector with command `phantom-mcp` (or
   `python -m phantom_audit.server` with the repo as working directory).
2. Add `skills/phantom-degree-audit/` as a skill.

Both persist across sessions.

## Try it

> Audit the predictor in demo_paths for degree bias and write a short report.

Expected numbers: Spearman(score, degree) +0.6594, predictor AUROC 0.9439,
degree-only AUROC 0.9054.

## What the agent does and does not do

- It runs the audit when the tools are connected and the task involves a PPI
  predictor. Whether it does so **without being told** is measured, not assumed:
  see `eval/` for the blinded test.
- Interpretation is constrained: every result carries fixed caveats and a
  `do_not_claim` list (no "% artifact", no "the model only learns degree").
- Scope: PPI scores on a candidate pair set. For paired-input binding predictors
  in general (pHLA, TCR-epitope, drug-target), the BIND degree-ratio audit applies.

## Blinded evaluation

`eval/run_blinded.sh N` runs N fresh headless Claude Code sessions per arm with a
neutral prompt that never mentions degree, hubs or bias:

- `tool`: PHANTOM server connected
- `control`: no MCP servers

`eval/score_runs.py` records, per run, whether the agent called PHANTOM, computed
degree in its own code, and raised degree/hub bias in its answer. Keyword
scoring is a pre-screen; read each `answer.md` before reporting.
