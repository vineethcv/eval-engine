from __future__ import annotations

import os
from typing import Optional

from openai import OpenAI

PROMPT_VERSION = "v1.0-wine-recommendation"


class LLMClientError(RuntimeError):
    """Raised when the LLM client fails to produce a valid response."""


def _get_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise LLMClientError("OPENAI_API_KEY env var not set.")
    return OpenAI(api_key=api_key)


def respond_openai(
    query: str,
    model: str = "gpt-4o-mini",
    temperature: float = 0.0,
) -> str:
    """
    Generate a wine recommendation response using OpenAI.

    This is the generation client (not evaluation).
    The prompt is intentionally constrained to make evaluation easier.
    """

    system_prompt = """
You are a helpful wine recommendation assistant.

STRICT RULES:
- Recommend EXACTLY 3 wines
- ALL wines must be RED wines
- ALL wines must be UNDER 50 euros
- Each recommendation must include:
  - Wine name
  - Region and country
  - Approximate price in euros
  - Short tasting note

FORMAT:
1. Wine Name — Region, Country — €Price
Tasting note.

2. Wine Name — Region, Country — €Price
Tasting note.

3. Wine Name — Region, Country — €Price
Tasting note.

Do not include anything else.
"""

    client = _get_client()

    try:
        resp = client.chat.completions.create(
            model=model,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query},
            ],
        )
    except Exception as exc:
        raise LLMClientError(f"OpenAI request failed: {exc}") from exc

    try:
        content = resp.choices[0].message.content or ""
    except Exception as exc:
        raise LLMClientError("Malformed response from OpenAI.") from exc

    if not content.strip():
        raise LLMClientError("OpenAI returned empty response.")

    return content