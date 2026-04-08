# Eval Engine

A lightweight evaluation framework for LLM systems combining:

- deterministic evaluation (critical gates + heuristics)
- probabilistic evaluation (LLM-as-judge)
- regression detection across runs

---

## Core Idea

LLM systems are non-deterministic.

Traditional pass/fail testing is not enough.

This project explores a layered evaluation approach:

```text
Dataset
↓
System Under Test Response
↓
Critical Gates (hard constraints)
↓
Heuristic Scoring (deterministic)
↓
(Optional) Judge Ensemble (LLM)
↓
Regression Comparison
```
---

## Example Packs

The project now supports **multiple evaluation domains** via self-contained example packs.

### 1. Wine Recommendation (Reference Example)

- recommendation-style evaluation
- structured list outputs
- qualitative scoring (taste, tone, diversity)
- baseline reference task

examples/wine_recommendation/

---

### 2. Retail Support (Multi-purpose Example)

Demonstrates:

- recommendation tasks
- support assistant evaluation
- retrieval-grounded responses (RAG-style)
- simple agent workflows (mock tools)
- structured output expectations

examples/retail_support/

---

## Project Structure

```text
.
│
├── examples/
│   ├── wine_recommendation/
│   └── retail_support/
│
├── configs/
│   ├── tasks/
│   ├── systems/
│   └── judges/
│
├── results/<task_name>/
├── baselines/<task_name>/
│
├── runner.py
├── scorer.py
├── task_loader.py
├── tool_simulator.py
├── schemas.py
├── regression_compare.py
```
---

## Running Evaluations

### Wine example
```bash
python3 runner.py --task-config configs/tasks/wine.yaml --mode mock
```
### Retail support example
```bash
python3 runner.py --task-config examples/retail_support/task_config.yaml --mode mock
```
⸻

## Writing Baselines
```bash
python3 runner.py --task-config configs/tasks/wine.yaml --mode mock --write-baseline
python3 runner.py --task-config examples/retail_support/task_config.yaml --mode mock --write-baseline
```
⸻

## Regression Comparison

Using explicit paths:
```bash
python3 regression_compare.py baselines/wine_recommendation/baseline_results.json results/wine_recommendation/latest_results.json
```
Using task shortcut:
```bash
python3 regression_compare.py --task wine_recommendation
python3 regression_compare.py --task retail_support
```

⸻

## What This Project Demonstrates
	•	How to evaluate LLM outputs beyond simple correctness
	•	How to combine heuristics and LLM judges
	•	How to detect regressions in non-deterministic systems
	•	How to design evaluation datasets and rubrics
	•	How to structure reusable evaluation tasks

⸻

## Status

This is a V1 learning lab project.

Focus:
	•	clarity over completeness
	•	simplicity over abstraction
	•	experimentation over production design

⸻

## Future Directions
	•	judge disagreement visualization
	•	evaluation analytics across runs
	•	cross-model judge comparison
	•	richer agent workflow evaluation
	•	dashboard / visualization layer