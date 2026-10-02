**Short answer: no, not on this evidence. The top-ranked pairs look excellent on the benchmark, but that mostly shows the benchmark is easy, not that the predictor has found real biology.**

**What I measured**

On the 858 scored pairs, which all match labeled pairs:

| Measure | Result |
|---|---|
| AUROC | 0.944 |
| Average precision | 0.960 |
| Precision in top 10, 25 and 50 | 100% |
| Precision in top 100 | 99% |
| Precision in top 400 | 97% |

Taken at face value, that is a strong result.

**Why I don't trust it for target nomination**

1. **The predictor is no better than a protein-identity shortcut.**
   - I scored each pair by how often its two proteins appear as positives in the other labels, leaving the pair itself out. This uses no biology.
   - That shortcut gets AUROC 0.955 on the same pairs, slightly above the predictor's 0.944. On all 52,725 labeled pairs it gets 0.915.
   - The predictor's scores correlate with it at r = 0.54. Hub-like proteins also dominate the top 100: 83 distinct proteins cover 200 slots, and one protein appears 10 times.
   - So the high ranking may reflect "this protein is promiscuous in the benchmark" rather than a learned interaction. I did not test that directly with a train/test split by protein.
   - Promiscuous hubs are poor drug-target candidates anyway.
   - Real use means novel pairs among proteins the model hasn't seen paired. The benchmark gives no evidence about that.

2. **The scored set is not representative.**
   - Only 858 of the 52,725 labeled pairs (1.6%) have scores, covering 612 of 15,525 proteins.
   - The positive rate in the scored set is 60%, against 9% in the full benchmark. Whatever selected these pairs was not random, so the precision and AUROC figures can't be extrapolated to the full set.
   - I can't tell how the subset was chosen. You should find out.

3. **A third of the scores look like a default value.**
   - 326 pairs (38%) sit at about 0.00417, which looks like a floor or fill value rather than a real prediction.
   - 12% of those are true interactors, so those pairs are effectively missed.
   - The score isn't calibrated: the 0.1–0.3 bin is 96% positive. Don't read the scores as probabilities.
   - Excluding the floor pairs, AUROC drops to 0.844.

4. **The benchmark may be too easy.** I didn't check whether the benchmark negatives are random pairs, which are usually easy to reject. Interacting is also not the same as druggable or disease-relevant. This benchmark cannot speak to either.

**What I'd do before relying on it**

- Rerun the evaluation with protein-disjoint (cold-start) splits, or at least report performance on pairs where neither protein appears in training.
- Report results stratified by protein degree, and against the degree baseline above.
- Find out why only 1.6% of pairs were scored, and what the floor value means.
- Prefer candidates with independent support, such as experimental evidence, orthogonal databases or structural plausibility, over the raw ranking.

All my scripts are in the scratchpad (`/tmp/claude-0/a.py`).
