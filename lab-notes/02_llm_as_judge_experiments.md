# LLM-as-Judge Experiments

Author: Vineeth C. Vijayan  
Project: Eval Engine Learning Lab  
Phase: LLM-as-Judge Evaluation

---

# Motivation

The initial evaluation harness relied on **heuristic scoring**.

Pipeline before this phase:

Dataset → Model → Critical Gates → Heuristic Scoring → Verdict → Baseline Comparison

Heuristic scoring has several advantages:

- deterministic
- stable
- inexpensive
- easy to debug

However, heuristics also have clear limitations:

- limited ability to interpret nuanced language
- difficulty capturing qualitative qualities (tone, clarity, usefulness)
- brittle rule logic when responses change format
- hard to capture human-like judgment

This motivated the exploration of **LLM-as-Judge evaluation**.

The goal was **not to replace heuristics**, but to introduce an **additional analytical evaluator**.

---

# Architectural Decision

A key design decision was made early:

The judge system should **not determine PASS/FAIL**.

Instead:

Heuristic scoring → operational decision
LLM judge → analytical signal

This prevents circular logic such as:

LLM → evaluated by another LLM → determines system correctness

Instead, the judge provides:

- qualitative insight
- disagreement detection
- rubric refinement signals
- evaluator perspective diversity

The operational governance layer remains **deterministic**.

---

# First Implementation: Single Judge

A new module was introduced:

The judge receives:

- user query
- model response
- rubric definition

The judge then scores the following dimensions:

- tasting_clarity
- popularity_alignment
- regional_diversity
- language_tone

Example output:

```json
{
  "tasting_clarity": 4,
  "popularity_alignment": 5,
  "regional_diversity": 3,
  "language_tone": 4,
  "reasoning": "The tasting notes are clear and detailed and the wines are widely recognized."
}

A critical constraint was enforced: temperature = 0

This ensured deterministic judging behavior.

---

# Observation: Score Inflation

Initial results showed the judge frequently assigning high scores:

Example:
{
  "tasting_clarity": 5,
  "popularity_alignment": 4,
  "regional_diversity": 4,
  "language_tone": 5
}

This revealed a known phenomenon in LLM evaluation:

evaluation inflation

LLMs tend to be generous evaluators unless explicitly instructed otherwise.

---

# Judge Calibration

To reduce score inflation, the judge prompt was calibrated.

Calibration techniques included:
	•	explicit scoring anchors
	•	discouraging high scores
	•	stating that scores of 5 should be rare
	•	emphasizing conservative evaluation behavior

Example scoring anchors introduced:
tasting_clarity
1 = no tasting description
2 = very generic description
3 = some sensory detail
4 = clear tasting notes
5 = vivid sensory description

After calibration, judge scoring became more realistic.

Example calibrated output:
{
  "tasting_clarity": 4,
  "popularity_alignment": 5,
  "regional_diversity": 3,
  "language_tone": 4
}

This brought judge scoring closer to heuristic scoring.

⸻

# Judge vs Heuristic Comparison

The system now records both evaluation paths:

heuristic_weighted_score
judge_weighted_score
judge_delta

Example:
heuristic_score: 4.00
judge_score: 4.17
judge_delta: +0.17

Interpretation:

Judges are slightly more generous than heuristics, but broadly aligned.

Tracking the delta helps identify where heuristics may miss nuance.

⸻

# Multi-Judge Ensemble

A single judge can still introduce bias.

To improve evaluation reliability, an ensemble of judges was introduced.

Implementation:

Three judge evaluations using the same model but different prompt variants.

Judge A — Balanced evaluator
Judge B — Conservative critic
Judge C — Recommendation usefulness evaluator

The ensemble computes:
	•	mean score
	•	standard deviation
	•	individual judge outputs

Example result:
judge_scores:
  tasting_clarity: 4
  popularity_alignment: 5
  regional_diversity: 3
  language_tone: 4.33

judge_stddev:
  tasting_clarity: 0.816
  popularity_alignment: 0.0
  regional_diversity: 0.0
  language_tone: 0.471

⸻

Interpreting Judge Disagreement

Key observation:

Objective dimensions tend to converge.

These include:
	•	popularity_alignment
	•	regional_diversity

Subjective dimensions tend to show variance.

These include:
	•	tasting_clarity
	•	language_tone

Example disagreement:
Judge A: tasting_clarity = 4
Judge B: tasting_clarity = 3
Judge C: tasting_clarity = 5

This variance reveals rubric interpretation differences.

⸻

Agreement Signal

A derived signal was introduced:
judge_agreement_level

Rules:
stddev < 0.5  → high agreement
stddev < 0.8  → medium agreement
otherwise     → low agreement

Example:
max stddev = 0.816
agreement_level = low

This indicates strong disagreement among judges on at least one dimension.

⸻

Key Insight

The most valuable signal from the judge system is not the score itself, but:
	•	disagreement between judges
	•	disagreement between judge and heuristic scoring

These disagreements highlight areas where:
	•	the rubric may be unclear
	•	heuristics may be insufficient
	•	responses are ambiguous

This provides valuable signals for improving the evaluation system.

⸻

Current Evaluation Architecture

The evaluation pipeline now includes multiple evaluation layers:

Dataset
   ↓
Model Response
   ↓
Critical Gates
   ↓
Heuristic Scoring
   ↓
Judge Ensemble
   ↓
Judge Variance
   ↓
Judge vs Heuristic Delta
   ↓
Baseline Regression

This creates a layered evaluation system combining:
	•	deterministic evaluators
	•	probabilistic evaluators

⸻

Next Experiments

Planned explorations:
	1.	Judge temperature experiments
	2.	Judge reliability across repeated runs
	3.	Visualization of judge disagreement patterns across runs

The next step will focus on visualizing judge disagreement patterns to better understand evaluation dynamics.

⸻

Reflection

A key realization during this phase:

Evaluation of LLM systems requires careful prompt engineering for evaluators themselves.

Designing a good judge prompt requires as much attention to detail as designing the original system prompt.

In other words:

Evaluating LLMs is itself an LLM engineering problem.