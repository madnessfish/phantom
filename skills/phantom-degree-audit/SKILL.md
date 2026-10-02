---
name: phantom-degree-audit
description: Audit a protein-protein interaction (PPI) predictor or PPI target ranking for degree bias using the PHANTOM MCP tools. Use whenever you evaluate, benchmark, compare, or rank targets with a PPI predictor (D-SCRIPT, AlphaFold-Multimer scores, PIPR, Topsy-Turvy, STRING scores, AP-MS scores), even if nobody mentions bias.
---

# PHANTOM degree-bias audit

A PPI score is only useful for target nomination if it reflects specific binding,
not how often a protein appears among the candidate pairs. Benchmarks with randomly
sampled negatives give hubs high degree among positives, so a model can score well
by ranking hubs. PHANTOM measures how much of a ranking survives a degree control.

## When to run it
Any time a PPI predictor's scores are evaluated or used to rank targets. Run it
before reporting AUROC/AUPR, and before calling top-ranked pairs "specific".

## Steps
1. `candidate_degree_profile(scores_path)`: does the candidate graph have hubs?
2. `audit_ppi_predictor(scores_path, labels_path, predictor_name, out_dir)`:
   score-degree Spearman with a permutation null, degree-only AUROC baseline,
   top-K overlap, top hubs, and a verdict.
3. Read the `phantom://interpretation-rules` resource.
4. Report: the numbers, the verdict findings, the caveats verbatim, and what the
   audit cannot tell you.

## Input format
3-column TSV (or CSV by extension), header optional:
`prot1  prot2  score` and, for labels, `prot1  prot2  label(0/1)`.
`NA` scores are dropped. Labels are matched order-independently.

## Reporting rules
- Report the predictor AUROC next to the degree-only AUROC, never alone.
- The AUROC difference is descriptive. Never call it "biological signal".
- Never state a "% artifact" or "% real", or that a model "only learns degree".
- State that degrees are computed on the supplied subset.

## Test run
`demo_paths()` returns the bundled D-SCRIPT human_v1 subset (858 pairs).
Expected: Spearman +0.6594, predictor AUROC 0.9439, degree-only AUROC 0.9054.
