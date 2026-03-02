# eval-engine/runner.py
from __future__ import annotations

import argparse
import csv
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List
from confidence import compute_confidence
from llm_client import respond_openai

from scorer import evaluate_case, evalresult_to_flat_dict


def load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

# ----------------------------
# Mock model (Week 2: infra-first)
# Replace this with real model calls in Week 3.
# ----------------------------
def mock_llm_respond(query: str) -> str:
    q = query.lower()

    # Adversarial asks for €100 option
    if "100" in q or "premium" in q:
        return (
            "1. Rioja Crianza (Spain) – €18\n"
            "Approachable and smooth with red berry notes.\n\n"
            "2. Chianti Classico (Italy) – €24\n"
            "Elegant acidity, light tannins, notes of cherry.\n\n"
            "3. Côtes du Rhône (France) – €16\n"
            "Soft spice and blackberry, easy-drinking.\n\n"
            "Note: I’m keeping all picks under €50 as requested."
        )

    # Negative filter: no Pinot Noir
    if "no pinot" in q or "without pinot" in q:
        return (
            "1. Merlot (France) – €22\n"
            "Smooth, low tannins, plum and cherry.\n\n"
            "2. Tempranillo Rioja (Spain) – €19\n"
            "Medium-bodied, vanilla and red berries, very approachable.\n\n"
            "3. Sangiovese (Italy) – €23\n"
            "Fresh cherry notes, balanced acidity, easy for beginners."
        )

    # Steak / dinner context
    if "steak" in q:
        return (
            "1. Malbec (Argentina) – €20\n"
            "Plush dark fruit, medium tannins, great with steak.\n\n"
            "2. Cabernet Sauvignon (Chile) – €18\n"
            "Blackcurrant notes, structured but approachable.\n\n"
            "3. Rioja Crianza (Spain) – €21\n"
            "Oak-tinged vanilla and cherry, smooth finish."
        )

    # Italian preference
    if "italian" in q or "italy" in q:
        return (
            "1. Chianti Classico (Italy) – €24\n"
            "Cherry, subtle herbs, balanced acidity, smooth tannins.\n\n"
            "2. Montepulciano d'Abruzzo (Italy) – €16\n"
            "Soft plum notes, easy-drinking, medium body.\n\n"
            "3. Nero d'Avola (Italy) – €17\n"
            "Ripe berry fruit, gentle spice, approachable finish."
        )

    # Default strong-ish answer
    return (
        "1. Merlot (France) – €22\n"
        "Smooth, fruit-forward, low tannins with plum and cherry.\n\n"
        "2. Rioja Crianza (Spain) – €19\n"
        "Medium-bodied, vanilla and red berries, balanced and approachable.\n\n"
        "3. Chianti Classico (Italy) – €24\n"
        "Elegant acidity, soft structure, bright cherry notes."
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["mock", "openai"], default="mock")
    parser.add_argument("--model", default="gpt-4.1-mini")  # you can change later
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--dataset", default="dataset.json")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--rubric", default="rubric.json")
    parser.add_argument("--outdir", default="results")
    parser.add_argument("--set-baseline", action="store_true", help="Overwrite results/baseline_results.json with this run")
    args = parser.parse_args()

    dataset = load_json(args.dataset)
    rubric: Dict[str, Any] = load_json(args.rubric)

    ensure_dir(args.outdir)

    all_results = []
    flat_rows = []
    dataset_iter = dataset[:args.limit] if args.limit else dataset
    for case in dataset_iter:
        query = str(case.get("query", ""))
        if args.mode == "mock":
            response = mock_llm_respond(query)
        else:
            response = respond_openai(query, model=args.model, temperature=args.temperature)
        er = evaluate_case(case, response, rubric)
        dim_scores = {
            "tasting_clarity": er.dimension_scores.tasting_clarity,
            "popularity_alignment": er.dimension_scores.popularity_alignment,
            "regional_diversity": er.dimension_scores.regional_diversity,
            "language_tone": er.dimension_scores.language_tone,
        }
        conf = compute_confidence(response, er.critical_gate.passed, dim_scores)
        all_results.append({
            "case": case,
            "response": response,
            "critical_gate": {
                "passed": er.critical_gate.passed,
                "reasons": er.critical_gate.reasons,
            },
            "dimension_scores": dim_scores,
            "weighted_score": er.weighted_score,
            "verdict": er.verdict,
            "eval_confidence": conf,
            "notes": er.notes,
        })
        flat = evalresult_to_flat_dict(er)
        flat["eval_confidence"] = conf
        flat_rows.append(flat)

    run_payload = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "run_config": {
            "mode": args.mode,
            "model": args.model if args.mode != "mock" else "mock",
            "temperature": args.temperature if args.mode != "mock" else None,
        },
        "summary": {
            "total": len(flat_rows),
            "pass": sum(1 for r in flat_rows if r["verdict"] == "PASS"),
            "warn": sum(1 for r in flat_rows if r["verdict"] == "WARN"),
            "fail": sum(1 for r in flat_rows if r["verdict"] == "FAIL"),
        },
        "results": all_results,
    }

    # Write latest JSON
    latest_json_path = os.path.join(args.outdir, "latest_results.json")
    with open(latest_json_path, "w", encoding="utf-8") as f:
        json.dump(run_payload, f, ensure_ascii=False, indent=2)

    # Write timestamped JSON
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    run_json_path = os.path.join(args.outdir, f"run_{ts}.json")
    with open(run_json_path, "w", encoding="utf-8") as f:
        json.dump(run_payload, f, ensure_ascii=False, indent=2)

    # CSV report
    csv_path = os.path.join(args.outdir, "report.csv")
    fieldnames = list(flat_rows[0].keys()) if flat_rows else []
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in flat_rows:
            w.writerow(r)

    # Baseline
    if args.set_baseline:
        baseline_path = os.path.join(args.outdir, "baseline_results.json")
        with open(baseline_path, "w", encoding="utf-8") as f:
            json.dump(run_payload, f, ensure_ascii=False, indent=2)
        print(f"Baseline set: {baseline_path}")

    print(f"Wrote: {latest_json_path}")
    print(f"Wrote: {run_json_path}")
    print(f"Wrote: {csv_path}")

    totals = {
        "PASS": sum(1 for r in flat_rows if r["verdict"] == "PASS"),
        "WARN": sum(1 for r in flat_rows if r["verdict"] == "WARN"),
        "FAIL": sum(1 for r in flat_rows if r["verdict"] == "FAIL"),
    }
    print("Summary:", totals)

if __name__ == "__main__":
    main()