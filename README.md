# eval-engine (mock-first EvalOps skeleton)

This repo is a lightweight evaluation harness for LLM-style systems.

## What it does
- Loads a dataset (`dataset.json`)
- Applies critical gates + heuristic scoring (`scorer.py`)
- Computes a weighted score + verdict (PASS/WARN/FAIL)
- Writes JSON + CSV reports into `results/`
- Supports baselines + regression detection (`regression_compare.py`)
- Adds evaluator confidence heuristically (`confidence.py`)

## Quickstart

```bash
cd eval-engine
python3 runner.py --set-baseline
python3 runner.py
python3 regression_compare.py results/baseline_results.json results/latest_results.json 0.3