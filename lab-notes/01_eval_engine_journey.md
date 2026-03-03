# Eval Engine Lab Notebook

Author: Vineeth C. Vijayan  
Purpose: Internal learning lab for building evaluation infrastructure for LLM systems.

---

## Session 1 — Foundations

Key realization:

LLMs are non-deterministic systems. Traditional pass/fail testing is insufficient.
Evaluation requires a combination of:

- deterministic gates
- heuristic scoring
- baselines
- regression comparison

The goal is not perfect scoring but **stable measurement**.

---

## Session 2 — Building the Eval Harness

Components implemented:

- dataset.json → test cases
- rubric.json → scoring weights
- scorer.py → critical gates + heuristic scoring
- confidence.py → evaluator confidence heuristic
- runner.py → orchestrates evaluation runs
- regression_compare.py → baseline regression detection

Outputs generated:

- results/latest_results.json
- results/run_<timestamp>.json
- results/report.csv

---

## Session 3 — Real LLM Integration

Added OpenAI API support.

Challenges encountered:

- model outputs lacked tasting notes
- scoring dropped due to rubric mismatch
- system prompt needed stricter formatting contract

Updated system prompt to enforce:

- exactly 3 items
- price in €
- tasting notes
- region included

Result: scoring aligned with rubric → PASS.

---

## Session 4 — Baseline Versioning

Two baselines introduced:

mock baseline
baselines/baseline_results_mock.json

OpenAI baseline
baselines/baseline_results_openai_gpt-4o-mini.json

Regression comparison now detects score drift across runs.

---

## Key Learning So Far

Evaluation is not just scoring.

It requires:

- careful prompt contracts
- measurable outputs
- deterministic gates
- versioned baselines
- regression detection

The hardest part is **forcing a non-deterministic system to produce structured signals for evaluation.**

---

## Next Session Plan

System ownership walkthrough:

1. runner.py
2. scorer.py
3. confidence.py
4. regression_compare.py

For each module we will analyze:

- responsibility
- assumptions
- brittleness
- potential refactors