# eval-engine/llm_client.py
from __future__ import annotations

import os
from typing import Optional


class LLMClientError(RuntimeError):
    pass

PROMPT_VERSION = "v2.0-3item-notes-region"

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
        "- Output EXACTLY 3 items and nothing else.\n"
        "- Each item MUST be a red wine under €50.\n"
        "- Each item MUST include: Wine name, Country/Region, Price, and a short tasting note.\n"
        "- The tasting note must be 8–20 words and include at least TWO sensory descriptors "
        "(e.g., cherry, plum, blackberry, vanilla, oak, tannins, acidity, medium-bodied).\n"
        "- Use the euro symbol '€' for prices.\n\n"
        "FORMAT (exactly 3 lines):\n"
        "1. <Wine name> (<Country/Region>) - €<number> - <tasting note>\n"
        "2. <Wine name> (<Country/Region>) - €<number> - <tasting note>\n"
        "3. <Wine name> (<Country/Region>) - €<number> - <tasting note>\n"
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