# Wine Recommendation Reference Task

This document describes the current reference example task used in the eval engine boilerplate refactor.

The wine recommendation task is intentionally kept as the first example because it demonstrates a useful mix of:
- hard constraints
- qualitative scoring
- subjective evaluation dimensions
- adversarial prompts
- regression comparison

It is a strong example task even though the framework is being generalized.

---

## Purpose of the example

The current system evaluates responses to wine recommendation prompts such as:

- Recommend 3 red wines under 50 euros.
- Recommend 3 Italian red wines under 50 euros.
- Recommend 3 red wines under 50 euros for steak dinner.

This domain works well for evaluation experimentation because the outputs are not fully deterministic, but they still contain testable structure.

---

## Why this is a good reference example

### 1. Hard constraints are easy to express
The task includes clear constraints such as:
- exactly 3 items
- must be red wines
- must remain under a maximum price

This makes it ideal for demonstrating critical gates.

### 2. Quality dimensions are still subjective
The task also contains qualitative dimensions such as:
- tasting clarity
- popularity alignment
- regional diversity
- language tone

This makes it useful for showing how heuristic scoring and LLM judges can coexist.

### 3. It supports adversarial cases
The dataset includes prompts that attempt to pull the system outside the allowed constraints.

Example:
- include one option around 100 euros

This helps demonstrate why hard gates must remain separate from softer evaluation signals.

### 4. The outputs are human-readable
The responses are easy to inspect manually, which makes the task practical for debugging and learning.

---

## Current dataset structure

The dataset currently contains:
- happy path cases
- filter variations
- contextual preference cases
- explicit constraint cases
- adversarial cases

Example fields:
- `id`
- `query`
- `bucket`
- `scenario`

This structure is simple enough for a learning lab, but already useful for later analysis.

---

## Current rubric dimensions

The current heuristic rubric uses:

- `tasting_clarity`
- `popularity_alignment`
- `regional_diversity`
- `language_tone`

The current critical gates use:

- exact item count
- red wine constraint
- max price

These dimensions are specific to the example task, not intended as universal framework dimensions.

---

## Current judge roles

The current judge ensemble includes three evaluation perspectives:

- balanced evaluator
- strict evaluator
- usefulness evaluator

These roles are meant to demonstrate multi-judge analysis, disagreement, and rubric interpretation variance.

They are also example roles, not universal boilerplate defaults for every future task.

---

## What this example proves

The wine recommendation task proves that the framework can support:

- deterministic gates
- deterministic quality scoring
- config-driven judge roles
- analytical LLM judging
- regression comparison
- mock mode and online mode

That makes it a good first reference implementation for the boilerplate.

---

## What stays task-specific for now

The following parts are still specific to the wine example:

- system generation prompt
- scorer dimensions
- response parsing assumptions
- judge JSON output keys
- rubric anchors

These are expected to evolve later as the boilerplate becomes more generic.

---

## Long-term role of this example

Wine recommendation should remain in the repo as:

- a reference task
- a demo task
- a regression-safe example
- a simple onboarding example for future contributors

It should not define the identity of the framework, but it should remain the canonical example of how to plug a task into the framework.