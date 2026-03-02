# eval-engine/llm_client.py
from __future__ import annotations

import os
from typing import Optional


class LLMClientError(RuntimeError):
    pass


def respond_openai(query: str, model: str, temperature: float) -> str:
    """
    Minimal OpenAI client using the official SDK.
    Requires:
      - pip install openai
      - env var: OPENAI_API_KEY
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise LLMClientError("OPENAI_API_KEY env var not set.")

    # Lazy import so mock mode doesn't require the dependency
    from openai import OpenAI

    client = OpenAI(api_key=api_key)

    system = (
        "You are a wine recommendation assistant.\n"
        "You MUST follow the output rules exactly.\n\n"
        "OUTPUT RULES:\n"
        "- Output EXACTLY 3 lines.\n"
        "- Each line must start with '1. ', '2. ', '3. ' respectively.\n"
        "- Each line must recommend a red wine.\n"
        "- Each line MUST include a euro price using the '€' symbol (example: €24).\n"
        "- Each price MUST be <= €50.\n"
        "- Do NOT add any other text before or after the 3 lines.\n\n"
        "FORMAT (exactly 3 lines):\n"
        "1. <Wine name> - €<number>\n"
        "2. <Wine name> - €<number>\n"
        "3. <Wine name> - €<number>\n"
    )

    resp = client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": query},
        ],
    )

    return resp.choices[0].message.content or ""