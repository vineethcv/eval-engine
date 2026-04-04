from __future__ import annotations

import os

from openai import OpenAI
from typing import Protocol


class SystemClient(Protocol):
    def generate(self, query: str) -> str:
        ...

SYSTEM_PROMPT_VERSION = "v1.0-wine-recommendation"


class SystemClientError(RuntimeError):
    """Raised when the system-under-test client fails to produce a valid response."""


def _get_openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise SystemClientError("OPENAI_API_KEY env var not set.")
    return OpenAI(api_key=api_key)


def generate_openai_response(
    query: str,
    model: str = "gpt-4o-mini",
    temperature: float = 0.0,
) -> str:
    """
    Generate a response from the current system under test using OpenAI.

    This remains the generation client, not the evaluation layer.
    The current implementation is still wine-specific and OpenAI-backed.
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

    client = _get_openai_client()

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
        raise SystemClientError(f"OpenAI request failed: {exc}") from exc

    try:
        content = resp.choices[0].message.content or ""
    except Exception as exc:
        raise SystemClientError("Malformed response from OpenAI.") from exc

    if not content.strip():
        raise SystemClientError("OpenAI returned empty response.")

    return content

class OpenAISystemClient:
    def __init__(self, model: str, temperature: float):
        self.model = model
        self.temperature = temperature

    def generate(self, query: str) -> str:
        return generate_openai_response(
            query=query,
            model=self.model,
            temperature=self.temperature,
        )