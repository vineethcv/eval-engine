# Eval Engine Learning Lab — Project Summary (V1)

## Purpose

This project is a lightweight evaluation framework for LLM systems.

It was built as a **learning lab** to explore how to evaluate non-deterministic AI outputs using a combination of:

- deterministic validation (rules)
- heuristic scoring (structured signals)
- LLM-as-judge (analytical signal)
- regression comparison (stability tracking)

The goal is not to build a production system, but to understand **evaluation design principles for AI systems**.

---

## Core Problem

Traditional QA assumes:
- deterministic outputs
- exact expected results

LLM systems introduce:
- variability in responses
- qualitative outputs
- probabilistic reasoning
- formatting inconsistencies

This makes simple pass/fail testing insufficient.

---

## Evaluation Approach

This project uses a **layered evaluation architecture**:

## Architecture


```text
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

---

## Current Capabilities (V1)

### Dataset
- Located in `dataset.json`
- ~10 curated test cases
- Covers:
  - happy path
  - constraints
  - filters
  - adversarial input

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

### LLM Client (`llm_client.py`)
- generates responses using OpenAI
- constrained prompt to reduce variability

### Judge Client (`judge_client.py`)
- multi-judge ensemble (3 variants):
  - balanced evaluator
  - strict critic
  - usefulness evaluator
- outputs:
  - per-dimension scores
  - mean score
  - standard deviation
  - individual judge outputs

### Runner (`runner.py`)
- orchestrates full pipeline
- supports:
  - mock mode (offline)
  - openai mode
  - optional judge execution (`--enable-judge`)
  - baseline writing
- outputs:
  - JSON results
  - CSV report

### Regression Comparison (`regression_compare.py`)
- compares baseline vs latest run
- detects:
  - missing cases
  - gate regressions
  - score drops
  - verdict regressions

---

## Output Schema

Each result includes:

- heuristic scores
- weighted_score
- verdict (PASS / WARN / FAIL)
- gate_pass + reasons
- optional judge metrics:
  - judge_scores
  - judge_weighted_score
  - judge_stddev
  - judge_delta
  - judge_agreement_level
- confidence

---

## What Works Well

- Clean separation of deterministic vs probabilistic evaluation
- Judge disagreement provides meaningful signals
- Simple but effective regression detection
- Offline-safe execution (mock mode)
- Small, understandable codebase

---

## Known Limitations

- Domain-specific (wine recommendations)
- Heuristic scoring is simplistic
- Parsing is regex-based (not robust)
- Judge depends on external API
- Small dataset limits coverage

---

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

---

## Suggested Future Directions

- Visualization of judge disagreement
- Judge reliability testing (multiple runs)
- Cross-model judge comparison
- Rubric refinement based on judge signals
- Larger and more diverse dataset
- Better parsing (structured extraction)

---

## How to Use This File (For Future AI Assistants)

This file provides:
- system intent
- architecture
- constraints
- design philosophy

When modifying the project:
- prioritize consistency with existing architecture
- avoid introducing conflicting evaluation logic
- preserve deterministic vs analytical separation

---

## Status

V1 complete:
- evaluation pipeline stable
- judge ensemble integrated
- regression comparison working
- repo structured and published

Next phase:
- analysis and insight, not infrastructure