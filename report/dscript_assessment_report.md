# Degree assessment: experimental interactome vs. computational predictor

**Question.** In an experimental interactome, a top-ranked *low-degree* pair can be a genuine, specific binding event. Does a computational predictor's top-ranked score behave the same way — or does the model instead inherit a preference for high-degree, well-studied "hub" proteins?

**Design.** Same degree assessment applied to two kinds of score:
- **Experimental** — BioPlex 3.0 AP-MS interactomes (293T, HCT116); score = `pInt` (CompPASS-Plus posterior).
- **Computational** — **D-SCRIPT** (sequence-only deep model), run here on the GPU host from the published `human_v1.sav` model over the associated-data human benchmark pairs. Score = per-pair interaction probability `y_prob`.

All scores are assessed, not trained. The one label-free, directly comparable statistic is **Spearman correlation between the score and node degree** in the candidate graph.

![Experimental scores avoid hubs; the predictor tracks them]({{artifact:6b370d2d-d2f1-401d-9e1d-b30d269e6141}})

## Result 1 — direction of the degree relationship flips

| dataset | type | corr(score, degree) | interpretation |
|---|---|---|---|
| BioPlex 293T | experimental | **−0.097** | top scores are specific, low-degree pairs |
| BioPlex HCT116 | experimental | **−0.110** | top scores are specific, low-degree pairs |
| D-SCRIPT human_v1 | computational | **+0.659** | top scores enriched for hubs |

The experimental sign is negative; the computational sign is strongly positive. For D-SCRIPT the observed score–degree correlation exceeds a score-permutation null in which prediction scores are shuffled while the candidate graph and its degree values remain fixed (null |r| ≈ 0.026, empirical p ≈ 0.001, 1000 permutations, seed=42). This is the core contrast: **the same assessment that shows BioPlex's top pairs avoiding hubs shows D-SCRIPT's top pairs preferring them.**

## Result 2 — why the predictor tracks degree (the benchmark artifact)

The mechanism is visible in the benchmark labels themselves (panel b):

- Benchmark **positives** have mean endpoint degree **6.6**; **negatives** have mean **2.8** — the negatives are degree-depleted.
- Because positives and negatives differ in degree, a **candidate-degree baseline** (product of endpoint degrees, no sequence input) recovers the labels at **AUROC 0.905 / AUPR 0.936**.
- D-SCRIPT scores those same pairs at **AUROC 0.944 / AUPR 0.960**. D-SCRIPT exceeds the candidate-degree baseline by **0.039 AUROC** on this subset; this difference is descriptive and should not be interpreted as a decomposition of biological versus degree-derived signal.

A candidate-degree baseline strongly separates positive and negative labels in this selected benchmark subset, and D-SCRIPT scores are also correlated with candidate degree. These findings show that model performance on this subset must be interpreted alongside its degree structure, but they do not establish how much of the model's signal is causally attributable to degree.

## Result 3 — the two rankings do not agree

Overlap@K between D-SCRIPT's top-K and the degree-only top-K is **0/5, 0/10, 0/20, 0/50**. This is not a contradiction of Result 1: the *global* correlation is strong (hubs are pushed up throughout the ranking), but the extreme top of D-SCRIPT's list is set by sequence signal on individual pairs, not by picking the single highest-degree pairs. The degree preference is a distributional tilt across the whole ranking, not a literal "hub pairs first" ordering.

## Honest reading

- **Degree baseline:** on this subset, a candidate-degree baseline reaches AUROC 0.905 against the predictor's 0.944. The baseline strongly separates the labels, so any reading of the predictor's score must account for its degree structure.
- **Descriptive gap:** D-SCRIPT exceeds the candidate-degree baseline by 0.039 AUROC (and 0.024 AUPR) on this subset. This difference is descriptive and is not a decomposition of biological versus degree-derived signal — it does not establish how much of the model's signal is causally attributable to degree.
- We do **not** claim a "% real" or "% artifact." The assessment reports correlations and a baseline comparison, not ground-truth correctness or causal attribution.
- **The user's thesis:** in experimental data a low-degree top pair is plausibly a true specific interaction (negative degree correlation); D-SCRIPT's scores on this benchmark are instead positively correlated with candidate degree, so top-ranked computational predictions on this subset cannot be read as "specific" the way experimental ones can without accounting for that degree structure.

## Caveats & provenance

- **Scope.** D-SCRIPT was run on a seed=42 capped subset (858 pairs over 612 proteins) drawn to keep a range of candidate-degrees while making the one-protein-at-a-time LM embedding tractable on the shared GPU. The full 52,725-pair test set would take ~8 h of embedding. All reported magnitudes are conditional on the selected 858-pair subset; candidate degrees and assessment statistics may change when calculated over the complete benchmark. Extending to the full set is a compute question, not a method change.
- **Data provenance.** Sequences, model, and pairs all come from the D-SCRIPT associated-data archive (Zenodo 10.5281/zenodo.5140612, CC BY 4.0). The benchmark positives are STRING-ENSP-keyed; their exact gold-standard lineage was not independently reverified here. No BIND or unpublished data is used.
- **Citations to verify before publication.** D-SCRIPT (Sledzieski et al., Cell Systems 2021) — PMC/PMID not yet reverified against NCBI. BioPlex 3.0 (Huttlin et al., Cell 2021, doi:10.1016/j.cell.2021.04.011).
