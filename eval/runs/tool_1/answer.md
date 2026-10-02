**Short answer: don't trust the top-ranked pairs for drug-target nomination as they stand.** The headline accuracy is high, but much of it can be reproduced by counting how often a protein appears in the candidate list. The top of the ranking is also dominated by those frequently appearing proteins.

**What I ran:** the PHANTOM degree-bias audit, a degree-only baseline, and a few checks of my own. Only 858 pairs in `scores.tsv` overlap the labels. `labels.tsv` has about 52.7k pairs with a 9% positive rate. The 858 scored pairs are 60% positive, so they are a heavily enriched subset. All numbers below come from that subset and may not carry over to the full benchmark.

**Findings**
- **Headline performance is strong.** AUROC is 0.944 and AUPR is 0.960.
- **A biology-free baseline gets most of the way there.** Scoring each pair by the product of its two proteins' candidate degrees gives AUROC 0.905 and AUPR 0.936. The predictor beats it by only 0.039 AUROC. That gap is descriptive, not an estimate of real biological signal.
- **Scores track degree.** The Spearman correlation between score and degree product is +0.66 (permutation p ≈ 0.001, against a null of about 0.03).
- **Positives are far more connected than negatives.** Mean endpoint degree is 6.6 for positives and 2.8 for negatives. Labels themselves are partly predictable from connectivity, which is a property of how the benchmark was built.
- **The top of the ranking is the hub-heavy part.** The top 10 to 100 pairs are about 99–100% positive. Their median degree product is about 40–45, against 18 for all pairs. A high score therefore says little beyond "involves well-represented proteins", and for target nomination those hub proteins are the least informative candidates.
- **Performance drops where degree can't help.** In the lower-degree half of pairs, the prevalence is 29% and AUROC falls to 0.86. The top 50 low-degree pairs are 84% positive, which is still decent. The upper-degree half has 93% prevalence and AUROC 0.95, so the high-degree half is easy mostly because it is nearly all positive. These are my own split-half checks, so treat them as exploratory.

**What this does and doesn't show:**
- It shows the ranking rewards hubs on this set.
- It doesn't show that the model "only learns degree" or has no real signal. The 0.04 premium and the 0.86 AUROC on low-degree pairs suggest some pair-specific signal.
- It doesn't show how much of the model's accuracy is caused by degree.

**Recommendation**
1. Don't nominate targets directly from the global top-ranked list.
2. Always report the predictor next to the degree-only baseline.
3. Re-evaluate on a degree-matched or degree-stratified benchmark, and ideally on a split with no protein overlap between train and test.
4. If you use the predictor, rank within degree strata, or look at pairs that score high despite low degree.
5. Treat any shortlist as hypotheses that need orthogonal evidence. Interacting is also not the same as being druggable.
6. Rerun the audit on the full labelled set rather than the 858-pair subset.
