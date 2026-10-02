"""The MCP tools must reproduce the committed PHANTOM results exactly.

Run:  python -m pytest tests -q
"""
import asyncio
import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from phantom_audit import core  # noqa: E402

SCORES = REPO / "data" / "dscript_human_v1_subset_yprob.tsv"
LABELS = REPO / "data" / "human_test_labeled.tsv"
COMMITTED = json.loads((REPO / "results" / "dscript_assessment_summary.json").read_text())


def test_summary_matches_committed_json():
    summary, _ = core.audit(SCORES, LABELS, predictor="D-SCRIPT human_v1", model_file="human_v1.sav")
    for key, val in COMMITTED.items():
        assert summary[key] == val, f"{key}: got {summary[key]!r}, committed {val!r}"


def test_per_pair_table_matches_committed_csv():
    _, df = core.audit(SCORES, LABELS)
    ref = pd.read_csv(REPO / "results" / "dscript_assessment_df.csv")
    cols = ["p1", "p2", "yprob", "label", "deg1", "deg2", "deg_score", "rank_yprob", "rank_deg"]
    got = df[cols].reset_index(drop=True)
    pd.testing.assert_frame_equal(got.astype(ref[cols].dtypes.to_dict()), ref[cols], check_exact=False)


def test_verdict_flags_dscript_and_carries_caveats():
    summary, _ = core.audit(SCORES, LABELS)
    v = core.verdict(summary)
    assert v["degree_bias_flag"] is True
    assert v["caveats"] == core.CAVEATS
    assert any("% artifact" in c for c in v["do_not_claim"])


def test_no_bias_on_shuffled_scores(tmp_path):
    """Negative control: scores unrelated to degree must not be flagged on the correlation test."""
    df = core.load_scores(SCORES)
    df["yprob"] = df.yprob.sample(frac=1, random_state=0).values
    p = tmp_path / "shuffled.tsv"
    df.to_csv(p, sep="\t", header=False, index=False)
    summary, _ = core.audit(p, None, n_perm=200)
    assert abs(summary["spearman_yprob_deg"]) < core.STRONG_DEGREE_CORR
    assert core.verdict(summary)["degree_bias_flag"] is False


def test_mcp_protocol_round_trip():
    """Call the tool through a real stdio MCP session, as Claude Code / Claude Science would."""
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    async def run():
        params = StdioServerParameters(command=sys.executable, args=["-m", "phantom_audit.server"],
                                       cwd=str(REPO))
        async with stdio_client(params) as (r, w):
            async with ClientSession(r, w) as s:
                await s.initialize()
                tools = {t.name for t in (await s.list_tools()).tools}
                res = await s.call_tool("audit_ppi_predictor",
                                        {"scores_path": str(SCORES), "labels_path": str(LABELS)})
                resources = {str(x.uri) for x in (await s.list_resources()).resources}
                prompts = {p.name for p in (await s.list_prompts()).prompts}
                return tools, json.loads(res.content[0].text), resources, prompts

    tools, out, resources, prompts = asyncio.run(run())
    assert {"audit_ppi_predictor", "candidate_degree_profile", "score_degree_correlation",
            "degree_only_baseline", "demo_paths"} <= tools
    assert out["summary"]["spearman_yprob_deg"] == COMMITTED["spearman_yprob_deg"]
    assert out["summary"]["auroc_degree"] == COMMITTED["auroc_degree"]
    assert "phantom://interpretation-rules" in resources
    assert "audit_ppi_predictor_workflow" in prompts
