from regression_compare import compare_results


def test_compare_results_accepts_nested_heuristic_schema() -> None:
    baseline = [
        {
            "id": "REC_001",
            "heuristic_evaluation": {
                "weighted_score": 4.0,
                "verdict": "PASS",
                "gate_pass": True,
            },
        }
    ]

    latest = [
        {
            "id": "REC_001",
            "heuristic_evaluation": {
                "weighted_score": 4.0,
                "verdict": "PASS",
                "gate_pass": True,
            },
        }
    ]

    exit_code = compare_results(baseline=baseline, latest=latest, max_drop=0.3)
    assert exit_code == 0


def test_compare_results_detects_score_drop_from_nested_schema() -> None:
    baseline = [
        {
            "id": "REC_001",
            "heuristic_evaluation": {
                "weighted_score": 4.5,
                "verdict": "PASS",
                "gate_pass": True,
            },
        }
    ]

    latest = [
        {
            "id": "REC_001",
            "heuristic_evaluation": {
                "weighted_score": 3.9,
                "verdict": "PASS",
                "gate_pass": True,
            },
        }
    ]

    exit_code = compare_results(baseline=baseline, latest=latest, max_drop=0.3)
    assert exit_code == 1


def test_compare_results_accepts_legacy_top_level_fields() -> None:
    baseline = [
        {
            "id": "REC_001",
            "weighted_score": 4.0,
            "verdict": "PASS",
            "gate_pass": True,
        }
    ]

    latest = [
        {
            "id": "REC_001",
            "weighted_score": 4.0,
            "verdict": "PASS",
            "gate_pass": True,
        }
    ]

    exit_code = compare_results(baseline=baseline, latest=latest, max_drop=0.3)
    assert exit_code == 0