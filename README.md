# Eval Engine Learning Lab

A minimal, practical evaluation framework for LLM systems and AI application flows.

This project started as a learning lab for evaluating **non-deterministic AI outputs** using a layered approach, and is now being refactored toward a **boilerplate-friendly eval engine**.

It combines:
- deterministic rules (critical gates)
- heuristic scoring
- LLM-as-judge (analytical signal)
- regression comparison

---

## Why this exists

Traditional QA assumes deterministic outputs and exact expected results.

LLM systems and AI applications introduce:
- variable responses
- qualitative output quality
- probabilistic reasoning
- formatting inconsistency
- partial subjectivity in evaluation

This repo demonstrates a practical evaluation architecture to handle that while preserving deterministic control over PASS/FAIL.

---

## Core principle

> Heuristics decide PASS/FAIL. Judges provide analytical insight.

This separation is intentional.

- **Deterministic evaluation** remains the source of truth
- **LLM judges** help analyze quality, disagreement, and rubric clarity
- **Regression comparison** tracks stability across runs

---

## Architecture

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
## Boilerplate direction

The framework is being refactored so that the evaluated system is no longer assumed to be just a single hardcoded LLM prompt.

The intended boilerplate model is:
	•	task config → defines the evaluation task, dataset, rubric, and evaluation behavior
	•	system config → defines the system under test
	•	judge config → defines judge roles, prompts, and rubric anchors

This makes the framework reusable for:
	•	recommendation tasks
	•	support assistant evaluation
	•	agent workflow evaluation
	•	retrieval or RAG response evaluation
	•	other structured AI output evaluation tasks
For extension guidance, see: `docs/boilerplate_extension_guide.md`
⸻

## Current reference example

The current example task is:

Wine recommendation evaluation

This remains the reference task because it demonstrates:
	•	hard constraints
	•	qualitative scoring
	•	useful judge disagreement
	•	adversarial cases
	•	regression comparison

Wine is the example task, not the long-term framework identity.

⸻

## Repo structure

```text
.
├── configs/
│   ├── tasks/
│   │   └── wine.yaml
│   ├── systems/
│   │   └── openai_wine.yaml
│   └── judges/
│       └── default_ensemble.yaml
│
├── dataset.json
├── rubric.json
├── runner.py
├── scorer.py
├── confidence.py
├── system_client.py
├── judge_client.py
├── regression_compare.py
│
├── baselines/
├── results/
├── tests/
├── examples/
│
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
└── LICENSE

```

## Configuration model

1. Task config

Defines:
	•	dataset path
	•	rubric path
	•	evaluation wiring
	•	mock response profile
	•	selected judge ensemble config

Example:
	•	configs/tasks/wine.yaml

2. System config

Defines the system under test:
	•	provider
	•	model
	•	temperature
	•	mock mode support

Example:
	•	configs/systems/openai_wine.yaml

3. Judge config

Defines judge behavior:
	•	model
	•	temperature
	•	role definitions
	•	base prompt
	•	rubric anchors

Example:
	•	configs/judges/default_ensemble.yaml


## Quickstart

### 1. Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Add your OpenAI key:
```env
OPENAI_API_KEY=your_key_here
```
⸻

### Run examples

Mock (no API required)
```bash
python3 runner.py --mode mock
```
⸻

### OpenAI generation
```bash
python3 runner.py --mode openai --model gpt-4o-mini --temperature 0.0
```
⸻

### OpenAI + judge ensemble
```bash
python3 runner.py --mode openai --enable-judge
```
⸻

### Write baseline
```bash
python3 runner.py --mode openai --enable-judge --write-baseline
```
⸻

### Use explicit config paths
```bash
python3 runner.py \
  --mode openai \
  --task-config configs/tasks/wine.yaml \
  --system-config configs/systems/openai_wine.yaml \
  --judge-config configs/judges/default_ensemble.yaml \
  --enable-judge
```
⸻

## Output artifacts

Each run generates:
•	results/latest_results.json → latest evaluation snapshot
•	results/run_<timestamp>.json → historical run
•	results/report.csv → flat analysis table

Each result includes:
•	generator output
•	heuristic evaluation
•	optional judge evaluation
•	run metadata
•	compatibility fields for regression comparison

---
## Evaluation layers

### Critical gates

Hard constraints that must not be violated.

Examples in the wine task:
	•	exact item count
	•	red wine constraint
	•	max price

### Heuristic scoring

Deterministic scoring across defined dimensions.

Current wine rubric dimensions:
	•	tasting_clarity
	•	popularity_alignment
	•	regional_diversity
	•	language_tone

### Judge ensemble

LLM judges provide analytical signal only.

Current roles:
	•	balanced evaluator
	•	strict evaluator
	•	usefulness evaluator

Judges help surface:
	•	disagreement
	•	ambiguity
	•	rubric weaknesses
	•	heuristic blind spots

⸻

## Regression comparison
Use regression comparison to check whether a latest run regressed against a baseline.

Example:
```bash
python3 regression_compare.py baselines/baseline_results.json results/latest_results.json --max-drop 0.3
```
The comparator supports both:
	•	legacy flat result fields
	•	standardized nested evaluation result structure

---

## Design principles

•	deterministic logic governs decisions
•	judges are analytical, not operational
•	disagreement is useful
•	evaluation requires engineering discipline
•	simplicity is intentional

---

## Current reference example

The current example task is:

**Wine recommendation evaluation**

This remains the reference task because it demonstrates:
- hard constraints
- qualitative scoring
- useful judge disagreement
- adversarial cases
- regression comparison

Wine is the example task, not the long-term framework identity.
See also: `docs/examples/wine_recommendation.md`
---

## Roadmap direction

Near-term boilerplate refactor goals:
	•	keep wine as the example task
	•	make task/system/judge configuration first-class
	•	support reusable evaluation structure across domains
	•	preserve regression safety and offline mock mode

Longer-term exploration:
	•	judge disagreement visualization
	•	judge reliability experiments
	•	cross-model comparison
	•	rubric refinement
	•	evaluation analytics

## License

MIT