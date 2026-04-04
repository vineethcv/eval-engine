# Boilerplate Extension Guide

This guide explains how to extend the eval engine boilerplate beyond the current wine recommendation reference task.

The framework is being refactored so that a task can define:
- what is being evaluated
- how outputs are scored
- how judges evaluate quality
- which system under test is called

The current repo still contains some task-specific assumptions, but the structure is now ready for gradual generalization.

---

## 1. Extension model

There are three main configuration layers:

### Task config
Defines the evaluation task:
- dataset path
- rubric path
- evaluation wiring
- mock response profile
- selected judge config

### System config
Defines the system under test:
- provider
- model
- temperature
- mock support

### Judge config
Defines analytical judge behavior:
- judge roles
- prompt instructions
- scoring anchors
- judge model and temperature

Together, these make the evaluation flow reusable.

---

## 2. Adding a new task

To add a new domain, start by creating a new task config.

Example:
- `configs/tasks/customer_support.yaml`

A task config should define:
- dataset source
- rubric source
- evaluation behavior
- selected system config
- selected judge config

Typical sequence:
1. create a dataset
2. define a rubric
3. create a task config
4. connect system and judge configs
5. adjust the scorer if the dimensions differ from the current example

---

## 3. Adding a new dataset

A dataset should contain evaluation cases.

Suggested fields:
- `id`
- `query`
- `bucket`
- `scenario`

You can add more fields later if needed, such as:
- expected policy
- user segment
- locale
- product area
- risk level

Keep the first version simple.

---

## 4. Adding a new rubric

A rubric defines:
- critical gates
- scoring weights
- thresholds

The current wine rubric is domain-specific, but future rubrics can be adapted to other tasks.

Examples for other domains:

### Customer support
Possible dimensions:
- policy_compliance
- resolution_quality
- empathy_tone
- clarity

### RAG / retrieval QA
Possible dimensions:
- answer_relevance
- grounding
- completeness
- clarity

### Agent workflows
Possible dimensions:
- task_completion
- instruction_following
- tool_use_quality
- communication_quality

Keep deterministic gates separate from qualitative scoring.

---

## 5. Adding a new system under test

The current implementation supports an OpenAI-backed system client plus mock mode.

Future systems could include:
- HTTP app endpoints
- RAG pipelines
- local models
- agent coordinators
- internal orchestration flows

To extend this:
1. add a new provider type in `system_client.py`
2. create a matching system config
3. keep the `generate(query)` interface stable

The key design rule is:
the runner should interact with a generic system client, not with provider-specific code.

---

## 6. Adding new judge roles

Judge roles allow multiple evaluation perspectives over the same output.

Current example roles:
- balanced
- strict
- usefulness

New roles could include:
- safety
- compliance
- empathy
- domain_expert
- brand_tone
- factuality
- retrieval_grounding

A new judge role should define:
- a role name
- a prompt key
- an instruction

In the current config structure, this lives in the judge config YAML.

---

## 7. Writing judge prompts

Judge prompts should be built from three layers:

### Base prompt
Defines the stable judging contract:
- output format
- scoring format
- constraints
- evidence discipline

### Role instruction
Defines the evaluation perspective:
- strict
- balanced
- usefulness
- etc.

### Rubric anchors
Defines what high/medium/low performance means for each dimension.

This keeps judging more stable and reduces score inflation.

Important:
judge prompts should remain analytical.
They should not become the source of operational PASS/FAIL.

---

## 8. When to update the scorer

The scorer should be updated when:
- rubric dimensions change
- parsing assumptions change
- critical gate logic changes
- verdict logic changes

The scorer is still the main deterministic decision layer.

The framework should continue to preserve this rule:

> Judges analyze. Heuristics decide.

---

## 9. Recommended extension order

When introducing a new task, use this order:

1. dataset
2. rubric
3. task config
4. system config
5. judge config
6. scorer adjustments
7. mock support
8. baseline generation
9. regression comparison

This keeps the evolution controlled and testable.

---

## 10. Keep the first version small

When adding a new task:
- start with a small dataset
- use a small number of dimensions
- keep gates simple
- keep output schema stable
- prefer clarity over flexibility

The boilerplate should stay understandable.

---

## 11. Long-term direction

As the boilerplate matures, task-specific logic can move further out of core code and into:
- configs
- prompt templates
- task modules
- reusable scorer adapters

For now, the repo should prioritize:
- clarity
- small steps
- regression safety
- explicit configuration