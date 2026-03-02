# eval-engine/regression_compare.py
from __future__ import annotations

import json
import sys
from typing import Any, Dict, Tuple


def load(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def index_by_case(results: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Input is runner's latest_results.json structure:
    { run_at, summary, results: [ { case, response, critical_gate, dimension_scores, weighted_score, verdict } ... ] }
    """
    out: Dict[str, Dict[str, Any]] = {}
    for r in results.get("results", []):
        cid = r.get("case", {}).get("id")
        if cid:
            out[str(cid)] = r
    return out


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: python3 regression_compare.py <baseline.json> <latest.json> [max_drop]")
        sys.exit(2)

    baseline_path = sys.argv[1]
    latest_path = sys.argv[2]
    max_drop = float(sys.argv[3]) if len(sys.argv) >= 4 else 0.3

    base = load(baseline_path)
    latest = load(latest_path)

    b = index_by_case(base)
    l = index_by_case(latest)

    regressions = []

    for cid, bcase in b.items():
        if cid not in l:
            regressions.append((cid, "missing_in_latest", "", ""))
            continue

        lcase = l[cid]

        b_gate = bool(bcase.get("critical_gate", {}).get("passed", False))
        l_gate = bool(lcase.get("critical_gate", {}).get("passed", False))

        b_score = float(bcase.get("weighted_score", 0.0))
        l_score = float(lcase.get("weighted_score", 0.0))

        b_verdict = str(bcase.get("verdict", ""))
        l_verdict = str(lcase.get("verdict", ""))

        # Critical regression: gate was passing and now fails
        if b_gate and not l_gate:
            regressions.append((cid, "critical_gate_regression", b_verdict, l_verdict))
            continue

        # Score regression (only if both pass gates)
        if b_gate and l_gate:
            drop = b_score - l_score
            if drop > max_drop:
                regressions.append((cid, f"score_drop>{max_drop} (drop={drop:.2f})", f"{b_score}", f"{l_score}"))

            # Verdict regression: PASS->WARN/FAIL or WARN->FAIL
            order = {"PASS": 2, "WARN": 1, "FAIL": 0}
            if order.get(l_verdict, -1) < order.get(b_verdict, -1):
                regressions.append((cid, "verdict_regression", b_verdict, l_verdict))

    if regressions:
        print("REGRESSIONS DETECTED:")
        for cid, kind, before, after in regressions:
            print(f"- {cid}: {kind} ({before} -> {after})")
        sys.exit(1)

    print("No regressions detected.")
    sys.exit(0)


if __name__ == "__main__":
    main()