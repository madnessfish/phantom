"""
PHANTOM MCP server: exposes the degree-bias audit to any MCP client
(Claude Code, Claude Science, Claude Desktop).

Run:  python -m phantom_audit.server        (stdio transport)
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
try:  # MCP Python SDK 2.x
    from mcp.server.mcpserver import MCPServer as FastMCP
except ImportError:  # SDK 1.x
    from mcp.server.fastmcp import FastMCP

from . import core

REPO = Path(__file__).resolve().parent.parent
DEMO_SCORES = REPO / "data" / "dscript_human_v1_subset_yprob.tsv"
DEMO_LABELS = REPO / "data" / "human_test_labeled.tsv"

mcp = FastMCP(
    "phantom",
    instructions=(
        "PHANTOM audits protein-protein interaction (PPI) predictors for degree bias: "
        "whether a score tracks how often a protein appears among candidate pairs (hubs, "
        "well-studied proteins) rather than specific binding. Use it whenever you evaluate, "
        "benchmark, or rank targets with a PPI predictor. Report findings with the caveats "
        "the tools return and never make the claims listed under do_not_claim."
    ),
)


def _resolve(path: str | None) -> Path | None:
    if not path:
        return None
    p = Path(path).expanduser()
    if not p.exists():
        raise FileNotFoundError(f"{p} not found")
    return p.resolve()


# ----------------------------------------------------------------------- tools
@mcp.tool()
def audit_ppi_predictor(scores_path: str, labels_path: str | None = None,
                        predictor_name: str = "unnamed predictor",
                        n_perm: int = 1000, seed: int = 42,
                        out_dir: str | None = None) -> dict:
    """Run the full PHANTOM degree-bias audit on a PPI predictor's scores.

    Args:
        scores_path: 3-column file (TSV, or CSV by extension): prot1, prot2, score.
            'NA' scores are dropped. Header row optional.
        labels_path: optional 3-column file: prot1, prot2, label (0/1). Pairs are matched
            order-independently. Without labels, only the label-free tests run.
        predictor_name: name to record in the summary.
        n_perm: permutation-null iterations for the score-degree correlation.
        seed: random seed (42 reproduces the published PHANTOM numbers).
        out_dir: if given, writes phantom_summary.json and phantom_pairs.csv there.

    Returns summary statistics, a verdict with fixed conservative wording, caveats,
    a list of claims not to make, and the top hub proteins.
    """
    summary, df = core.audit(_resolve(scores_path), _resolve(labels_path),
                             n_perm=n_perm, seed=seed, predictor=predictor_name)
    result = dict(summary=summary, verdict=core.verdict(summary), top_hubs=core.top_hubs(df))
    if out_dir:
        od = Path(out_dir).expanduser()
        od.mkdir(parents=True, exist_ok=True)
        (od / "phantom_summary.json").write_text(json.dumps(result, indent=2))
        df.to_csv(od / "phantom_pairs.csv", index=False)
        result["written"] = [str(od / "phantom_summary.json"), str(od / "phantom_pairs.csv")]
    return result


@mcp.tool()
def candidate_degree_profile(scores_path: str, top_n: int = 10) -> dict:
    """Describe the candidate graph: how many pairs each protein appears in.

    Label-free and fast. Use first to see whether a benchmark has hubs at all.
    """
    df = core.candidate_degrees(core.load_scores(_resolve(scores_path)))
    deg = (pd.concat([df[["p1", "deg1"]].set_axis(["p", "d"], axis=1),
                      df[["p2", "deg2"]].set_axis(["p", "d"], axis=1)])
           .drop_duplicates("p").d)
    return dict(n_pairs=int(len(df)), n_proteins=int(deg.size),
                degree_min=int(deg.min()), degree_median=float(deg.median()),
                degree_max=int(deg.max()),
                share_proteins_degree_1=round(float((deg == 1).mean()), 4),
                top_hubs=core.top_hubs(df, top_n))


@mcp.tool()
def score_degree_correlation(scores_path: str, n_perm: int = 1000, seed: int = 42) -> dict:
    """Spearman correlation between predictor score and degree product, with a
    score-permutation null (scores shuffled, graph and degrees fixed). Label-free."""
    df = core.candidate_degrees(core.load_scores(_resolve(scores_path)))
    return core.degree_correlation(df, n_perm=n_perm, seed=seed)


@mcp.tool()
def degree_only_baseline(scores_path: str, labels_path: str) -> dict:
    """AUROC/AUPR of the predictor versus a biology-free degree-product baseline on the
    labelled pairs. The difference is descriptive, not a biological-signal estimate."""
    df = core.attach_labels(core.load_scores(_resolve(scores_path)), _resolve(labels_path))
    out = core.degree_only_baseline(core.candidate_degrees(df))
    out["caveat"] = core.CAVEATS[1]
    return out


@mcp.tool()
def demo_paths() -> dict:
    """Paths to the bundled D-SCRIPT example (858-pair seed-42 subset) for a test run."""
    return dict(scores_path=str(DEMO_SCORES), labels_path=str(DEMO_LABELS),
                expected=dict(spearman_yprob_deg=0.6594, auroc_yprob=0.9439, auroc_degree=0.9054))


# ------------------------------------------------------------------- resources
@mcp.resource("phantom://readme")
def readme() -> str:
    """PHANTOM README: question, findings, provenance."""
    return (REPO / "README.md").read_text()


@mcp.resource("phantom://report")
def report() -> str:
    """Full D-SCRIPT assessment write-up with caveats."""
    return (REPO / "report" / "dscript_assessment_report.md").read_text()


@mcp.resource("phantom://interpretation-rules")
def interpretation_rules() -> str:
    """How to report a PHANTOM audit without overclaiming."""
    lines = ["# Reporting a PHANTOM audit", "", "## Always state"]
    lines += [f"- {c}" for c in core.CAVEATS]
    lines += ["", "## Never claim"] + [f"- {c}" for c in core.DO_NOT_CLAIM]
    return "\n".join(lines)


# --------------------------------------------------------------------- prompts
@mcp.prompt()
def audit_ppi_predictor_workflow(scores_path: str, labels_path: str = "") -> str:
    """Step-by-step degree-bias audit of a PPI predictor."""
    lab = f" and labels at {labels_path}" if labels_path else ""
    return (
        f"Audit the PPI predictor whose scores are at {scores_path}{lab} for degree bias.\n"
        "1. Call candidate_degree_profile to see whether the candidate graph has hubs.\n"
        "2. Call audit_ppi_predictor (with labels if available).\n"
        "3. Read phantom://interpretation-rules.\n"
        "4. Write a short report: what was tested, the numbers, the verdict findings, "
        "the caveats verbatim, and what the audit cannot tell us. Do not make any claim "
        "listed under do_not_claim."
    )


def main():
    mcp.run()


if __name__ == "__main__":
    main()
