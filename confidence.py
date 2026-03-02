# eval-engine/confidence.py
from __future__ import annotations

from typing import Dict, Any
from scorer import extract_items, extract_prices, distinct_regions, genericness, _normalize


def compute_confidence(response: str, gate_passed: bool, dimension_scores: Dict[str, float]) -> float:
    """
    Returns confidence 1.0–5.0 (heuristic).
    This is confidence in the *eval score* (not the model's confidence).
    """
    if not gate_passed:
        return 4.5  # we are usually confident about hard failures (deterministic)

    t = _normalize(response)

    # Signals that reduce confidence (uncertainty in scoring)
    items = extract_items(response)
    priced = sum(1 for it in items if extract_prices(it))
    regions = distinct_regions(response)
    gen = genericness(response)

    penalties = 0.0

    # If we can't clearly detect 3 priced items, scoring is less reliable
    if priced < 3:
        penalties += 1.0

    # If regions are not explicit, diversity score is less reliable
    if regions == 0:
        penalties += 0.8

    # If very generic language, tasting/tone scoring becomes more subjective
    if gen >= 2:
        penalties += 0.7

    # If weighted score is borderline, confidence should drop a bit
    # (close to thresholds = more disagreement risk)
    weighted = (
        dimension_scores["tasting_clarity"] * 0.3 +
        dimension_scores["popularity_alignment"] * 0.3 +
        dimension_scores["regional_diversity"] * 0.2 +
        dimension_scores["language_tone"] * 0.2
    )
    if 3.3 <= weighted <= 3.7:
        penalties += 0.5

    base = 4.5
    conf = max(1.0, min(5.0, base - penalties))
    # round for reporting
    return round(conf, 1)