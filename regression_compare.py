from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, List


def load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_results(payload: Any) -> List[Dict[str, Any]]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        if "results" in payload and isinstance(payload["results"], list):
            return payload["results"]
    raise TypeError("Expected results payload to be a list or a dict containing a 'results' list.")


def get_case_map(results: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    return {row["id"]: row for row in results}


def get_weighted_score(row: Dict[str, Any]) -> float:
    if "weighted_score" in row:
        return float(row["weighted_score"])

    heuristic = row.get("heuristic_evaluation", {})
    if "weighted_score" in heuristic:
        return float(heuristic["weighted_score"])

    raise KeyError(f"weighted_score not found for row id={row.get('id')}")


def get_verdict(row: Dict[str, Any]) -> str:
    if "verdict" in row:
        return str(row["verdict"])

    heuristic = row.get("heuristic_evaluation", {})
    if "verdict" in heuristic:
        return str(heuristic["verdict"])

    raise KeyError(f"verdict not found for row id={row.get('id')}")


def get_gate_pass(row: Dict[str, Any]) -> bool:
    if "gate_pass" in row:
        return bool(row["gate_pass"])

    heuristic = row.get("heuristic_evaluation", {})
    if "gate_pass" in heuristic:
        return bool(heuristic["gate_pass"])

    raise KeyError(f"gate_pass not found for row id={row.get('id')}")


def compare_results(
    baseline: List[Dict[str, Any]],
    latest: List[Dict[str, Any]],
    max_drop: float,
) -> int:
    baseline_map = get_case_map(baseline)
    latest_map = get_case_map(latest)

    exit_code = 0

    missing_cases = sorted(set(baseline_map.keys()) - set(latest_map.keys()))
    if missing_cases:
        print("ERROR: Missing cases in latest run:")
        for case_id in missing_cases:
            print(f" - {case_id}")
        exit_code = 1

    for case_id, base_row in baseline_map.items():
        if case_id not in latest_map:
            continue

        latest_row = latest_map[case_id]

        base_gate_pass = get_gate_pass(base_row)
        latest_gate_pass = get_gate_pass(latest_row)
        if base_gate_pass and not latest_gate_pass:
            print(f"ERROR: Gate regression for {case_id}")
            exit_code = 1

        base_score = get_weighted_score(base_row)
        latest_score = get_weighted_score(latest_row)
        score_drop = round(base_score - latest_score, 2)

        if score_drop > max_drop:
            print(
                f"ERROR: Score drop too large for {case_id} "
                f"(baseline={base_score}, latest={latest_score}, drop={score_drop})"
            )
            exit_code = 1

        base_verdict = get_verdict(base_row)
        latest_verdict = get_verdict(latest_row)
        verdict_rank = {"FAIL": 0, "WARN": 1, "PASS": 2}

        if verdict_rank.get(latest_verdict, -1) < verdict_rank.get(base_verdict, -1):
            print(
                f"ERROR: Verdict regression for {case_id} "
                f"(baseline={base_verdict}, latest={latest_verdict})"
            )
            exit_code = 1

    if exit_code == 0:
        print("OK: No regression detected.")

    return exit_code


def resolve_paths(
    baseline_path: str | None,
    latest_path: str | None,
    task: str | None,
) -> tuple[str, str]:
    if baseline_path and latest_path:
        return baseline_path, latest_path

    if task:
        resolved_baseline = baseline_path or f"baselines/{task}/baseline_results.json"
        resolved_latest = latest_path or f"results/{task}/latest_results.json"
        return resolved_baseline, resolved_latest

    raise ValueError(
        "Provide both baseline_path and latest_path, or use --task to resolve example-scoped defaults."
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare eval results against baseline.")
    parser.add_argument("baseline_path", nargs="?", type=str, help="Path to baseline results JSON")
    parser.add_argument("latest_path", nargs="?", type=str, help="Path to latest results JSON")
    parser.add_argument(
        "--task",
        type=str,
        default=None,
        help="Task/example name used to resolve default paths under baselines/<task>/ and results/<task>/",
    )
    parser.add_argument(
        "--max-drop",
        type=float,
        default=0.3,
        help="Maximum allowed weighted score drop before failing",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    baseline_path, latest_path = resolve_paths(
        baseline_path=args.baseline_path,
        latest_path=args.latest_path,
        task=args.task,
    )

    baseline_payload = load_json(baseline_path)
    latest_payload = load_json(latest_path)

    baseline = extract_results(baseline_payload)
    latest = extract_results(latest_payload)

    exit_code = compare_results(
        baseline=baseline,
        latest=latest,
        max_drop=args.max_drop,
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()