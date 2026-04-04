from __future__ import annotations

import argparse
import json
from typing import Any, Dict, List


def load_results(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def index_by_id(results: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    return {row["id"]: row for row in results}


def compare_runs(
    baseline: Dict[str, Any],
    latest: Dict[str, Any],
    max_drop: float,
) -> List[Dict[str, Any]]:
    baseline_results = index_by_id(baseline.get("results", []))
    latest_results = index_by_id(latest.get("results", []))

    regressions: List[Dict[str, Any]] = []

    for case_id, base_row in baseline_results.items():
        latest_row = latest_results.get(case_id)

        if latest_row is None:
            regressions.append(
                {
                    "id": case_id,
                    "type": "missing_case",
                    "message": "Case missing in latest run",
                }
            )
            continue

        if base_row.get("gate_pass") and not latest_row.get("gate_pass"):
            regressions.append(
                {
                    "id": case_id,
                    "type": "critical_gate_regression",
                    "message": "Critical gate changed from PASS to FAIL",
                }
            )

        base_score = float(base_row.get("weighted_score", 0))
        latest_score = float(latest_row.get("weighted_score", 0))
        score_drop = round(base_score - latest_score, 2)

        if score_drop > max_drop:
            regressions.append(
                {
                    "id": case_id,
                    "type": "score_drop",
                    "message": f"Weighted score dropped by {score_drop}",
                    "baseline_score": base_score,
                    "latest_score": latest_score,
                }
            )

        base_verdict = base_row.get("verdict")
        latest_verdict = latest_row.get("verdict")

        if base_verdict == "PASS" and latest_verdict in {"WARN", "FAIL"}:
            regressions.append(
                {
                    "id": case_id,
                    "type": "verdict_regression",
                    "message": f"Verdict changed from {base_verdict} to {latest_verdict}",
                }
            )
        elif base_verdict == "WARN" and latest_verdict == "FAIL":
            regressions.append(
                {
                    "id": case_id,
                    "type": "verdict_regression",
                    "message": f"Verdict changed from {base_verdict} to {latest_verdict}",
                }
            )

    return regressions


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare eval runs for regressions.")
    parser.add_argument("baseline", help="Path to baseline results JSON")
    parser.add_argument("latest", help="Path to latest results JSON")
    parser.add_argument(
        "--max-drop",
        type=float,
        default=0.3,
        help="Maximum allowed weighted score drop before flagging regression",
    )

    args = parser.parse_args()

    baseline = load_results(args.baseline)
    latest = load_results(args.latest)

    regressions = compare_runs(baseline, latest, args.max_drop)

    baseline_count = len(baseline.get("results", []))
    latest_count = len(latest.get("results", []))
    compared_count = min(baseline_count, latest_count)

    print("\nRegression comparison summary")
    print(f" - baseline: {args.baseline}")
    print(f" - latest:   {args.latest}")
    print(f" - baseline cases: {baseline_count}")
    print(f" - latest cases:   {latest_count}")
    print(f" - compared cases: {compared_count}")
    print(f" - regressions found: {len(regressions)}")

    if regressions:
        print("\nRegressions:")
        for reg in regressions:
            print(f" - [{reg['id']}] {reg['type']}: {reg['message']}")
        return 1

    print("\nNo regressions found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())