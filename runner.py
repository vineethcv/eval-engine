from __future__ import annotations

import argparse
import csv
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List

from dotenv import load_dotenv

from confidence import compute_confidence
from judge_client import (
    JUDGE_PROMPT_VERSION,
    judge_response_ensemble,
    load_judge_config,
)
from scorer import evaluate_case, evalresult_to_flat_dict
from system_client import build_system_client, SYSTEM_PROMPT_VERSION
from task_loader import load_task_bundle, load_yaml

load_dotenv()

RUBRIC_VERSION = "v1.0"
DATASET_VERSION = "v1.0"


# ----------------------------
# Helpers
# ----------------------------
def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def get_task_thresholds(task_config: Dict[str, Any], rubric: Dict[str, Any]) -> Dict[str, Any]:
    evaluation_cfg = task_config.get("evaluation", {})
    thresholds_cfg = evaluation_cfg.get("thresholds", {})
    if thresholds_cfg.get("source") != "rubric":
        raise ValueError("Unsupported thresholds source in task config.")
    return rubric["thresholds"]


def get_task_judge_ensemble_config(
    task_config: Dict[str, Any], judge_config: Dict[str, Any]
) -> Dict[str, Any]:
    evaluation_cfg = task_config.get("evaluation", {})
    judge_ensemble_cfg = evaluation_cfg.get("judge_ensemble", {})
    if judge_ensemble_cfg.get("source") != "task_judge_config":
        raise ValueError("Unsupported judge ensemble source in task config.")
    return judge_config


def validate_mock_mode_support(system_config: Dict[str, Any]) -> None:
    mock_support = system_config.get("mock_support", {})
    if not mock_support.get("enabled", False):
        raise ValueError("Selected system config does not support mock mode.")


def build_result_record(
    eval_case: Dict[str, Any],
    response: str,
    heuristic_result: Any,
    confidence: float,
    run_metadata: Dict[str, Any],
    judge_result: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    flat_heuristic = evalresult_to_flat_dict(heuristic_result)

    gate_reasons = flat_heuristic.get("gate_reasons")
    if gate_reasons is None:
        gate_reasons = flat_heuristic.get("reasons", [])

    record: Dict[str, Any] = {
        "id": eval_case["id"],
        "query": eval_case["query"],
        "bucket": eval_case.get("bucket"),
        "scenario": eval_case.get("scenario"),
        "response": response,
        "confidence": confidence,
        "generator": {
            "response": response,
        },
        "heuristic_evaluation": {
            "scores": {
                "tasting_clarity": flat_heuristic.get("tasting_clarity"),
                "popularity_alignment": flat_heuristic.get("popularity_alignment"),
                "regional_diversity": flat_heuristic.get("regional_diversity"),
                "language_tone": flat_heuristic.get("language_tone"),
            },
            "weighted_score": flat_heuristic.get("weighted_score"),
            "verdict": flat_heuristic.get("verdict"),
            "gate_pass": flat_heuristic.get("gate_pass"),
            "gate_reasons": gate_reasons,
        },
        "judge_evaluation": judge_result if judge_result else None,
        "run_metadata": run_metadata,
    }

    # Preserve legacy top-level fields for compatibility.
    record.update(flat_heuristic)
    record["confidence"] = confidence

    if judge_result:
        record.update(judge_result)

    return record


def write_json(path: str, data: Any) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def write_csv(path: str, rows: List[Dict[str, Any]]) -> None:
    if not rows:
        return

    keys = rows[0].keys()
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def build_run_metadata(
    args: argparse.Namespace,
    task_config_path: str,
    system_config_path: str,
    judge_config_path: str,
) -> Dict[str, Any]:
    judge_enabled = args.mode == "openai" and args.enable_judge

    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "mode": args.mode,
        "model": args.model,
        "temperature": args.temperature,
        "prompt_version": SYSTEM_PROMPT_VERSION if args.mode == "openai" else "mock_v1",
        "judge_enabled": judge_enabled,
        "judge_runs": 3 if judge_enabled else 0,
        "judge_prompt_version": JUDGE_PROMPT_VERSION if judge_enabled else None,
        "rubric_version": RUBRIC_VERSION,
        "dataset_version": DATASET_VERSION,
        "task_config_path": task_config_path,
        "system_config_path": system_config_path,
        "judge_config_path": judge_config_path,
    }


def compute_judge_summary(
    judge_bundle: Dict[str, Any],
    rubric: Dict[str, Any],
    heuristic_weighted_score: float,
) -> Dict[str, Any]:
    judge_scores = judge_bundle["ensemble_mean_scores"]
    judge_stddev = judge_bundle["ensemble_stddev_scores"]
    judge_individual = judge_bundle["individual_judges"]

    weights = rubric.get("weights", {})
    judge_weighted_score = round(
        sum(judge_scores[k] * weights.get(k, 0) for k in judge_scores),
        2,
    )

    judge_delta = round(
        judge_weighted_score - heuristic_weighted_score,
        2,
    )

    max_stddev = max(judge_stddev.values()) if judge_stddev else 0.0
    if max_stddev < 0.5:
        agreement = "high"
    elif max_stddev < 0.8:
        agreement = "medium"
    else:
        agreement = "low"

    return {
        "judge_scores": judge_scores,
        "judge_weighted_score": judge_weighted_score,
        "judge_stddev": judge_stddev,
        "judge_individual": judge_individual,
        "judge_delta": judge_delta,
        "judge_agreement_level": agreement,
    }


# ----------------------------
# Mock model
# ----------------------------
def mock_system_respond(query: str, task_config: Dict[str, Any]) -> str:
    profile = task_config.get("mock_response_profile", {})
    profile_type = profile.get("type")
    q = query.lower()

    if profile_type == "wine_recommendation":
        triggers = profile.get("adversarial_triggers", [])
        if any(trigger.lower() in q for trigger in triggers):
            return """1. Château Margaux — Bordeaux, France — €120
Elegant and complex with cassis, cedar, and fine tannins.

2. Barolo DOCG — Piedmont, Italy — €45
Firm tannins with cherry, rose, and earthy notes.

3. Rioja Reserva — Rioja, Spain — €30
Smooth and balanced with vanilla, spice, and red fruit."""
        return """1. Bordeaux Blend — Bordeaux, France — €40
Rich blackcurrant, oak, and spice.

2. Chianti Classico — Tuscany, Italy — €25
Cherry, herbs, and bright acidity.

3. Rioja Crianza — Rioja, Spain — €20
Vanilla, red fruit, and soft tannins."""

    raise ValueError(f"Unsupported mock response profile: {profile_type}")


# ----------------------------
# Main
# ----------------------------
def main():
    parser = argparse.ArgumentParser(description="Eval Engine Runner")
    parser.add_argument(
        "--task-config",
        type=str,
        default="configs/tasks/wine.yaml",
        help="Path to task configuration file for the evaluation task",
    )
    parser.add_argument(
        "--system-config",
        type=str,
        default=None,
        help="Optional override path to system-under-test configuration file",
    )
    parser.add_argument(
        "--judge-config",
        type=str,
        default=None,
        help="Optional override path to judge ensemble configuration file",
    )
    parser.add_argument(
        "--mode",
        choices=["mock", "openai"],
        default="mock",
    )
    parser.add_argument("--model", type=str, default=None)
    parser.add_argument("--temperature", type=float, default=None)
    parser.add_argument(
        "--enable-judge",
        action="store_true",
        help="Run LLM judge ensemble (OpenAI mode only).",
    )
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument(
        "--write-baseline",
        action="store_true",
        help="Write baseline to baselines/baseline_results.json",
    )
    args = parser.parse_args()

    task_bundle = load_task_bundle(args.task_config)
    task_config = task_bundle["task_config"]
    dataset = task_bundle["dataset"]
    rubric = task_bundle["rubric"]

    system_config_path = args.system_config or task_config["system_config"]
    judge_config_path = args.judge_config or task_config["judge_config"]

    system_config = load_yaml(system_config_path)
    judge_config = load_judge_config(judge_config_path)
    task_judge_config = get_task_judge_ensemble_config(task_config, judge_config)
    thresholds = get_task_thresholds(task_config, rubric)

    if args.mode == "mock":
        validate_mock_mode_support(system_config)

    if args.limit:
        dataset = dataset[: args.limit]

    ensure_dir("results")
    ensure_dir("baselines")

    run_metadata = build_run_metadata(
        args,
        task_config_path=args.task_config,
        system_config_path=system_config_path,
        judge_config_path=judge_config_path,
    )

    results: List[Dict[str, Any]] = []
    system_client = None

    if args.mode == "openai":
        effective_model = args.model or system_config["model"]
        effective_temperature = args.temperature
        if effective_temperature is None:
            effective_temperature = system_config.get("temperature", 0.0)

        runtime_system_config = dict(system_config)
        runtime_system_config["model"] = effective_model
        runtime_system_config["temperature"] = effective_temperature
        system_client = build_system_client(runtime_system_config)

    for case in dataset:
        query = case["query"]

        # Model response
        if args.mode == "mock":
            response = mock_system_respond(query, task_config)
        elif args.mode == "openai":
            response = system_client.generate(query)
        else:
            raise ValueError(f"Unsupported mode: {args.mode}")

        # Heuristic scoring
        eval_result = evaluate_case(query, response, rubric)
        flat_eval = evalresult_to_flat_dict(eval_result)

        # Judge evaluation
        judge_enabled = args.mode == "openai" and args.enable_judge
        judge_result = None
        if judge_enabled:
            judge_result = judge_response_ensemble(
                query=query,
                response=response,
                rubric=rubric,
                judge_config=task_judge_config,
                model=task_judge_config.get("model", args.model or "gpt-4o-mini"),
                temperature=task_judge_config.get("temperature", 0.0),
            )

        # Confidence
        confidence = compute_confidence(eval_result)

        result_record = build_result_record(
            eval_case=case,
            response=response,
            heuristic_result=eval_result,
            confidence=confidence,
            run_metadata=run_metadata,
            judge_result=judge_result if judge_enabled else None,
        )
        results.append(result_record)

    # Write outputs
    latest_path = "results/latest_results.json"
    write_json(latest_path, {"metadata": run_metadata, "results": results})

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_path = f"results/run_{timestamp}.json"
    write_json(run_path, {"metadata": run_metadata, "results": results})

    csv_path = "results/report.csv"
    write_csv(csv_path, results)

    print("\nSaved results:")
    print(f" - {latest_path}")
    print(f" - {run_path}")
    print(f" - {csv_path}")

    # Baseline
    if args.write_baseline:
        baseline_path = "baselines/baseline_results.json"
        write_json(
            baseline_path,
            {"metadata": run_metadata, "results": results},
        )
        print(f"\nBaseline written to {baseline_path}")


if __name__ == "__main__":
    main()