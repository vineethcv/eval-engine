# Eval Engine Learning Lab

A minimal, practical evaluation framework for LLM systems combining deterministic scoring and LLM-based analysis.

This project explores how to evaluate **non-deterministic AI outputs** using a layered approach:
- deterministic rules (critical gates)
- heuristic scoring
- LLM-as-judge (analytical signal)
- regression comparison

---

## Why this exists

Traditional QA assumes deterministic outputs.

LLM systems introduce:
- variability
- qualitative responses
- probabilistic reasoning

This repo demonstrates a **practical evaluation architecture** to handle that.

---

## Architecture

Dataset
↓
Model Response
↓
Critical Gates (hard constraints)
↓
Heuristic Scoring (deterministic)
↓
(Optional) Judge Ensemble (LLM)
↓
Regression Comparison

Key principle:
> Heuristics decide PASS/FAIL. Judges provide analytical insight.

---

## Repo structure

```text
.
├── dataset.json              # evaluation queries
├── rubric.json              # scoring rules & weights
├── runner.py                # main evaluation pipeline
├── scorer.py                # deterministic scoring logic
├── confidence.py            # evaluation confidence signal
├── llm_client.py            # OpenAI response generation∏
├── judge_client.py          # LLM-as-judge ensemble
├── regression_compare.py    # regression detection
│
├── tests/                   # minimal test coverage
├── examples/                # sample outputs
│
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
└── LICENSE

```

## Quickstart

### 1. Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

Add your OpenAI key:
OPENAI_API_KEY=your_key_here
⸻

Run examples

Mock (no API required)
python3 runner.py --mode mock
⸻

OpenAI generation
python3 runner.py --mode openai --model gpt-4o-mini --temperature 0.2
⸻

OpenAI + judge ensemble
python3 runner.py --mode openai --model gpt-4o-mini --temperature 0.2 --enable-judge
⸻

Write baseline
python3 runner.py --mode openai --enable-judge --write-baseline
⸻

Compare runs
python3 regression_compare.py baselines/baseline_results.json results/latest_results.json --max-drop 0.3
⸻

```

## Output artifacts

Each run generates:

- `results/latest_results.json` → latest evaluation snapshot  
- `results/run_<timestamp>.json` → historical run  
- `results/report.csv` → flat table for analysis  

Each result includes:
- heuristic scores
- verdict (PASS / WARN / FAIL)
- optional judge metrics
- evaluation confidence

---

## Design principles

- Deterministic logic governs decisions  
- Judges are **not** decision-makers  
- Disagreement is a signal, not a bug  
- Evaluation itself requires engineering  

---

## Current limitations

- Domain-specific (wine recommendations)  
- Heuristic scoring is simplified  
- Judge depends on OpenAI API  
- Small dataset  

---

## Roadmap

- Judge disagreement visualization  
- Judge reliability testing  
- Cross-model comparison  
- Rubric refinement  
- Evaluation analytics 

## License

MIT