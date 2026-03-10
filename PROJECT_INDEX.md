# Eval Engine Learning Lab — Project Index

Author: Vineeth C. Vijayan

This file acts as the navigation layer for the evaluation lab project.
It explains where different types of information live so that reasoning
can reference the correct files.

---

# 1. Project Context

File:
Project Context.md

Contains the architectural overview of the evaluation system including:

- problem statement
- evaluation philosophy
- pipeline architecture
- system components
- rubric and dataset design
- long-term vision

Use this file when understanding the **overall system design**.

---

# 2. Current System State

File:
SESSION_STATE.md

Contains the current progress snapshot:

- completed phases
- current evaluation capabilities
- latest results
- immediate next task

Use this file to understand **what stage the project is currently in**.

---

# 3. Experiment Logs

Location:
lab-notes/

These documents record the development journey and experiments.

Current notes:

01_eval_engine_journey.md
02_llm_as_judge_experiments.md

These include:

- design decisions
- observations
- experiments performed
- lessons learned

Use these files when understanding **how the system evolved**.

---

# 4. Roadmap

File:
NEXT_STEPS_HIGH_LEVEL.md

Contains the high-level roadmap of upcoming experiments.

The roadmap currently includes:

1. Visualize judge disagreement patterns
2. Judge temperature experiments
3. Judge reliability across repeated runs
4. Cross-model judge comparison
5. Rubric improvements
6. Evaluation analytics
7. Visualization dashboard

Use this file when determining **the next development step**.

---

# 5. Evaluation Code Structure

Core files:

runner.py
scorer.py
judge_client.py
confidence.py
regression_compare.py

These implement the evaluation pipeline.

Primary execution entrypoint:
runner.py

---

# 6. Data Files

dataset.json
rubric.json

These define the evaluation inputs and scoring rules.

---

# 7. Result Artifacts

Location:
results/

Outputs from evaluation runs:

latest_results.json
run_<timestamp>.json
report.csv

These contain raw evaluation outputs for analysis.

---

# 8. Baselines

Location:
baselines/

Stores reference evaluation results used for regression detection.

---

# Working Principle

The project intentionally separates:

System documentation → Project Context.md  
Current status → SESSION_STATE.md  
Experiment narrative → lab-notes/  
Future roadmap → NEXT_STEPS_HIGH_LEVEL.md  

This keeps reasoning structured even as the project grows.

---

# Current Focus

Phase 3 — LLM-as-Judge evaluation

Immediate next task:

Visualize judge disagreement patterns across runs.