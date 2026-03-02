# eval-engine/scorer.py
from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Tuple


# ----------------------------
# Helpers: parsing / extraction
# ----------------------------

PRICE_RE = re.compile(r"(€\s*\d+(?:\.\d+)?)|(\b\d+(?:\.\d+)?\s*euros?\b)", re.IGNORECASE)

SENSORY_WORDS = {
    "cherry", "plum", "blackberry", "raspberry", "vanilla", "oak", "cocoa", "pepper",
    "tannin", "tannins", "acidity", "body", "finish", "silky", "smooth", "elegant",
    "structured", "balanced", "medium-bodied", "full-bodied", "light-bodied",
}
GENERIC_PHRASES = {
    "tasty", "nice taste", "strong flavors", "many people like", "good wine", "suitable for dinner"
}
WINE_STYLE_RED_HINTS = {"red", "rioja", "chianti", "barolo", "bordeaux", "cabernet", "merlot", "syrah", "shiraz",
                        "tempranillo", "sangiovese", "malbec", "pinot noir", "nebbiolo", "garnacha","côtes", "cotes", "rhône", "rhone", "côtes du rhône", "cotes du rhone",
                        "cote du rhone", "côtes du rhone","montepulciano", "montepulciano d'abruzzo", "montepulciano d abruzzo",
                        "nero d'avola", "nero d avola",
                        "barbera", "dolcetto", "primitivo", "amarone", "valpolicella",}
WHITE_HINTS = {"white", "chardonnay", "sauvignon blanc", "riesling", "pinot grigio"}

REGION_KEYWORDS = {
    "france", "italy", "spain", "bordeaux", "tuscany", "piemonte", "rioja",
    "california", "chile", "argentina", "australia", "south africa", "portugal",
    "côtes du rhône", "cotes du rhone", "rhone"
}

def _normalize(s: str) -> str:
    s = s.strip().lower()
    # Normalize apostrophes and accents-ish
    s = s.replace("’", "'")
    s = re.sub(r"[^\w\s\-']", " ", s)  # keep words, spaces, hyphens, apostrophes
    s = re.sub(r"\s+", " ", s)
    return s

def extract_items(response: str) -> List[str]:
    lines = [ln.strip() for ln in response.splitlines() if ln.strip()]
    numbered = [ln for ln in lines if re.match(r"^\d+[\.\)]\s+", ln)]
    return [re.sub(r"^\d+[\.\)]\s+", "", ln).strip() for ln in numbered]

def extract_prices(text: str) -> List[float]:
    prices: List[float] = []
    for m in PRICE_RE.finditer(text):
        token = m.group(0)
        # Pull the first number out
        nm = re.search(r"\d+(?:\.\d+)?", token)
        if nm:
            prices.append(float(nm.group(0)))
    return prices

def looks_red(text: str) -> bool:
    t = _normalize(text)
    if any(w in t for w in WHITE_HINTS):
        return False
    return any(w in t for w in WINE_STYLE_RED_HINTS)

def contains_white_signal(text: str) -> bool:
    t = _normalize(text)
    return any(w in t for w in WHITE_HINTS)

def distinct_regions(text: str) -> int:
    t = _normalize(text)
    found = {rk for rk in REGION_KEYWORDS if rk in t}
    return len(found)

def sensory_density(text: str) -> float:
    t = _normalize(text)
    words = re.findall(r"[a-zA-Z\-']+", t)
    if not words:
        return 0.0
    sensory_hits = sum(1 for w in words if w in SENSORY_WORDS)
    return sensory_hits / max(1, len(words))

def genericness(text: str) -> int:
    t = _normalize(text)
    return sum(1 for p in GENERIC_PHRASES if p in t)


# ----------------------------
# Output data structures
# ----------------------------

@dataclass
class GateResult:
    passed: bool
    reasons: List[str]

@dataclass
class DimensionScores:
    tasting_clarity: float
    popularity_alignment: float
    regional_diversity: float
    language_tone: float

@dataclass
class EvalResult:
    case_id: str
    query: str
    response: str
    critical_gate: GateResult
    dimension_scores: DimensionScores
    weighted_score: float
    verdict: str  # PASS / WARN / FAIL
    notes: Dict[str, Any]


# ----------------------------
# Critical gate checks
# ----------------------------

def check_critical_gates(response: str, rubric: Dict[str, Any]) -> GateResult:
    reasons: List[str] = []
    gates = rubric.get("critical_gates", {})
    expected_count = int(gates.get("exact_count", 3))
    max_price = float(gates.get("max_price", 50))
    must_be_red = bool(gates.get("must_be_red", True))

    items = extract_items(response)

    # Count gate: We consider "items with prices" as the actual recommendation items (more robust).
    priced_items = []
    for it in items:
        if extract_prices(it):
            priced_items.append(it)
    candidate_items = priced_items if priced_items else items

    if len(candidate_items) != expected_count:
        reasons.append(f"Expected exactly {expected_count} items, got {len(candidate_items)}.")

    # Price gate
    # Only check prices inside the candidate items (recommendations), not in explanatory notes
    candidate_text = "\n".join(candidate_items[:expected_count])
    all_prices = extract_prices(candidate_text)
    if not all_prices:
        reasons.append("No prices found in response.")
    else:
        over = [p for p in all_prices if p > max_price]
        if over:
            reasons.append(f"Found price(s) over €{max_price}: {over}")

    # Red wine gate (real LLM friendly):
    # Per-item red classification is brittle without a wine knowledge base.
    # Only fail if the response explicitly signals white wines.
    if must_be_red and contains_white_signal(response):
        reasons.append("Response contains signals of white wine.")

    # Factual integrity gate (v1): heuristic only.
    # In Week 3/4 we’ll replace this with LLM-judge or knowledge-base checks.
    # For now, we only flag obviously fabricated patterns.
    if "unicorn winery" in _normalize(response) or "madeup" in _normalize(response):
        reasons.append("Possible fabricated entity detected (heuristic).")

    return GateResult(passed=(len(reasons) == 0), reasons=reasons)


# ----------------------------
# Heuristic scoring (v1)
# ----------------------------

def score_tasting_clarity(response: str) -> float:
    """
    1 = generic/vague
    5 = structured sensory detail
    """
    dens = sensory_density(response)
    gen = genericness(response)

    # Simple buckets: tune later
    if dens < 0.01 and gen >= 1:
        return 1.0
    if dens < 0.015:
        return 2.0
    if dens < 0.025:
        return 3.0
    if dens < 0.04:
        return 4.0
    return 5.0

def score_popularity_alignment(response: str) -> float:
    """
    Proxy:
    - recognizable grapes/regions -> higher
    - totally vague -> lower
    """
    t = _normalize(response)
    hits = sum(1 for w in ["rioja", "chianti", "bordeaux", "cabernet", "merlot", "pinot noir", "syrah", "malbec"]
               if w in t)
    if hits == 0:
        return 2.0
    if hits <= 2:
        return 3.0
    if hits <= 4:
        return 4.0
    return 5.0

def score_regional_diversity(response: str) -> float:
    """
    Uses explicit region/country mentions as a proxy.
    If no region signals, cap the score.
    """
    n = distinct_regions(response)
    if n == 0:
        return 2.0
    if n == 1:
        return 2.0
    if n == 2:
        return 3.0
    if n == 3:
        return 4.0
    return 5.0

def score_language_tone(response: str) -> float:
    """
    Proxy:
    - very short / generic -> low
    - clear and descriptive -> higher
    """
    t = response.strip()
    length = len(t)
    gen = genericness(t)

    if length < 120:
        return 2.0 if gen == 0 else 1.0
    if gen >= 2:
        return 2.0
    # Look for structure cues
    if any(k in _normalize(t) for k in ["notes of", "pairs with", "acidity", "tannins", "finish", "medium-bodied"]):
        return 4.5
    return 4.0


# ----------------------------
# Main evaluation function
# ----------------------------

def evaluate_case(case: Dict[str, Any], response: str, rubric: Dict[str, Any]) -> EvalResult:
    gates = check_critical_gates(response, rubric)

    # Default dimension scores (if gate fails, still compute but verdict becomes FAIL with weighted_score=0)
    dim = DimensionScores(
        tasting_clarity=score_tasting_clarity(response),
        popularity_alignment=score_popularity_alignment(response),
        regional_diversity=score_regional_diversity(response),
        language_tone=score_language_tone(response),
    )

    weights = rubric.get("weights", {})
    w_t = float(weights.get("tasting_clarity", 0.3))
    w_p = float(weights.get("popularity_alignment", 0.3))
    w_r = float(weights.get("regional_diversity", 0.2))
    w_l = float(weights.get("language_tone", 0.2))

    weighted = (
        dim.tasting_clarity * w_t +
        dim.popularity_alignment * w_p +
        dim.regional_diversity * w_r +
        dim.language_tone * w_l
    )

    thresholds = rubric.get("thresholds", {})
    pass_th = float(thresholds.get("pass", 3.5))
    warn_th = float(thresholds.get("warn", 3.0))

    if not gates.passed:
        verdict = "FAIL"
        weighted_score = 0.0
    else:
        weighted_score = round(weighted, 2)
        if weighted_score >= pass_th:
            verdict = "PASS"
        elif weighted_score >= warn_th:
            verdict = "WARN"
        else:
            verdict = "FAIL"

    return EvalResult(
        case_id=str(case.get("id", "")),
        query=str(case.get("query", "")),
        response=response,
        critical_gate=gates,
        dimension_scores=dim,
        weighted_score=weighted_score,
        verdict=verdict,
        notes={
            "bucket": case.get("bucket", case.get("notes", "")),
        }
    )

def evalresult_to_flat_dict(er: EvalResult) -> Dict[str, Any]:
    d = {
        "case_id": er.case_id,
        "query": er.query,
        "verdict": er.verdict,
        "weighted_score": er.weighted_score,
        "gate_passed": er.critical_gate.passed,
        "gate_reasons": " | ".join(er.critical_gate.reasons),
        "tasting_clarity": er.dimension_scores.tasting_clarity,
        "popularity_alignment": er.dimension_scores.popularity_alignment,
        "regional_diversity": er.dimension_scores.regional_diversity,
        "language_tone": er.dimension_scores.language_tone,
        "bucket": er.notes.get("bucket", ""),
    }
    return d