from scorer import evaluate_case

RUBRIC = {
    "critical_gates": {
        "exact_count": 3,
        "must_be_red": True,
        "max_price": 50,
    },
    "weights": {
        "tasting_clarity": 0.3,
        "popularity_alignment": 0.3,
        "regional_diversity": 0.2,
        "language_tone": 0.2,
    },
    "thresholds": {
        "pass": 3.5,
        "warn": 3.0,
    },
}


def test_valid_response_passes_gates():
    response = """1. Bordeaux — France — €40
Rich and structured.

2. Chianti — Italy — €30
Cherry and spice.

3. Rioja — Spain — €25
Smooth and balanced."""
    
    res = evaluate_case("query", response, RUBRIC)

    assert res.gate_pass is True
    assert res.verdict in {"PASS", "WARN", "FAIL"}  # flexible


def test_price_gate_failure():
    response = """1. Bordeaux — France — €60
Rich.

2. Chianti — Italy — €30
Cherry.

3. Rioja — Spain — €25
Smooth."""
    
    res = evaluate_case("query", response, RUBRIC)

    assert res.gate_pass is False
    assert "price_exceeded" in res.gate_reasons


def test_exact_count_failure():
    response = """1. Bordeaux — France — €40
Rich.

2. Chianti — Italy — €30
Cherry."""
    
    res = evaluate_case("query", response, RUBRIC)

    assert res.gate_pass is False
    assert "incorrect_item_count" in res.gate_reasons


def test_white_wine_detection():
    response = """1. Chardonnay — France — €30
Crisp.

2. Chianti — Italy — €30
Cherry.

3. Rioja — Spain — €25
Smooth."""
    
    res = evaluate_case("query", response, RUBRIC)

    assert res.gate_pass is False
    assert "non_red_wine_detected" in res.gate_reasons


def test_region_diversity_scoring():
    response = """1. Bordeaux — France — €40
Rich.

2. Rioja — Spain — €30
Cherry.

3. Chianti — Italy — €25
Smooth."""
    
    res = evaluate_case("query", response, RUBRIC)

    assert res.regional_diversity >= 3