from typing import Dict, Any

from scorer import EvalResult


def compute_confidence(result: EvalResult) -> float:
    """
    Estimate confidence in the evaluation itself (not model confidence).

    Lower confidence when:
    - parsing is weak
    - borderline scores
    - limited signal in response
    """

    score = result.weighted_score

    # Penalize near-boundary scores
    if 3.0 <= score <= 3.6:
        score_adj = 0.2
    else:
        score_adj = 0.0

    # Penalize weak parsing signals
    item_penalty = 0.2 if result.notes.get("item_count", 0) < 3 else 0
    price_penalty = 0.2 if result.notes.get("price_count", 0) < 3 else 0
    region_penalty = 0.2 if result.notes.get("region_count", 0) < 2 else 0

    confidence = 1.0 - (score_adj + item_penalty + price_penalty + region_penalty)

    return round(max(0.0, confidence), 2)