from __future__ import annotations

import json
import os
import statistics
from dataclasses import dataclass
from typing import Any, Dict, List

from openai import OpenAI

JUDGE_PROMPT_VERSION = "v1.0"


class JudgeClientError(RuntimeError):
    """Raised when judge evaluation fails."""


@dataclass(frozen=True)
class JudgeRole:
    name: str
    prompt_key: str


def _get_openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise JudgeClientError("OPENAI_API_KEY env var not set.")
    return OpenAI(api_key=api_key)


def _build_role_instruction(role: JudgeRole) -> str:
    if role.prompt_key == "balanced":
        return "You are a balanced evaluator. Score fairly across all rubric dimensions."
    if role.prompt_key == "strict":
        return "You are a conservative critic. Penalize weak evidence and give high scores rarely."
    if role.prompt_key == "usefulness":
        return "You are a usefulness-focused evaluator. Prioritize practical value to the end user."
    raise ValueError(f"Unsupported judge prompt key: {role.prompt_key}")


def _build_judge_prompt(
    query: str,
    response: str,
    rubric: Dict[str, Any],
    role: JudgeRole,
) -> str:
    role_instruction = _build_role_instruction(role)

    return f"""
You are evaluating a system response using a rubric.

{role_instruction}

Return valid JSON with exactly these keys:
- tasting_clarity
- popularity_alignment
- regional_diversity
- language_tone
- reasoning

Scoring rules:
- Each score must be an integer from 1 to 5
- Be conservative
- A score of 5 should be rare
- Base scores only on the provided response

Rubric:
{json.dumps(rubric, indent=2)}

User query:
{query}

System response:
{response}
""".strip()


def _call_openai_judge(
    prompt: str,
    model: str,
    temperature: float = 0.0,
) -> Dict[str, Any]:
    client = _get_openai_client()

    try:
        resp = client.chat.completions.create(
            model=model,
            temperature=temperature,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": "You are a careful evaluation judge that returns only valid JSON.",
                },
                {"role": "user", "content": prompt},
            ],
        )
    except Exception as exc:
        raise JudgeClientError(f"Judge OpenAI request failed: {exc}") from exc

    try:
        content = resp.choices[0].message.content or "{}"
        return json.loads(content)
    except Exception as exc:
        raise JudgeClientError("Failed to parse judge JSON response.") from exc


def _mean(values: List[float]) -> float:
    return round(sum(values) / len(values), 2)


def _stddev(values: List[float]) -> float:
    if len(values) < 2:
        return 0.0
    return round(statistics.pstdev(values), 3)


def _agreement_level(stddev_map: Dict[str, float]) -> str:
    max_stddev = max(stddev_map.values()) if stddev_map else 0.0
    if max_stddev < 0.5:
        return "high"
    if max_stddev < 0.8:
        return "medium"
    return "low"


def _weighted_score(scores: Dict[str, float], weights: Dict[str, float]) -> float:
    total = 0.0
    for key, weight in weights.items():
        total += scores[key] * weight
    return round(total, 2)


def judge_response(
    query: str,
    response: str,
    rubric: Dict[str, Any],
    role: JudgeRole,
    model: str = "gpt-4o-mini",
    temperature: float = 0.0,
) -> Dict[str, Any]:
    prompt = _build_judge_prompt(
        query=query,
        response=response,
        rubric=rubric,
        role=role,
    )
    result = _call_openai_judge(prompt=prompt, model=model, temperature=temperature)

    required_keys = {
        "tasting_clarity",
        "popularity_alignment",
        "regional_diversity",
        "language_tone",
        "reasoning",
    }
    missing = required_keys - set(result.keys())
    if missing:
        raise JudgeClientError(f"Judge response missing keys: {sorted(missing)}")

    return result


def judge_response_ensemble(
    query: str,
    response: str,
    rubric: Dict[str, Any],
    model: str = "gpt-4o-mini",
    temperature: float = 0.0,
) -> Dict[str, Any]:
    roles = [
        JudgeRole(name="balanced", prompt_key="balanced"),
        JudgeRole(name="strict", prompt_key="strict"),
        JudgeRole(name="usefulness", prompt_key="usefulness"),
    ]

    individual = []
    for role in roles:
        result = judge_response(
            query=query,
            response=response,
            rubric=rubric,
            role=role,
            model=model,
            temperature=temperature,
        )
        individual.append(
            {
                "judge_role": role.name,
                "scores": {
                    "tasting_clarity": result["tasting_clarity"],
                    "popularity_alignment": result["popularity_alignment"],
                    "regional_diversity": result["regional_diversity"],
                    "language_tone": result["language_tone"],
                },
                "reasoning": result["reasoning"],
            }
        )

    dimensions = [
        "tasting_clarity",
        "popularity_alignment",
        "regional_diversity",
        "language_tone",
    ]

    judge_scores = {
        dim: _mean([entry["scores"][dim] for entry in individual]) for dim in dimensions
    }
    judge_stddev = {
        dim: _stddev([entry["scores"][dim] for entry in individual]) for dim in dimensions
    }

    judge_weighted_score = _weighted_score(judge_scores, rubric["weights"])
    judge_agreement_level = _agreement_level(judge_stddev)

    return {
        "judge_scores": judge_scores,
        "judge_weighted_score": judge_weighted_score,
        "judge_stddev": judge_stddev,
        "judge_individual": individual,
        "judge_agreement_level": judge_agreement_level,
    }