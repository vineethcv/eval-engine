from __future__ import annotations

import json
import os
from statistics import mean, pstdev
from typing import Any, Dict, List

JUDGE_PROMPT_VERSION = "v2.0-ensemble-variants"

JUDGE_PROMPT_A = """
You are a strict evaluator for a wine recommendation assistant.

Score each dimension from 1 to 5 using these anchors.

tasting_clarity
1 = no tasting description
2 = very generic description
3 = some sensory detail
4 = clear tasting notes
5 = vivid sensory description

popularity_alignment
1 = obscure or unrealistic recommendations
3 = acceptable mainstream wines
5 = very appropriate and widely recognized wines

regional_diversity
1 = all wines from same region
3 = moderate variety
5 = clearly diverse regions

language_tone
1 = blunt / mechanical
3 = acceptable tone
5 = engaging sommelier-style language

Be conservative with scoring.
Scores of 5 should be rare.

Return ONLY valid JSON with exactly these fields:
{
  "tasting_clarity": integer from 1 to 5,
  "popularity_alignment": integer from 1 to 5,
  "regional_diversity": integer from 1 to 5,
  "language_tone": integer from 1 to 5,
  "reasoning": "short explanation"
}

Do not add any other fields.
Do not include overall_score.
Do not include evaluation.
"""

JUDGE_PROMPT_B = """
You are a critical evaluator for a wine recommendation assistant.

Be strict and skeptical when scoring.

If information is missing or generic, prefer lower scores.

tasting_clarity
1 = no tasting detail
2 = vague or generic
3 = moderate detail
4 = clear sensory description
5 = exceptional tasting detail

popularity_alignment
1 = unrealistic recommendations
3 = acceptable wines
5 = widely recognized and highly suitable wines

regional_diversity
1 = same region
3 = some variety
5 = strong geographic diversity

language_tone
1 = blunt or mechanical
3 = acceptable tone
5 = refined sommelier-style language

Scores of 5 should be extremely rare.

Return ONLY valid JSON with exactly these fields:
{
  "tasting_clarity": integer from 1 to 5,
  "popularity_alignment": integer from 1 to 5,
  "regional_diversity": integer from 1 to 5,
  "language_tone": integer from 1 to 5,
  "reasoning": "short explanation"
}

Do not add any other fields.
Do not include overall_score.
Do not include evaluation.
"""

JUDGE_PROMPT_C = """
You are evaluating how useful the wine recommendations are for a user.

Focus on how helpful and informative the recommendations are.

tasting_clarity
1 = no description
3 = basic tasting description
5 = vivid description that helps choose the wine

popularity_alignment
1 = poor recommendations
3 = acceptable wines
5 = excellent choices for most consumers

regional_diversity
1 = same region
3 = some variety
5 = strong variety of regions

language_tone
1 = robotic language
3 = neutral tone
5 = engaging recommendation style

Return ONLY valid JSON with exactly these fields:
{
  "tasting_clarity": integer from 1 to 5,
  "popularity_alignment": integer from 1 to 5,
  "regional_diversity": integer from 1 to 5,
  "language_tone": integer from 1 to 5,
  "reasoning": "short explanation"
}

Do not add any other fields.
Do not include overall_score.
Do not include evaluation.
"""

DIMENSIONS = [
    "tasting_clarity",
    "popularity_alignment",
    "regional_diversity",
    "language_tone",
]


class JudgeClientError(RuntimeError):
    """Raised when the LLM judge client cannot produce a valid evaluation."""


def _get_client():
    """Create the OpenAI client lazily so importing this module stays safe."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise JudgeClientError("OPENAI_API_KEY env var not set.")

    from openai import OpenAI

    return OpenAI(api_key=api_key)


def _build_user_prompt(query: str, response: str, rubric: Dict[str, Any]) -> str:
    return f"""
QUERY:
{query}

MODEL RESPONSE:
{response}

RUBRIC:
{json.dumps(rubric, indent=2)}
"""


def _validate_judge_output(payload: Dict[str, Any]) -> Dict[str, Any]:
    required_keys = set(DIMENSIONS + ["reasoning"])
    missing = required_keys - set(payload.keys())
    if missing:
        raise JudgeClientError(
            f"Judge response missing required keys: {sorted(missing)}"
        )

    for dim in DIMENSIONS:
        value = payload[dim]
        if not isinstance(value, (int, float)):
            raise JudgeClientError(
                f"Judge field '{dim}' must be numeric, got {type(value).__name__}."
            )
        if value < 1 or value > 5:
            raise JudgeClientError(
                f"Judge field '{dim}' must be between 1 and 5, got {value}."
            )

    if not isinstance(payload["reasoning"], str) or not payload["reasoning"].strip():
        raise JudgeClientError("Judge field 'reasoning' must be a non-empty string.")

    return payload


def _judge_response_with_prompt(
    query: str,
    response: str,
    rubric: Dict[str, Any],
    system_prompt: str,
    model: str,
) -> Dict[str, Any]:
    client = _get_client()
    user_prompt = _build_user_prompt(query=query, response=response, rubric=rubric)

    try:
        completion = client.chat.completions.create(
            model=model,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
    except Exception as exc:
        raise JudgeClientError(f"Judge model call failed: {exc}") from exc

    content = completion.choices[0].message.content
    if not content:
        raise JudgeClientError("Judge model returned empty content.")

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        raise JudgeClientError(f"Judge returned invalid JSON: {exc}") from exc

    return _validate_judge_output(parsed)


def judge_response(
    query: str,
    response: str,
    rubric: Dict[str, Any],
    model: str = "gpt-4o-mini",
) -> Dict[str, Any]:
    """
    Run a single calibrated judge.

    This judge is an analytical signal only. It is not intended to determine
    PASS/FAIL for the evaluated system.
    """
    return _judge_response_with_prompt(
        query=query,
        response=response,
        rubric=rubric,
        system_prompt=JUDGE_PROMPT_A,
        model=model,
    )


def judge_response_ensemble(
    query: str,
    response: str,
    rubric: Dict[str, Any],
    model: str = "gpt-4o-mini",
) -> Dict[str, Any]:
    """
    Run the three-judge ensemble and return per-dimension mean/stddev plus
    individual judge outputs.

    The ensemble is intended for analysis and disagreement inspection, not as
    the operational PASS/FAIL authority.
    """
    prompts = [JUDGE_PROMPT_A, JUDGE_PROMPT_B, JUDGE_PROMPT_C]

    judges: List[Dict[str, Any]] = [
        _judge_response_with_prompt(query, response, rubric, prompt, model)
        for prompt in prompts
    ]

    mean_scores = {
        dim: round(mean(judge[dim] for judge in judges), 2)
        for dim in DIMENSIONS
    }

    stddev_scores = {
        dim: round(pstdev(judge[dim] for judge in judges), 3)
        for dim in DIMENSIONS
    }

    return {
        "individual_judges": judges,
        "ensemble_mean_scores": mean_scores,
        "ensemble_stddev_scores": stddev_scores,
    }