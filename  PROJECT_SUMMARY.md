# Eval Engine Learning Lab — Project Summary (Boilerplate V1)

## Purpose

This project is a lightweight evaluation framework for LLM systems and AI application flows.

It began as a **learning lab** for exploring how to evaluate non-deterministic AI outputs using a combination of:

- deterministic validation (rules)
- heuristic scoring (structured signals)
- LLM-as-judge (analytical signal)
- regression comparison (stability tracking)

It has now been refactored into a **Boilerplate V1** shape so the same architecture can be reused across future evaluation tasks while keeping the codebase intentionally small and understandable.

The goal is still not to build a production-grade platform yet, but to understand and demonstrate **evaluation design principles for AI systems**.

---

## Core Problem

Traditional QA assumes:
- deterministic outputs
- exact expected results

LLM systems and broader AI application flows introduce:
- variability in responses
- qualitative outputs
- probabilistic reasoning
- formatting inconsistencies
- partial subjectivity in evaluation

This makes simple pass/fail testing insufficient.

---

## Evaluation Approach

This project uses a **layered evaluation architecture**:

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

## Key Design Principles

### 1. Deterministic logic governs decisions
- PASS / WARN / FAIL is decided **only by heuristics**
- ensures stability and reproducibility

### 2. LLM judges are analytical signals
- judges DO NOT decide correctness
- they provide:
  - qualitative insight
  - disagreement signals
  - rubric feedback

### 3. Disagreement is valuable
- variance between judges highlights:
  - ambiguity in outputs
  - weaknesses in rubric
  - subjective dimensions

### 4. Evaluation requires engineering
- prompts, rubrics, and scoring logic all require careful design
- evaluation is not trivial or secondary work

### 5. Simplicity is intentional
- the repo is intentionally lightweight
- backward-compatible evolution is preferred over over-engineering
---

## Current Capabilities (Boilerplate V1)

## Config-driven architecture

The framework now uses three main configuration layers:
•	task config
  •	dataset path
  •	rubric path
  •	evaluation wiring
  •	mock response profile
  •	selected judge config
•	system config
  •	system-under-test provider
  •	model
  •	temperature
  •	mock support
•	judge config
  •	judge roles
  •	base prompt
  •	role instructions
  •	rubric anchors
  •	judge model / temperature

This is the main architectural shift from the original learning-lab version.

### Dataset
•	Currently stored in dataset.json
•	~10 curated evaluation cases
•	Current fields include:
  •	id
  •	query
  •	bucket
  •	scenario

The current reference dataset remains wine-focused.

### Rubric
- Located in `rubric.json`
- Defines:
  - critical gates:
    - exact item count
    - max price
    - red wine constraint
  - weighted scoring:
    - tasting_clarity
    - popularity_alignment
    - regional_diversity
    - language_tone
  - verdict thresholds

### System Client (system_client.py)
•	generalized from the old LLM-specific naming
•	represents the system under test
•	currently supports:
  •	OpenAI-backed generation
  •	mock-safe local execution path

This is intended to be extended later for other AI application types.

### Judge Client (judge_client.py)
•	supports config-driven multi-judge evaluation
•	current judge roles:
  •	balanced evaluator
  •	strict evaluator
  •	usefulness evaluator
•	supports:
  •	base prompt + role overlay structure
  •	rubric anchors from config
  •	per-dimension judge scoring
  •	judge standard deviation
  •	judge agreement level

### Heuristic Scorer (`scorer.py`)
- deterministic evaluation
- responsible for:
  - parsing response
  - validating constraints
  - computing scores
  - assigning verdict

### Confidence Signal (`confidence.py`)
- estimates reliability of evaluation
- penalizes:
  - weak parsing
  - missing data
  - borderline scores

### Runner (`runner.py`)
- orchestrates full pipeline
- supports:
  - mock mode (offline)
  - openai mode
  - optional judge execution (`--enable-judge`)
  - config-driven task/system/judge wiring
  - baseline writing
- outputs:
  - JSON results
  - CSV report

### Regression Comparison (`regression_compare.py`)
•	compares baseline vs latest run
•	supports:
  •	legacy flat result fields
  •	standardized nested result schema
•	detects:
  •	missing cases
  •	gate regressions
  •	score drops
  •	verdict regressions

---

## Output Schema

Each result now includes structured sections such as:
•	generator
•	heuristic_evaluation
•	judge_evaluation
•	run_metadata

Legacy top-level fields are still preserved for compatibility with regression and existing tooling.

---
## Boilerplate Refactor Outcome

The project is now in a hybrid but useful state:
•	more reusable than the original domain-specific learning-lab version
•	not yet fully domain-agnostic

That is acceptable for Boilerplate V1.

### What is now more generic
•	config-driven task/system/judge wiring
•	system-under-test abstraction
•	judge role abstraction
•	prompt template scaffolding
•	standardized run result shape
•	regression support across old and new result schemas

### What remains intentionally task-specific
•	wine-oriented reference task
•	scorer dimensions
•	parsing assumptions
•	generator prompt content
•	judge JSON dimension keys
•	rubric anchors

This is expected at this stage.

⸻

## Current Reference Example

The framework still uses wine recommendation evaluation as the reference example task.

This remains useful because it demonstrates:
•	hard constraints
•	qualitative scoring
•	adversarial prompts
•	subjective judge disagreement
•	regression comparison

Wine should be treated as the canonical example task, not the long-term identity of the framework.

⸻

## What Works Well
•	Clean separation of deterministic vs probabilistic evaluation
•	Config-driven structure is now in place
•	Judge disagreement provides meaningful analytical signals
•	Regression comparison remains simple and effective
•	Offline-safe execution remains intact
•	Boilerplate refactor stayed incremental and backward-compatible
•	Public-repo CI path is now aligned with GitHub-hosted runners

⸻

## Known Limitations
•	The reference implementation is still domain-shaped
•	Heuristic scoring is simplistic
•	Parsing is regex-based and brittle
•	Judge depends on external API
•	Small dataset limits coverage
•	Full domain genericity is not complete yet

⸻

## Important Constraints (Do Not Break)

When extending this project:

1. **Do NOT let LLM judges decide PASS/FAIL**
   - this breaks evaluation integrity

2. **Keep heuristic scoring as the source of truth**

3. **Keep mock mode fully offline**
   - no API dependency

4. **Maintain output schema stability**
   - regression comparison depends on it

5. **Avoid over-engineering**
   - simplicity is intentional

⸻

## CI / Workflow Status

The project workflows have been updated for public-repo readiness:
•	no dependency on self-hosted runners
•	GitHub-hosted runner flow for smoke and mock eval execution
•	mock-mode-friendly CI path retained

This keeps the public repo simpler and safer to run.

⸻

## Suggested Next Step

The next best validation step is not a large refactor.

Instead, the strongest next move would be to add one more example task using the same boilerplate structure, such as:
•	customer support response evaluation
•	retrieval QA / RAG answer evaluation
•	simple agent task completion evaluation

That would test whether Boilerplate V1 is genuinely reusable without making the framework too abstract too early.

⸻

## How to Use This File (For Future AI Assistants)

This file provides:
•	project purpose
•	architecture
•	constraints
•	current system shape
•	design philosophy
•	known limitations

When modifying the project:
•	prioritize consistency with the current architecture
•	preserve deterministic vs analytical separation
•	protect backward compatibility where practical
•	avoid introducing judge-driven operational decisions

⸻

## Status

Boilerplate V1 complete:
•	config-driven structure in place
•	system/judge abstractions introduced
•	standardized result schema added
•	regression comparison compatibility preserved
•	public-repo workflow path updated
•	reference example retained

Next phase:
•	validate reusability with a second task
•	continue analysis and insight work, not large infrastructure expansion