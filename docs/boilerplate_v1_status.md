# Boilerplate V1 Status

This document captures the current status of the Eval Engine boilerplate refactor.

The project began as a domain-specific learning lab centered on wine recommendation evaluation. The current refactor moves it toward a reusable boilerplate structure while intentionally preserving the original design philosophy.

---

## Current status

The repo now supports a config-driven structure with three main layers:

- task config
- system config
- judge config

The current reference implementation remains the wine recommendation task.

This is intentional.

The project is now in a hybrid state:
- **more reusable than the original learning-lab version**
- **not yet fully domain-agnostic**

That is acceptable for Boilerplate V1.

---

## What Boilerplate V1 now supports

### Config-driven wiring
The evaluation flow is now wired through:
- `configs/tasks/...`
- `configs/systems/...`
- `configs/judges/...`

### Pluggable system-under-test concept
The old LLM-specific naming has been shifted toward a more general system-under-test abstraction.

### Configurable judge perspectives
Judge roles are now represented as configurable evaluation perspectives rather than only hardcoded variants.

### Standardized result schema
Run results now include structured sections for:
- generator output
- heuristic evaluation
- judge evaluation
- run metadata

### Backward compatibility safeguards
Compatibility has been intentionally preserved through:
- legacy top-level result fields
- regression comparison support for both old and new result shapes
- continued mock mode support

---

## What remains intentionally task-specific

Boilerplate V1 still contains task-specific assumptions in these areas:

- scorer implementation
- response parsing logic
- wine-oriented generator prompt
- current judge JSON score dimensions
- rubric anchors

This is expected and acceptable at this stage.

The framework structure is more generic now, even though the example implementation remains domain-shaped.

---

## Design rules preserved

The refactor did **not** change the core evaluation philosophy.

These rules still hold:

1. Heuristics decide PASS / WARN / FAIL
2. Judges remain analytical only
3. Mock mode remains offline-safe
4. Regression comparison remains a first-class safety mechanism
5. Simplicity is preferred over premature generalization

---

## Recommended next step after Boilerplate V1

The next logical step is not a large refactor.

Instead, the best next step is to add **one more example task** using the same structure.

Good candidates:
- customer support response evaluation
- retrieval QA / RAG answer evaluation
- simple agent task completion evaluation

This would validate whether the current boilerplate shape is genuinely reusable without overcomplicating the framework.

---

## Summary

Boilerplate V1 is complete enough to serve as:

- a reusable starting point
- a learning-oriented evaluation reference
- a small public-facing framework example
- a foundation for a second domain example

It should be treated as:
- structurally improved
- backward-compatible
- intentionally still simple