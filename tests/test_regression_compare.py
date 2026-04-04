from regression_compare import compare_runs


def test_missing_case_detection():
    baseline = {
        "results": [{"id": "A", "weighted_score": 4.0, "verdict": "PASS", "gate_pass": True}]
    }
    latest = {"results": []}

    regressions = compare_runs(baseline, latest, max_drop=0.3)

    assert any(r["type"] == "missing_case" for r in regressions)


def test_score_drop_detection():
    baseline = {
        "results": [{"id": "A", "weighted_score": 4.0, "verdict": "PASS", "gate_pass": True}]
    }
    latest = {
        "results": [{"id": "A", "weighted_score": 3.0, "verdict": "PASS", "gate_pass": True}]
    }

    regressions = compare_runs(baseline, latest, max_drop=0.5)

    assert any(r["type"] == "score_drop" for r in regressions)


def test_verdict_regression():
    baseline = {
        "results": [{"id": "A", "weighted_score": 4.0, "verdict": "PASS", "gate_pass": True}]
    }
    latest = {
        "results": [{"id": "A", "weighted_score": 3.2, "verdict": "WARN", "gate_pass": True}]
    }

    regressions = compare_runs(baseline, latest, max_drop=1.0)

    assert any(r["type"] == "verdict_regression" for r in regressions)


def test_gate_regression():
    baseline = {
        "results": [{"id": "A", "weighted_score": 4.0, "verdict": "PASS", "gate_pass": True}]
    }
    latest = {
        "results": [{"id": "A", "weighted_score": 4.0, "verdict": "PASS", "gate_pass": False}]
    }

    regressions = compare_runs(baseline, latest, max_drop=1.0)

    assert any(r["type"] == "critical_gate_regression" for r in regressions)