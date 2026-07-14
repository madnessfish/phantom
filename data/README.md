# Data provenance

Two committed files are the inputs to `analysis/degree_assessment.py`. Both derive
from the **D-SCRIPT associated-data archive** (Sledzieski et al., Cell Systems
2021; Zenodo, CC BY 4.0). Protein identifiers are STRING ENSP keys
(`9606.ENSP…`, human).

### `dscript_human_v1_subset_yprob.tsv` (858 rows)
Per-pair interaction probability from D-SCRIPT's published `human_v1.sav`
model, produced by `analysis/run_dscript_predict.py`. Three columns, no
header:

```
prot1<TAB>prot2<TAB>y_prob
```

`y_prob` is the model's interaction probability; `NA` marks pairs the model
could not score (missing embedding). This is a **seed-42 subset** of the full
test set — capped to keep a range of candidate-degrees while making the
one-protein-at-a-time language-model embedding tractable on a shared GPU. The
full 52,725-pair test set would take ~8 h of embedding; the subset preserves
the degree-assessment structure (extending to the full set is a compute question,
not a method change).

### `human_test_labeled.tsv` (52,725 rows)
The benchmark gold-standard labels for the human test set. Three columns, no
header:

```
prot1<TAB>prot2<TAB>label   # label ∈ {0,1}
```

Positives are the benchmark's curated interacting pairs; negatives are
non-interacting pairs. Only the 858 pairs also present in the y_prob
file are used by the assessment (matched order-independently). **Note:** the
AUROC/AUPR numbers quantify the degree confound and should not be read as
D-SCRIPT's accuracy on a balanced or hard-negative task.

### Not committed
- `human_v1.sav`, `lm_v1.sav` (D-SCRIPT model + language model) and the full
  sequence FASTA — download from the D-SCRIPT associated-data archive. Only
  needed to regenerate scores with `run_dscript_predict.py`; not needed to
  reproduce the committed `results/`.
- STRING and Complex Portal data used by the companion notebook are fetched
  live from public REST APIs at run time.
