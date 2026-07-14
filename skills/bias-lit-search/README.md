# bias-lit-search

A bounded Claude Code Agent Skill that surveys the *known biases* in a research topic,
flags what each prior paper concerns, and notes what it did not address — returning a
structured, bias-flagged citation table plus a short synthesis.

Built during the Built with Claude: Life Sciences hackathon (Research track) as the
literature-grounding step of an independent prediction-audit pipeline. Designed to be
reusable across topics.

## Usage
Invoke with a `topic` (and optionally `hypotheses`, `areas`, `max_papers`). Output is a
Markdown file under `notes/`. Every citation is flagged for human verification — treat
the output as a draft to check, not ground truth.

## Scope
This is a single-pass grounding tool, not an exhaustive systematic review, and not an
audit of prediction outputs. It informs positioning and the streetlight (attention-bias)
check; it does not produce trust verdicts.

## License
MIT — see the [repository LICENSE](../../LICENSE).
