#!/usr/bin/env python3
"""
degree_assessment.py  —  the core degree-bias assessment for a PPI predictor.

Given a predictor's per-pair scores (y_prob) over a set of candidate protein
pairs, ask a single label-free question:

    Does the score track *node degree* — i.e. how many candidate pairs a
    protein appears in — rather than specific binding?

Node degree here is degree in the CANDIDATE graph: an edge is drawn for every
pair that was scored, positive or negative. So "degree" measures how heavily a
protein is studied / how often it was tested, not how many true interactions
it has. That is deliberate: it is exactly the study/sampling structure we are
assessing.

Outputs (written to the working directory):
  - dscript_assessment_summary.json : headline statistics
  - dscript_assessment_df.csv       : per-pair scores, degrees, ranks, labels

Reproduces the numbers in ../results/. seed=42.

Usage:
    python degree_assessment.py \
        --yprob ../data/dscript_human_v1_subset_yprob.tsv \
        --labels ../data/human_test_labeled.tsv
"""
import argparse
import json

import numpy as np
import pandas as pd
import networkx as nx
from scipy import stats
from sklearn.metrics import roc_auc_score, average_precision_score

N_PERM = 1000  # permutation-null iterations for the Spearman test


def main(yprob_path, labels_path, predictor, model_file,
         out_summary="dscript_assessment_summary.json", out_df="dscript_assessment_df.csv"):
    np.random.seed(42)

    # --- scores: 3-col TSV  prot1  prot2  y_prob  (NA where the model could not score) ---
    df = pd.read_csv(yprob_path, sep="\t", header=None, names=["p1", "p2", "yprob"])
    df = df[df.yprob != "NA"].copy()
    df["yprob"] = df.yprob.astype(float)

    # --- labels: 3-col TSV  prot1  prot2  label(0/1) ; matched order-independently ---
    lab = pd.read_csv(labels_path, sep="\t", header=None, names=["p1", "p2", "label"])
    labmap = {frozenset([r.p1, r.p2]): r.label for r in lab.itertuples()}
    df["label"] = df.apply(lambda r: labmap.get(frozenset([r.p1, r.p2]), np.nan), axis=1)
    n = len(df)

    # --- candidate graph: one edge per scored pair; degree = # candidate pairs touched ---
    G = nx.Graph()
    G.add_edges_from(df[["p1", "p2"]].itertuples(index=False, name=None))
    deg = dict(G.degree())
    df["deg1"] = df.p1.map(deg)
    df["deg2"] = df.p2.map(deg)
    # preferential-attachment degree score: product of endpoint degrees, no biology
    df["deg_score"] = df.deg1 * df.deg2
    df["rank_yprob"] = df.yprob.rank(ascending=False, method="min").astype(int)
    df["rank_deg"] = df.deg_score.rank(ascending=False, method="min").astype(int)

    # --- Spearman(score, degree) vs a permutation null ---
    obs_r = stats.spearmanr(df.yprob, df.deg_score).correlation
    perm = np.empty(N_PERM)
    yv = df.yprob.values.copy()
    dv = df.deg_score.values
    for i in range(N_PERM):
        perm[i] = stats.spearmanr(np.random.permutation(yv), dv).correlation
    p_emp = (np.sum(np.abs(perm) >= abs(obs_r)) + 1) / (N_PERM + 1)

    # --- how much of the labelled discrimination is degree alone? ---
    d2 = df.dropna(subset=["label"]).copy()
    d2["label"] = d2.label.astype(int)
    auroc_y = roc_auc_score(d2.label, d2.yprob)
    auroc_d = roc_auc_score(d2.label, d2.deg_score)   # degree-only baseline
    aupr_y = average_precision_score(d2.label, d2.yprob)
    aupr_d = average_precision_score(d2.label, d2.deg_score)
    prev = d2.label.mean()

    # --- do the two top-K lists even agree? ---
    ov = {}
    for K in [5, 10, 20, 50]:
        a = set(df.nsmallest(K, "rank_yprob").index)
        b = set(df.nsmallest(K, "rank_deg").index)
        ov[K] = len(a & b)

    df.to_csv(out_df, index=False)
    summary = dict(
        predictor=predictor, model_file=model_file,
        n_pairs=int(n), n_labeled=int(len(d2)),
        prevalence=round(float(prev), 4),
        spearman_yprob_deg=round(float(obs_r), 4),
        spearman_null_absmean=round(float(np.abs(perm).mean()), 4),
        spearman_emp_p=float(p_emp),
        auroc_yprob=round(float(auroc_y), 4),
        auroc_degree=round(float(auroc_d), 4),
        auroc_premium=round(float(auroc_y - auroc_d), 4),
        aupr_yprob=round(float(aupr_y), 4),
        aupr_degree=round(float(aupr_d), 4),
        overlapK={str(k): v for k, v in ov.items()},
    )
    json.dump(summary, open(out_summary, "w"), indent=2)
    print(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--yprob", default="../data/dscript_human_v1_subset_yprob.tsv",
                    help="3-col TSV: prot1  prot2  y_prob")
    ap.add_argument("--labels", default="../data/human_test_labeled.tsv",
                    help="3-col TSV: prot1  prot2  label(0/1)")
    ap.add_argument("--predictor", default="D-SCRIPT human_v1")
    ap.add_argument("--model-file", default="human_v1.sav")
    ap.add_argument("--out-summary", default="dscript_assessment_summary.json")
    ap.add_argument("--out-df", default="dscript_assessment_df.csv")
    a = ap.parse_args()
    main(a.yprob, a.labels, a.predictor, a.model_file, a.out_summary, a.out_df)
