# Wine Recommendation Example

This is the current reference example for the eval engine.

It demonstrates:
- recommendation-style evaluation
- critical gates for hard constraints
- heuristic scoring across qualitative dimensions
- optional LLM-as-judge analysis
- regression comparison across runs

## Files

- `dataset.json` — evaluation cases for wine recommendation prompts
- `rubric.json` — critical gates, weights, and thresholds for this task

## Notes

This example remains the baseline reference task while the repo evolves toward a reusable multi-example evaluation framework.