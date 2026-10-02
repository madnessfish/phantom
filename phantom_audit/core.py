"""
phantom_audit.core — the PHANTOM degree-bias assessment as importable functions.

Same statistics as analysis/degree_assessment.py, split into steps an agent can
call one at a time. `audit()` reproduces results/dscript_assessment_summary.json
exactly (seed 42); tests/test_reproduce.py checks this.

Degree is degree in the CANDIDATE graph: one edge per scored pair, positive or
negative. It measures how often a protein was tested (study / sampling
structure), not how many true interactions it has.
"""
from __future__ import annotations

from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import average_precision_score, roc_auc_score

# Heuristic thresholds for the verdict. They are reporting conventions, not
# calibrated cut-offs; every verdict also returns the raw numbers.
STRONG_DEGREE_CORR = 0.3      # |Spearman(score, degree)| above this is "tracks degree"
DEGREE_BASELINE_FLAG = 0.75   # degree-only AUROC above this means labels are degree-separable
ALPHA = 0.05

CAVEATS = [
    "Degree is computed on the candidate graph of the pairs supplied; values change "
    "if the audit is run on a different subset of the benchmark.",
    "The AUROC difference between the predictor and the degree-only baseline is "
    "descriptive. It is not a decomposition into biological versus degree-derived signal.",
    "A high score-degree correlation shows the ranking rewards hubs on this set; it does "
    "not show how much of the model's signal is causally attributable to degree.",
]

DO_NOT_CLAIM = [
    "a '% artifact' or '% real' figure",
    "that the model 'only learns degree' or 'learns no biology'",
    "that the AUROC premium is the model's 'biological signal'",
    "results for the full benchmark when only a subset was audited",
]


# --------------------------------------------------------------------------- I/O
def _read_pairs(path: str | Path, value_col: str) -> pd.DataFrame:
    """Read a 3-column pair file (TSV or CSV, header optional)."""
    path = Path(path)
    sep = "," if path.suffix.lower() == ".csv" else "\t"
    df = pd.read_csv(path, sep=sep, header=None, dtype=str)
    if df.shape[1] < 3:
        raise ValueError(f"{path}: expected 3 columns (prot1, prot2, {value_col}), got {df.shape[1]}")
    df = df.iloc[:, :3]
    df.columns = ["p1", "p2", value_col]
    # drop a header row if present (third field not numeric and not NA)
    first = df.iloc[0][value_col]
    if first != "NA" and pd.to_numeric(pd.Series([first]), errors="coerce").isna().all():
        df = df.iloc[1:].reset_index(drop=True)
    return df


def load_scores(path: str | Path) -> pd.DataFrame:
    """prot1, prot2, score. Rows with score 'NA' (unscored) are dropped."""
    df = _read_pairs(path, "yprob")
    df = df[df.yprob != "NA"].copy()
    df["yprob"] = df.yprob.astype(float)
    return df.reset_index(drop=True)


def attach_labels(df: pd.DataFrame, labels_path: str | Path) -> pd.DataFrame:
    """Match labels to scored pairs order-independently. Unmatched pairs get NaN."""
    lab = _read_pairs(labels_path, "label")
    labmap = {frozenset([r.p1, r.p2]): int(float(r.label)) for r in lab.itertuples()}
    out = df.copy()
    out["label"] = [labmap.get(frozenset([a, b]), np.nan) for a, b in zip(out.p1, out.p2)]
    return out


# ----------------------------------------------------------------------- steps
def candidate_degrees(df: pd.DataFrame) -> pd.DataFrame:
    """Add deg1, deg2 and deg_score (= deg1*deg2, preferential attachment, no biology)."""
    G = nx.Graph()
    G.add_edges_from(df[["p1", "p2"]].itertuples(index=False, name=None))
    deg = dict(G.degree())
    out = df.copy()
    out["deg1"] = out.p1.map(deg)
    out["deg2"] = out.p2.map(deg)
    out["deg_score"] = out.deg1 * out.deg2
    out["rank_yprob"] = out.yprob.rank(ascending=False, method="min").astype(int)
    out["rank_deg"] = out.deg_score.rank(ascending=False, method="min").astype(int)
    return out


def degree_correlation(df: pd.DataFrame, n_perm: int = 1000, seed: int = 42) -> dict:
    """Spearman(score, deg_score) against a score-permutation null.

    Null: scores shuffled, candidate graph and degrees held fixed.
    """
    rng = np.random.RandomState(seed)  # same stream as np.random.seed(seed) in the script
    obs = stats.spearmanr(df.yprob, df.deg_score).correlation
    yv, dv = df.yprob.values.copy(), df.deg_score.values
    perm = np.array([stats.spearmanr(rng.permutation(yv), dv).correlation for _ in range(n_perm)])
    p = (np.sum(np.abs(perm) >= abs(obs)) + 1) / (n_perm + 1)
    return dict(
        spearman_yprob_deg=round(float(obs), 4),
        spearman_null_absmean=round(float(np.abs(perm).mean()), 4),
        spearman_emp_p=float(p),
        n_perm=n_perm,
        null="score permutation (graph and degrees fixed)",
    )


def degree_only_baseline(df: pd.DataFrame) -> dict:
    """Compare the predictor with a biology-free degree-product baseline on labelled pairs."""
    d = df.dropna(subset=["label"]).copy()
    if d.empty:
        raise ValueError("no labelled pairs matched; supply a labels file that covers the scored pairs")
    d["label"] = d.label.astype(int)
    if d.label.nunique() < 2:
        raise ValueError("labelled pairs contain only one class; AUROC is undefined")
    ay, ad = roc_auc_score(d.label, d.yprob), roc_auc_score(d.label, d.deg_score)
    pos, neg = d[d.label == 1], d[d.label == 0]
    return dict(
        n_labeled=int(len(d)),
        prevalence=round(float(d.label.mean()), 4),
        auroc_yprob=round(float(ay), 4),
        auroc_degree=round(float(ad), 4),
        auroc_premium=round(float(ay - ad), 4),
        aupr_yprob=round(float(average_precision_score(d.label, d.yprob)), 4),
        aupr_degree=round(float(average_precision_score(d.label, d.deg_score)), 4),
        mean_endpoint_degree_pos=round(float(pos[["deg1", "deg2"]].values.mean()), 2),
        mean_endpoint_degree_neg=round(float(neg[["deg1", "deg2"]].values.mean()), 2),
    )


def topk_overlap(df: pd.DataFrame, ks=(5, 10, 20, 50)) -> dict:
    """How many of the top-K pairs by score are also top-K by degree product."""
    out = {}
    for k in ks:
        a = set(df.nsmallest(k, "rank_yprob").index)
        b = set(df.nsmallest(k, "rank_deg").index)
        out[str(k)] = len(a & b)
    return out


def top_hubs(df: pd.DataFrame, n: int = 10) -> list[dict]:
    """Highest-degree proteins and their mean score: the candidate 'frequent flyers'."""
    long = pd.concat([df[["p1", "deg1", "yprob"]].set_axis(["protein", "degree", "yprob"], axis=1),
                      df[["p2", "deg2", "yprob"]].set_axis(["protein", "degree", "yprob"], axis=1)])
    g = long.groupby("protein").agg(degree=("degree", "first"), mean_score=("yprob", "mean"))
    g = g.sort_values(["degree", "mean_score"], ascending=False).head(n)
    return [dict(protein=p, degree=int(r.degree), mean_score=round(float(r.mean_score), 4))
            for p, r in g.iterrows()]


# -------------------------------------------------------------------- verdict
def verdict(summary: dict) -> dict:
    """Plain-language findings with fixed, conservative wording."""
    findings = []
    r, p = summary["spearman_yprob_deg"], summary["spearman_emp_p"]
    if p < ALPHA and r >= STRONG_DEGREE_CORR:
        findings.append(f"Scores track candidate degree (Spearman {r:+.2f}, permutation p = {p:.3g}): "
                        "top-ranked pairs are enriched for hubs.")
    elif p < ALPHA and r <= -STRONG_DEGREE_CORR:
        findings.append(f"Scores anti-correlate with candidate degree (Spearman {r:+.2f}, p = {p:.3g}): "
                        "top-ranked pairs favour low-degree, specific pairs.")
    else:
        findings.append(f"No strong score-degree relationship (Spearman {r:+.2f}, p = {p:.3g}).")

    if "auroc_degree" in summary:
        ad, ay = summary["auroc_degree"], summary["auroc_yprob"]
        if ad >= DEGREE_BASELINE_FLAG:
            findings.append(f"Labels are separable by degree alone on this set (degree-only AUROC {ad:.3f} "
                            f"vs predictor {ay:.3f}). Report the predictor's AUROC next to this baseline.")
        else:
            findings.append(f"Degree alone separates labels weakly (AUROC {ad:.3f} vs predictor {ay:.3f}).")
        if "mean_endpoint_degree_pos" in summary:
            findings.append(f"Mean endpoint degree: positives {summary['mean_endpoint_degree_pos']}, "
                            f"negatives {summary['mean_endpoint_degree_neg']}.")

    flagged = (p < ALPHA and abs(r) >= STRONG_DEGREE_CORR and r > 0) or \
              summary.get("auroc_degree", 0) >= DEGREE_BASELINE_FLAG
    return dict(degree_bias_flag=bool(flagged), findings=findings,
                caveats=CAVEATS, do_not_claim=DO_NOT_CLAIM,
                thresholds=dict(strong_degree_corr=STRONG_DEGREE_CORR,
                                degree_baseline_flag=DEGREE_BASELINE_FLAG, alpha=ALPHA,
                                note="heuristic reporting thresholds, not calibrated"))


# ----------------------------------------------------------------------- audit
def audit(scores_path, labels_path=None, n_perm: int = 1000, seed: int = 42,
          predictor: str = "unnamed predictor", model_file: str = "") -> tuple[dict, pd.DataFrame]:
    """Full audit. Returns (summary, per-pair dataframe)."""
    df = load_scores(scores_path)
    if labels_path:
        df = attach_labels(df, labels_path)
    df = candidate_degrees(df)

    summary = dict(predictor=predictor, model_file=model_file,
                   n_pairs=int(len(df)), n_proteins=int(len(set(df.p1) | set(df.p2))))
    corr = degree_correlation(df, n_perm=n_perm, seed=seed)
    if labels_path:
        summary.update(degree_only_baseline(df))
    summary.update({k: corr[k] for k in ("spearman_yprob_deg", "spearman_null_absmean", "spearman_emp_p")})
    summary["overlapK"] = topk_overlap(df)
    return summary, df
