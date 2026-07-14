![Built with Claude: Life Sciences — a global virtual hackathon, July 07-13, in partnership with Gladstone Institutes](docs/hackathon_banner.png)

# PHANTOM: Catch phantom targets before the bench

*A degree-bias assessment for protein-protein interaction (PPI) predictors — is protein degree biology, or bias?*

> Built for the **Built with Claude: Life Sciences** hackathon.

A top-ranked protein-protein interaction (PPI) is only useful if its rank
reflects *specific binding*, not *how well-studied or how connected* the
protein is. This repository asks one question of a PPI score, experimental or
computational:

> **Does the score track a protein's node degree — how many candidate pairs it
> appears in — rather than specific interaction?**

If it does, the ranking rewards hubs and abundant, heavily-studied proteins,
and its top is filled with promiscuous "frequent flyers" while genuine but
low-degree members sink to the bottom.

## The finding, in one line

The **same degree assessment** applied to two kinds of score points in **opposite
directions**:

| score | dataset | corr(score, degree) | reading |
|---|---|---|---|
| experimental | BioPlex 293T | **−0.10** | top pairs are specific, low-degree |
| experimental | BioPlex HCT116 | **−0.11** | top pairs are specific, low-degree |
| computational | **D-SCRIPT** human_v1 | **+0.66** | top pairs are enriched for hubs |

For the computational predictor (D-SCRIPT, sequence-only deep model), the
observed score–degree correlation exceeds a score-permutation null in which
prediction scores are shuffled while the candidate graph and its degree values
remain fixed (null |r| ≈ 0.026, empirical p ≈ 0.001, 1000 permutations,
seed 42). A candidate-degree baseline strongly separates positive and negative
labels in this selected benchmark subset (**AUROC 0.905**); D-SCRIPT scores
(**AUROC 0.944**) are also correlated with candidate degree. D-SCRIPT exceeds
the candidate-degree baseline by **0.039 AUROC** on this subset — this
difference is descriptive and should not be interpreted as a decomposition of
biological versus degree-derived signal. These findings show that model
performance on this subset must be interpreted alongside its degree structure,
but they do not establish how much of the model's signal is causally
attributable to degree.

All reported magnitudes are conditional on the selected 858-pair subset;
candidate degrees and assessment statistics may change when calculated over the
complete benchmark.

See [`report/dscript_assessment_report.md`](report/dscript_assessment_report.md) for the
full write-up, caveats, and provenance.

## Two threads

**1. Assessment of a real predictor (D-SCRIPT).**
D-SCRIPT's published `human_v1.sav` model was run on a seed-42 subset (858
pairs / 612 proteins) of its own associated-data human benchmark, then assessed.
- `analysis/run_dscript_predict.py` — produces the per-pair `y_prob` scores
  (GPU; version-compat patch for the 2021 pickle).
- `analysis/degree_assessment.py` — the assessment itself. Reproduces
  `results/dscript_assessment_summary.json` **exactly** from the committed scores
  and labels.

**2. Fully-reproducible companion (no proprietary data).**
A self-contained demonstration of the same confound on a real STRING v12
network of 3 curated complexes + 8 hub candidates, plus a target-recovery
filter. Runs top-to-bottom from public REST APIs — no model file needed.
- `notebook/degree_bias_reproducible.ipynb` — build network → connectivity
  leaderboard (ACTB #1, MCM6 #29) → prove degree is a confound via a
  degree-preserving edge-swap null → recover real members with a
  specificity × evidence × membership filter.
- `analysis/show_actb_complexes.py` — why ACTB reads as a hub: it is a curated
  member of dozens of *other* complexes absent from the demo graph.

## Included skill: `bias-lit-search`

`skills/bias-lit-search/` is a reusable Agent Skill that grounds a project in
the *known biases* of its field. Given a `topic`, it runs a single, bounded
pass over primary literature, flags the bias each paper concerns (degree,
abundance, leakage, evaluation-protocol, annotation), notes what each did *not*
address, and returns a bias-flagged citation table plus a short synthesis. It
was the literature-grounding step for this project. Every citation is marked
for human verification — the output is a draft to check, not ground truth. See
[`skills/bias-lit-search/README.md`](skills/bias-lit-search/README.md).

## Repository layout

```
ppi-degree-assessment/
├── README.md
├── requirements.txt
├── LICENSE
├── analysis/
│   ├── degree_assessment.py            # core assessment; reproduces results/ exactly
│   ├── run_dscript_predict.py     # D-SCRIPT scoring (GPU, version-patched)
│   └── show_actb_complexes.py     # ACTB hub explanation (Complex Portal)
├── notebook/
│   └── degree_bias_reproducible.ipynb   # self-contained, public-data-only
├── data/
│   ├── dscript_human_v1_subset_yprob.tsv   # D-SCRIPT scores (assessment input)
│   ├── human_test_labeled.tsv              # benchmark labels (assessment input)
│   └── README.md                           # data provenance
├── results/
│   ├── dscript_assessment_summary.json # headline statistics
│   ├── dscript_assessment_df.csv       # per-pair scores, degrees, ranks, labels
│   ├── ppi_target_reranking.csv   # naive → 3-step-filter re-ranking
│   ├── degree_specificity.csv     # per-protein degree vs specificity
│   └── mcm6_partner_evidence.csv  # MCM6 partner evidence table
├── figures/                       # 7 rendered figures (see below)
├── report/
│   └── dscript_assessment_report.md    # full write-up
└── skills/
    └── bias-lit-search/           # Agent Skill: bias-flagged literature grounding
        ├── SKILL.md
        └── README.md
```

## Figures

| file | what it shows |
|---|---|
| `fig1_exp_vs_pred_degree.png` | the core contrast: experimental scores avoid hubs (−0.10), D-SCRIPT tracks them (+0.66); benchmark positives are degree-enriched |
| `fig2_degree_leakage_yprob.png` | a degree-only link predictor scores AUC 0.70 and holds it after biology is scrambled away |
| `fig3_degree_is_confound.png` | the connectivity "score" is ~raw degree (ρ 0.94); ACTB stays top-3 in 100% of degree-preserving scrambles |
| `fig4_hub_vs_member_network.png` | network view — ACTB (degree 23) wins, true member MCM6 (degree 6) is buried |
| `fig5_rank_vs_membership.png` | the leaderboard: hubs on top, true members at the bottom |
| `fig6_specificity_recovers_signal.png` | degree × specificity separates real members from promiscuous artifacts |
| `fig7_three_step_filter.png` | PPI hit → candidate target via specificity × evidence × membership |

## Reproduce

```bash
pip install -r requirements.txt

# 1. the assessment (fast, CPU, no network) — reproduces results/ exactly
cd analysis
python degree_assessment.py

# 2. the self-contained companion (needs internet: STRING + Complex Portal)
jupyter nbconvert --to notebook --execute ../notebook/degree_bias_reproducible.ipynb

# 3. (optional) regenerate D-SCRIPT scores from the published model (GPU)
#    requires the D-SCRIPT associated-data archive; see data/README.md
python run_dscript_predict.py --pairs <pairs> --seqs <fasta> \
    --model human_v1.sav --lm lm_v1.sav -o yprob.tsv
```

## Data & citations

- **D-SCRIPT** — Sledzieski, Singh, Cowen & Berger. *D-SCRIPT translates
  genome to phenome with sequence-based, structure-aware, genome-scale
  predictions of protein-protein interactions.* Cell Systems 12(10):969–982.e6
  (2021). doi:10.1016/j.cels.2021.08.010 · PMID 34536380 · PMCID PMC8586911.
  Model, sequences and benchmark pairs from the associated-data archive
  (Zenodo, CC BY 4.0).
- **BioPlex 3.0** — Huttlin et al. *Dual proteome-scale networks reveal
  cell-specific remodeling of the human interactome.* Cell 184(11):3022–3040
  (2021). doi:10.1016/j.cell.2021.04.011.
- **Node-degree confound in PPI benchmarks** — Bernett et al. *Cracking the
  black box of deep sequence-based protein-protein interaction prediction.*
  Briefings in Bioinformatics 25(2):bbae076 (2024). The edge-swap null used in
  the companion notebook is in the spirit of that node-degree confound; the
  method here (Maslov–Sneppen degree-preserving swaps) differs from their
  KaHIP/CD-HIT split control.
- **STRING v12** (`string-db.org`) and **EBI Complex Portal / IntAct**
  (`ebi.ac.uk/intact/complex-ws`) — queried live by the companion notebook.

See [`data/README.md`](data/README.md) for exact provenance of the two
committed input files.

## Acknowledgments

Built for the **Built with Claude: Life Sciences** hackathon.
