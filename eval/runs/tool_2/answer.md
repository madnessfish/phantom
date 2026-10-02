**Short answer: don't use the top-ranked pairs to nominate drug targets on this evidence.** The predictor ranks well on this benchmark, but a degree-only baseline nearly matches it, and the top-ranked pairs are mostly hub proteins.

**Results** (858 scored pairs, all found in labels.tsv; I checked this with the PHANTOM tools and my own calculation, and the two agree):
- **Headline performance is high.** AUROC is 0.944 and AUPR is 0.960. The top 10, 25 and 50 pairs are all true positives, and the top 100 are 99% positive.
- **A baseline with no biology nearly matches it.** Scoring each pair only by how often its proteins appear among the candidate pairs gives AUROC 0.905 and AUPR 0.936. The predictor's margin over that baseline is 0.039 AUROC.
- **Scores track degree.** Spearman correlation between score and endpoint degree is +0.66, against a permutation null of about 0.03 (p ≈ 0.001).
- **Positives are hub-heavy.** Mean endpoint degree is 6.6 for positives and 2.8 for negatives. The maximum degree is 13 and the median is 2, so this is a small graph.

**Why this matters for target nomination:** the top-ranked pairs are likely to be pairs of well-connected proteins, which is what you'd expect to find among common, well-studied proteins. A top-50 list with 100% precision is therefore not evidence that the predictor found specific binding. Pairs between well-studied hubs may simply be easy to rank. Hub proteins also tend to be poor drug targets, because they are essential and drugging them is likely to cause toxicity. The ranked list may not reflect what you want to nominate.

**Caveats:**
- **Subset prevalence.** The scored subset is 60.5% positive. The full labels file is only 9.1% positive. Real-world precision at the top of the list would be much lower than the 100% seen here, and the AUPR is inflated by the enriched subset.
- **How degree was measured.** Degree here comes from the 858 supplied pairs, so it depends on how the subset was sampled. How these pairs were chosen from the larger benchmark isn't clear from the files.
- **What the comparison does and doesn't show.** The 0.039 gap over the baseline is descriptive. It doesn't say how much of the predictor's signal is real biology versus degree. I'm not claiming the model "only learns degree", only that this benchmark can't tell the two apart.
- **Two duplicated pairs in labels.tsv.** I kept the first occurrence of each. This is unlikely to change the results.

**What would change my view:** rerun on a benchmark where degree is balanced between positives and negatives, or where proteins don't overlap between train and test. Also check precision at the top of the list in the full 9%-prevalence setting, and whether the top-ranked pairs involve proteins that are plausible drug targets. Experimental validation of a few top pairs involving non-hub proteins would be more informative than any further benchmark metric.
