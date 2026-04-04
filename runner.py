from __future__ import annotations
from dotenv import load_dotenv

load_dotenv()

import argparse
import csv
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List

from confidence import compute_confidence
from llm_client import respond_openai, PROMPT_VERSION
from judge_client import judge_response_ensemble, JUDGE_PROMPT_VERSION
from scorer import evaluate_case, evalresult_to_flat_dict

RUBRIC_VERSION = "v1.0"
DATASET_VERSION = "v1.0"


# ----------------------------
# Helpers
# ----------------------------

def load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


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


def build_run_metadata(args: argparse.Namespace) -> Dict[str, Any]:
    judge_enabled = args.mode == "openai" and args.enable_judge
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "mode": args.mode,
        "model": args.model,
        "temperature": args.temperature,
        "prompt_version": PROMPT_VERSION if args.mode == "openai" else "mock_v1",
        "judge_enabled": judge_enabled,
        "judge_runs": 3 if judge_enabled else 0,
        "judge_prompt_version": JUDGE_PROMPT_VERSION if judge_enabled else None,
        "rubric_version": RUBRIC_VERSION,
        "dataset_version": DATASET_VERSION,
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

def mock_llm_respond(query: str) -> str:
    q = query.lower()

    if "100" in q or "premium" in q:
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


# ----------------------------
# Main
# ----------------------------

def main():
    parser = argparse.ArgumentParser(description="Eval Engine Runner")

    parser.add_argument("--dataset", default="dataset.json")
    parser.add_argument("--rubric", default="rubric.json")

    parser.add_argument(
        "--mode",
        choices=["mock", "openai"],
        default="mock",
    )

    parser.add_argument("--model", default="gpt-4o-mini")
    parser.add_argument("--temperature", type=float, default=0.0)
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

    dataset = load_json(args.dataset)
    rubric = load_json(args.rubric)

    if args.limit:
        dataset = dataset[: args.limit]

    ensure_dir("results")
    ensure_dir("baselines")

    run_metadata = build_run_metadata(args)

    results: List[Dict[str, Any]] = []

    for case in dataset:
        query = case["query"]

        # Model response
        if args.mode == "mock":
            response = mock_llm_respond(query)
        else:
            response = respond_openai(
                query=query,
                model=args.model,
                temperature=args.temperature,
            )

        # Heuristic scoring
        eval_result = evaluate_case(query, response, rubric)
        flat_eval = evalresult_to_flat_dict(eval_result)

        # Judge evaluation
        judge_enabled = args.mode == "openai" and args.enable_judge

        if judge_enabled:
            judge_bundle = judge_response_ensemble(
                query=query,
                response=response,
                rubric=rubric,
                model=args.model,
            )

            judge_summary = compute_judge_summary(
                judge_bundle,
                rubric,
                flat_eval["weighted_score"],
            )
        else:
            judge_summary = {
                "judge_scores": None,
                "judge_weighted_score": None,
                "judge_stddev": None,
                "judge_individual": [],
                "judge_delta": None,
                "judge_agreement_level": None,
            }

        # Confidence
        confidence = compute_confidence(eval_result)

        result = {
            "id": case["id"],
            "query": query,
            "response": response,
            **flat_eval,
            **judge_summary,
            "confidence": confidence,
        }

        results.append(result)

    # Write outputs
    latest_path = "results/latest_results.json"
    write_json(latest_path, {"metadata": run_metadata, "results": results})

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_path = f"results/run_{timestamp}.json"
    write_json(run_path, {"metadata": run_metadata, "results": results})

    csv_path = "results/report.csv"
    write_csv(csv_path, results)

    print(f"\nSaved results:")
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