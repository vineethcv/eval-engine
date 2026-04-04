from runner import build_result_record


class DummyEvalResult:
    def __init__(self) -> None:
        self.tasting_clarity = 4
        self.popularity_alignment = 4
        self.regional_diversity = 3
        self.language_tone = 5
        self.weighted_score = 4.0
        self.verdict = "PASS"
        self.gate_pass = True
        self.failure_reasons = []


def fake_evalresult_to_flat_dict(eval_result: DummyEvalResult) -> dict:
    return {
        "tasting_clarity": eval_result.tasting_clarity,
        "popularity_alignment": eval_result.popularity_alignment,
        "regional_diversity": eval_result.regional_diversity,
        "language_tone": eval_result.language_tone,
        "weighted_score": eval_result.weighted_score,
        "verdict": eval_result.verdict,
        "gate_pass": eval_result.gate_pass,
        "gate_reasons": eval_result.failure_reasons,
    }


def test_build_result_record_contains_standardized_sections(monkeypatch) -> None:
    monkeypatch.setattr("runner.evalresult_to_flat_dict", fake_evalresult_to_flat_dict)

    eval_case = {
        "id": "REC_001",
        "query": "Recommend 3 red wines under 50 euros.",
        "bucket": "happy_path",
        "scenario": "happy_path",
    }

    heuristic_result = DummyEvalResult()
    run_metadata = {"mode": "mock"}

    record = build_result_record(
        eval_case=eval_case,
        response="Example response",
        heuristic_result=heuristic_result,
        confidence=0.92,
        run_metadata=run_metadata,
        judge_result=None,
    )

    assert record["id"] == "REC_001"
    assert record["generator"]["response"] == "Example response"
    assert record["heuristic_evaluation"]["weighted_score"] == 4.0
    assert record["heuristic_evaluation"]["verdict"] == "PASS"
    assert record["heuristic_evaluation"]["gate_pass"] is True
    assert record["judge_evaluation"] is None
    assert record["run_metadata"] == run_metadata
    assert record["scenario"] == "happy_path"


def test_build_result_record_preserves_legacy_top_level_fields(monkeypatch) -> None:
    monkeypatch.setattr("runner.evalresult_to_flat_dict", fake_evalresult_to_flat_dict)

    eval_case = {
        "id": "REC_001",
        "query": "Recommend 3 red wines under 50 euros.",
    }

    heuristic_result = DummyEvalResult()

    record = build_result_record(
        eval_case=eval_case,
        response="Example response",
        heuristic_result=heuristic_result,
        confidence=0.92,
        run_metadata={},
        judge_result={"judge_scores": {"tasting_clarity": 4.0}},
    )

    assert record["weighted_score"] == 4.0
    assert record["verdict"] == "PASS"
    assert record["gate_pass"] is True
    assert record["judge_scores"]["tasting_clarity"] == 4.0