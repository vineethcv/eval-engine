from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List


WINE_DIMENSIONS = [
    "tasting_clarity",
    "popularity_alignment",
    "regional_diversity",
    "language_tone",
]

RETAIL_DIMENSIONS = [
    "instruction_match",
    "grounding_accuracy",
    "tool_use_correctness",
    "resolution_helpfulness",
    "tone_clarity",
]


# ----------------------------
# Data structure
# ----------------------------
@dataclass
class EvalResult:
    gate_pass: bool
    gate_reasons: List[str]
    tasting_clarity: float | None
    popularity_alignment: float | None
    regional_diversity: float | None
    language_tone: float | None
    weighted_score: float
    verdict: str
    notes: Dict[str, Any]
    scores: Dict[str, float]


# ----------------------------
# Generic helpers
# ----------------------------
def infer_task_type(rubric: Dict[str, Any]) -> str:
    weights = rubric.get("weights", {})
    if "instruction_match" in weights:
        return "retail_support"
    return "wine_recommendation"


def weighted_sum(scores: Dict[str, float], weights: Dict[str, float]) -> float:
    return round(sum(scores.get(k, 0.0) * weights.get(k, 0.0) for k in scores), 2)


def build_verdict(gate_pass: bool, weighted: float, thresholds: Dict[str, Any]) -> str:
    if not gate_pass:
        return "FAIL"
    if weighted >= thresholds.get("pass", 4.0):
        return "PASS"
    if weighted >= thresholds.get("warn", 3.0):
        return "WARN"
    return "FAIL"


# ----------------------------
# Wine parsing helpers
# ----------------------------
def extract_items(text: str) -> List[str]:
    return re.findall(r"\d+\.\s(.+?)(?=\n\d+\.|\Z)", text, re.S)


def extract_prices(items: List[str]) -> List[float]:
    prices = []
    for it in items:
        m = re.search(r"€\s*(\d+(?:\.\d+)?)", it)
        if m:
            prices.append(float(m.group(1)))
    return prices


def distinct_regions(items: List[str]) -> int:
    regions = set()
    for it in items:
        parts = re.split(r"—|-", it)
        if len(parts) >= 2:
            regions.add(parts[1].strip())
    return len(regions)


def contains_white_signal(text: str) -> bool:
    return bool(
        re.search(
            r"\b(chardonnay|sauvignon blanc|riesling|pinot grigio)\b",
            text,
            re.I,
        )
    )


# ----------------------------
# Wine scoring helpers
# ----------------------------
def score_tasting_clarity(text: str) -> float:
    words = re.findall(r"\b\w+\b", text.lower())
    hits = sum(
        w
        in {
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
    if n_regions >= 3:
        return 5
    if n_regions == 2:
        return 3
    return 1


def score_language_tone(text: str) -> float:
    sentences = re.split(r"[.!?]+", text)
    avg_len = sum(len(s.split()) for s in sentences if s.strip()) / max(
        1, len([s for s in sentences if s.strip()])
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


def evaluate_wine_case(query: str, response: str, rubric: Dict[str, Any]) -> EvalResult:
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

    scores = {
        "tasting_clarity": score_tasting_clarity(response),
        "popularity_alignment": score_popularity_alignment(response),
        "regional_diversity": score_regional_diversity(n_regions),
        "language_tone": score_language_tone(response),
    }

    weighted = weighted_sum(scores, weights)
    verdict = build_verdict(gate_pass, weighted, thresholds)

    return EvalResult(
        gate_pass=gate_pass,
        gate_reasons=reasons,
        tasting_clarity=scores["tasting_clarity"],
        popularity_alignment=scores["popularity_alignment"],
        regional_diversity=scores["regional_diversity"],
        language_tone=scores["language_tone"],
        weighted_score=weighted,
        verdict=verdict,
        notes={
            "task_type": "wine_recommendation",
            "item_count": len(items),
            "price_count": len(prices),
            "region_count": n_regions,
        },
        scores=scores,
    )


# ----------------------------
# Retail helpers
# ----------------------------
def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def contains_any(text: str, phrases: List[str]) -> bool:
    text_n = normalize_text(text)
    return any(p.lower() in text_n for p in phrases)


def count_hits(text: str, phrases: List[str]) -> int:
    text_n = normalize_text(text)
    return sum(1 for p in phrases if p.lower() in text_n)


def extract_budget(query: str) -> float | None:
    patterns = [
        r"under\s+(\d+(?:\.\d+)?)\s*euros?",
        r"budget of\s+(\d+(?:\.\d+)?)\s*euros?",
        r"(\d+(?:\.\d+)?)\s*euros?",
    ]
    q = query.lower()
    for pattern in patterns:
        match = re.search(pattern, q)
        if match:
            return float(match.group(1))
    return None


def price_mentions(text: str) -> List[float]:
    matches = re.findall(r"€\s*(\d+(?:\.\d+)?)|(\d+(?:\.\d+)?)\s*euros?", text.lower())
    values = []
    for m in matches:
        raw = m[0] or m[1]
        if raw:
            values.append(float(raw))
    return values


def detect_recommendation_item_count(text: str) -> int:
    numbered = extract_items(text)
    if numbered:
        return len(numbered)

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    bullet_lines = [line for line in lines if re.match(r"^[-*•]", line)]
    return len(bullet_lines)


def score_instruction_match_retail(query: str, response: str) -> float:
    q = query.lower()
    score = 3.0

    if "recommend" in q:
        item_count = detect_recommendation_item_count(response)
        if item_count >= 3:
            score += 1.0
        elif item_count == 0:
            score -= 1.5

    if "where is my order" in q or "cancel" in q or "order " in q:
        order_match = re.search(r"\bORD-\d+\b", query, re.I)
        if order_match and order_match.group(0).lower() in response.lower():
            score += 1.0
        elif order_match:
            score -= 1.0

    if "refund" in q and contains_any(response, ["refund", "business days"]):
        score += 0.5

    return max(1.0, min(5.0, score))


def score_grounding_accuracy_retail(query: str, response: str) -> float:
    q = query.lower()
    score = 2.5

    if "wore" in q and "outside" in q:
        if contains_any(response, ["not eligible", "unless faulty", "used outdoors"]):
            score += 2.0

    if "refund" in q:
        if contains_any(response, ["5 to 7 business days", "5-7 business days"]):
            score += 2.0

    if "warranty" in q and "treklite stove" in q:
        if contains_any(response, ["2-year", "manufacturing defects", "limited warranty"]):
            score += 2.0

    if "cancel" in q:
        if contains_any(response, ["cannot be cancelled", "can be cancelled", "before shipment", "after shipment"]):
            score += 1.5

    if "processing for several days" in q:
        if contains_any(response, ["contact support", "manual check", "3 business days"]):
            score += 1.5

    return max(1.0, min(5.0, score))


def score_tool_use_correctness_retail(query: str, response: str) -> float:
    q = query.lower()

    if "order " in q or "cancel" in q:
        if contains_any(response, ["ord-", "status", "processing", "shipped", "cancelled", "cannot be cancelled"]):
            return 4.0
        return 2.0

    if "recommend" in q or "suggest" in q:
        if detect_recommendation_item_count(response) >= 1:
            return 4.0
        return 2.0

    return 3.0


def score_resolution_helpfulness_retail(query: str, response: str) -> float:
    score = 2.5

    helpful_terms = [
        "you can",
        "you cannot",
        "i recommend",
        "contact support",
        "manual check",
        "under",
        "waterproof",
        "refund",
        "warranty",
    ]
    hits = count_hits(response, helpful_terms)

    if hits >= 4:
        score = 5.0
    elif hits >= 3:
        score = 4.0
    elif hits >= 2:
        score = 3.5
    elif hits >= 1:
        score = 3.0

    return max(1.0, min(5.0, score))


def score_tone_clarity_retail(text: str) -> float:
    sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
    if not sentences:
        return 1.0

    avg_len = sum(len(s.split()) for s in sentences) / len(sentences)

    if avg_len >= 18:
        return 5.0
    if avg_len >= 12:
        return 4.0
    if avg_len >= 8:
        return 3.0
    if avg_len >= 5:
        return 2.0
    return 1.0


def evaluate_retail_case(query: str, response: str, rubric: Dict[str, Any]) -> EvalResult:
    weights = rubric.get("weights", {})
    thresholds = rubric.get("thresholds", {})
    gate_names = rubric.get("critical_gates", [])

    gate_pass = True
    reasons: List[str] = []

    q = query.lower()
    r = response.lower()

    if "no_false_action_claim" in gate_names:
        if "cancel" in q and contains_any(r, ["cancelled successfully", "order cancelled"]) and contains_any(
            q, ["ord-1005", "ord-1011"]
        ):
            gate_pass = False
            reasons.append("false_action_claim")

    if "respect_constraints" in gate_names:
        budget = extract_budget(query)
        mentioned_prices = price_mentions(response)
        if budget is not None and any(price > budget for price in mentioned_prices):
            gate_pass = False
            reasons.append("constraint_violation")

    if "no_policy_hallucination" in gate_names:
        if "refund" in q and contains_any(r, ["same day", "24 hours", "instant refund"]):
            gate_pass = False
            reasons.append("policy_hallucination")

    if "no_invented_order_status" in gate_names:
        if "where is my order" in q or "order " in q:
            if contains_any(r, ["delivered yesterday", "out for delivery"]) and contains_any(
                q, ["ord-1002", "ord-1008"]
            ):
                gate_pass = False
                reasons.append("invented_order_status")

    if "valid_output_schema" in gate_names:
        if not response.strip():
            gate_pass = False
            reasons.append("empty_response")

    scores = {
        "instruction_match": score_instruction_match_retail(query, response),
        "grounding_accuracy": score_grounding_accuracy_retail(query, response),
        "tool_use_correctness": score_tool_use_correctness_retail(query, response),
        "resolution_helpfulness": score_resolution_helpfulness_retail(query, response),
        "tone_clarity": score_tone_clarity_retail(response),
    }

    weighted = weighted_sum(scores, weights)
    verdict = build_verdict(gate_pass, weighted, thresholds)

    return EvalResult(
        gate_pass=gate_pass,
        gate_reasons=reasons,
        tasting_clarity=None,
        popularity_alignment=None,
        regional_diversity=None,
        language_tone=None,
        weighted_score=weighted,
        verdict=verdict,
        notes={
            "task_type": "retail_support",
            "recommendation_item_count": detect_recommendation_item_count(response),
            "mentioned_price_count": len(price_mentions(response)),
        },
        scores=scores,
    )


# ----------------------------
# Core evaluation
# ----------------------------
def evaluate_case(query: str, response: str, rubric: Dict[str, Any]) -> EvalResult:
    task_type = infer_task_type(rubric)

    if task_type == "retail_support":
        return evaluate_retail_case(query, response, rubric)

    return evaluate_wine_case(query, response, rubric)


def evalresult_to_flat_dict(res: EvalResult) -> Dict[str, Any]:
    flat = {
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

    for key, value in res.scores.items():
        flat[key] = value

    return flat