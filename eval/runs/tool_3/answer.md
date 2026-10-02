**Short answer: not on this evidence.** The predictor ranks the benchmark pairs well. But that ranking is partly driven by how often a protein appears in the candidate pairs, and the test data can't show it will work for nominating targets.

**What I found**

- **Ranking looks very good on the scored set.** AUROC is 0.944 and AUPR is 0.960 on 858 scored pairs, and 99–100% of the top 100 are labelled positive. This is the part that looks trustworthy.
- **Scores track protein degree (how many candidate pairs a protein appears in).**
  - The Spearman correlation between score and degree product is +0.66, against a permutation null of about 0.03 (p ≈ 0.001).
  - Positive pairs have mean endpoint degree 6.6 versus 2.8 for negatives.
  - Top-ranked pairs are therefore enriched for hub proteins.
- **Degree alone nearly matches the predictor.** A baseline with no biology, using only degree, reaches AUROC 0.905, so the predictor adds only about 0.04. That gap is descriptive. It is not a measure of "real" signal, and I'm not claiming the model only learns degree.
- **Within degree strata the predictor does add something.** AUROC is about 0.88–0.93 inside each degree quartile, using degrees from the full label file. The model is not purely a hub detector, but hub enrichment is still a real effect.
- **The scored set is unrepresentative of the benchmark.**
  - `labels.tsv` has 52,725 pairs at 9% positive. `scores.tsv` has only 858 pairs at 60% positive.
  - The scored pairs were evidently selected, and I don't know how. This is the largest caveat. The headline numbers, and the top-100 precision, apply to this enriched subset, not to the benchmark.
  - I could not evaluate the predictor on the other ~51,900 labelled pairs, so I have no result for realistic prevalence.
  - Degree is computed on the 858-pair subgraph, so those degree figures depend on the subset.

**Why this matters for drug targets**

Hubs and well-studied proteins are over-represented among known interactions. A ranking that favours them will push already-known, often non-druggable or promiscuous hubs to the top. Those are the least novel nominations.

Top-100 precision of 99% is also an artefact of the enrichment. At 9% prevalence the same ranking would have far lower precision.

**Recommendations before using it**

1. Score a random or representative sample of `labels.tsv`, or all of it, and re-evaluate. Report precision at K at realistic prevalence, and report it next to the degree-only baseline.
2. Find out how the 858 pairs were chosen.
3. Rank within degree strata, or downweight hubs, and check whether the nominated pairs survive.
4. Treat the top-ranked pairs as hypotheses for experimental validation, not as confirmed interactions. Even a true interaction isn't evidence that the protein is a good drug target.

I made no claim about the share of the signal that is "artefact" or "real", and the results cover this 858-pair subset only.
