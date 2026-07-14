---
name: bias-lit-search
description: >
  Bounded, single-pass literature survey that flags known biases (degree,
  abundance, leakage, evaluation-protocol, annotation) in a research topic and
  identifies what prior work did NOT address. Returns a structured, bias-flagged
  citation table plus a short synthesis. Every citation is marked for human
  verification. Use to ground a project in prior art and locate the open gap —
  NOT as an exhaustive systematic review.
---

# bias-lit-search

## Purpose
Grounds a project in the *known biases* of its field. Surveys prior work, flags the
bias each paper concerns, and notes what each did not do — so the user can cite prior
art accurately and find the open gap. This is a foundation/positioning step, not an
audit of predictions.

## When to use
- Establishing prior art for a paper, proposal, or project.
- Checking whether a claimed contribution is already published.
- Producing publication counts per entity for a "streetlight" (attention-bias) check.

## Inputs
- `topic` (required): the research area, e.g. "protein-interaction / target-prediction ranking bias".
- `hypotheses` (optional): specific claims to ground, e.g. H1/H2.
- `areas` (optional): sub-areas to cover; defaults to the five below.
- `max_papers` (optional, default 20): hard cap. This is ONE pass — stop at the cap.

## Procedure
1. Survey primary sources (papers, preprints) across these areas, labeling each:
   1. Degree/hub bias in PPI / complex / target prediction (benchmark critiques, leakage, shortcut learning)
   2. AP-MS / assay-specific artifacts (abundant/nonspecific signal, frequency, scoring rationale)
   3. Network centrality as a target feature, and critiques of it
   4. Evidence that low-ranked / low-degree entities can still be relevant
   5. The same confound argument in adjacent fields (DTI, biomedical KG link prediction, link-prediction theory)
2. For each paper, emit one row of the OUTPUT TABLE below.
3. Write the SYNTHESIS (<=250 words).
4. Save output to `notes/litsearch_bias_<YYYY-MM-DDTHH-MM>.md`.

## Output table (one row per paper)
| citation (authors, year, venue) | link/DOI | area (1-5) | supports which hypothesis / context | one-sentence finding (own words, no long quotes) | BIAS flagged (degree / abundance / leakage / evaluation-protocol / annotation / other) | what it did NOT do (esp: per-prediction verdict on real data, or only benchmark/dataset-level?) | VERIFY? (always: yes) |

## Synthesis (<=250 words)
- What is firmly ESTABLISHED (so the user does not reclaim known results).
- Which hypotheses are well-supported vs UNDER-studied.
- Whether a per-prediction audit on real data already exists (name it, or mark the gap
  "appears open — provisional, confirm by reading").
- The 3-5 papers the user MUST cite.

## Guardrails
- ONE pass, capped at `max_papers`. Not exhaustive. Stop at the cap.
- Primary sources over reviews; use reviews only to find primaries.
- NO long quotations — paraphrase and cite.
- Be honest about how established each phenomenon is; if it's textbook, say so.
- Mark EVERY citation "VERIFY? yes" — literature output may contain errors or
  fabricated references; the user must confirm each before citing publicly.
- Do not reference the user's unpublished work.
