from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List


DIMENSIONS = [
    "tasting_clarity",
    "popularity_alignment",
    "regional_diversity",
    "language_tone",
]


# ----------------------------
# Data structure
# ----------------------------

@dataclass
class EvalResult:
    gate_pass: bool
    gate_reasons: List[str]

    tasting_clarity: float
    popularity_alignment: float
    regional_diversity: float
    language_tone: float

    weighted_score: float
    verdict: str

    notes: Dict[str, Any]


# ----------------------------
# Parsing helpers
# ----------------------------

def extract_items(text: str) -> List[str]:
    """
    Extract numbered list items from response.
    Expected format:
    1. Wine ...
    2. Wine ...
    """
    return re.findall(r"\d+\.\s(.+?)(?=\n\d+\.|\Z)", text, re.S)


def extract_prices(items: List[str]) -> List[float]:
    """
    Extract euro prices from each item.
    """
    prices = []
    for it in items:
        m = re.search(r"€\s*(\d+(?:\.\d+)?)", it)
        if m:
            prices.append(float(m.group(1)))
    return prices


def distinct_regions(items: List[str]) -> int:
    """
    Estimate distinct regions using text between dashes.
    """
    regions = set()
    for it in items:
        parts = re.split(r"—|-", it)
        if len(parts) >= 2:
            regions.add(parts[1].strip())
    return len(regions)


def contains_white_signal(text: str) -> bool:
    """
    Detect obvious white wine indicators.
    """
    return bool(
        re.search(
            r"\b(chardonnay|sauvignon blanc|riesling|pinot grigio)\b",
            text,
            re.I,
        )
    )


# ----------------------------
# Scoring helpers
# ----------------------------

def score_tasting_clarity(text: str) -> float:
    """
    Score based on presence of tasting vocabulary.
    """
    words = re.findall(r"\b\w+\b", text.lower())
    hits = sum(
        w in {
            "tannin",
            "tannins",
            "acidity",
            "oak",
            "oaky",
            "cherry",
            "berry",
            "spice",
            "vanilla",
            "aroma",
            "finish",
            "structured",
            "smooth",
            "balanced",
            "full-bodied",
            "medium-bodied",
        }
        for w in words
    )
    if hits >= 6:
        return 5
    if hits >= 4:
        return 4
    if hits >= 2:
        return 3
    if hits >= 1:
        return 2
    return 1


def score_popularity_alignment(text: str) -> float:
    """
    Proxy using presence of well-known regions.
    """
    known = [
        "bordeaux",
        "burgundy",
        "rioja",
        "tuscany",
        "chianti",
        "barolo",
        "napa",
    ]
    hits = sum(k in text.lower() for k in known)
    if hits >= 4:
        return 5
    if hits >= 3:
        return 4
    if hits >= 2:
        return 3
    if hits >= 1:
        return 2
    return 1


def score_regional_diversity(n_regions: int) -> float:
    """
    Score diversity based on distinct regions.
    """
    if n_regions >= 3:
        return 5
    if n_regions == 2:
        return 3
    return 1


def score_language_tone(text: str) -> float:
    """
    Rough proxy for tone quality based on sentence richness.
    """
    sentences = re.split(r"[.!?]+", text)
    avg_len = sum(len(s.split()) for s in sentences if s.strip()) / max(
        1, len(sentences)
    )
    if avg_len >= 12:
        return 5
    if avg_len >= 9:
        return 4
    if avg_len >= 6:
        return 3
    if avg_len >= 4:
        return 2
    return 1


# ----------------------------
# Core evaluation
# ----------------------------

def evaluate_case(query: str, response: str, rubric: Dict[str, Any]) -> EvalResult:
    """
    Run deterministic evaluation:
    - critical gates
    - heuristic scoring
    - weighted aggregation
    - verdict assignment
    """

    items = extract_items(response)
    prices = extract_prices(items)
    n_regions = distinct_regions(items)

    gates = rubric.get("critical_gates", {})
    weights = rubric.get("weights", {})
    thresholds = rubric.get("thresholds", {})

    gate_pass = True
    reasons = []

    if len(items) != gates.get("exact_count", 3):
        gate_pass = False
        reasons.append("incorrect_item_count")

    if any(p > gates.get("max_price", 50) for p in prices):
        gate_pass = False
        reasons.append("price_exceeded")

    if gates.get("must_be_red", True) and contains_white_signal(response):
        gate_pass = False
        reasons.append("non_red_wine_detected")

    t = score_tasting_clarity(response)
    p = score_popularity_alignment(response)
    r = score_regional_diversity(n_regions)
    l = score_language_tone(response)

    weighted = round(
        t * weights.get("tasting_clarity", 0)
        + p * weights.get("popularity_alignment", 0)
        + r * weights.get("regional_diversity", 0)
        + l * weights.get("language_tone", 0),
        2,
    )

    if not gate_pass:
        verdict = "FAIL"
    elif weighted >= thresholds.get("pass", 3.5):
        verdict = "PASS"
    elif weighted >= thresholds.get("warn", 3.0):
        verdict = "WARN"
    else:
        verdict = "FAIL"

    return EvalResult(
        gate_pass=gate_pass,
        gate_reasons=reasons,
        tasting_clarity=t,
        popularity_alignment=p,
        regional_diversity=r,
        language_tone=l,
        weighted_score=weighted,
        verdict=verdict,
        notes={
            "item_count": len(items),
            "price_count": len(prices),
            "region_count": n_regions,
        },
    )


def evalresult_to_flat_dict(res: EvalResult) -> Dict[str, Any]:
    """
    Convert EvalResult to flat dict for JSON/CSV output.
    """
    return {
        "gate_pass": res.gate_pass,
        "gate_reasons": ",".join(res.gate_reasons),
        "tasting_clarity": res.tasting_clarity,
        "popularity_alignment": res.popularity_alignment,
        "regional_diversity": res.regional_diversity,
        "language_tone": res.language_tone,
        "weighted_score": res.weighted_score,
        "verdict": res.verdict,
        **res.notes,
    }