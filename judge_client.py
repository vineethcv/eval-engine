from openai import OpenAI
import json
import os
from statistics import mean, pstdev

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

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

def judge_response(query, response, rubric, model="gpt-4o-mini"):
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
        model=model,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    return json.loads(completion.choices[0].message.content)

def judge_response_with_prompt(query, response, rubric, system_prompt, model):

    user_prompt = f"""
QUERY:
{query}

MODEL RESPONSE:
{response}

RUBRIC:
{json.dumps(rubric, indent=2)}
"""

    completion = client.chat.completions.create(
        model=model,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    return json.loads(completion.choices[0].message.content)

def judge_response_ensemble(query, response, rubric, model="gpt-4o-mini"):
    
    prompts = [JUDGE_PROMPT_A, JUDGE_PROMPT_B, JUDGE_PROMPT_C]

    judges = [
        judge_response_with_prompt(query, response, rubric, prompt, model)
        for prompt in prompts
    ]

    dims = [
        "tasting_clarity",
        "popularity_alignment",
        "regional_diversity",
        "language_tone",
    ]

    from statistics import mean, pstdev

    mean_scores = {
        dim: round(mean(j[dim] for j in judges), 2)
        for dim in dims
    }

    stddev_scores = {
        dim: round(pstdev(j[dim] for j in judges), 3)
        for dim in dims
    }

    return {
        "individual_judges": judges,
        "ensemble_mean_scores": mean_scores,
        "ensemble_stddev_scores": stddev_scores,
    }