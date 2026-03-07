from openai import OpenAI
import json
import os

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

JUDGE_PROMPT_VERSION = "v1.0"


def judge_response(query, response, rubric):
    system_prompt = """
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

        Return ONLY JSON with:

        {
        "tasting_clarity": int,
        "popularity_alignment": int,
        "regional_diversity": int,
        "language_tone": int,
        "reasoning": "short explanation"
        }
    """

    user_prompt = f"""
QUERY:
{query}

MODEL RESPONSE:
{response}

RUBRIC:
{json.dumps(rubric, indent=2)}
"""

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    return json.loads(completion.choices[0].message.content)