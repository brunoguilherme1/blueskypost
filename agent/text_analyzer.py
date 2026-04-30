"""
agent/text_analyzer.py

Planner step for the Bluesky Post Explainer.

This module analyzes a short social media post and decides:
1. What the post likely means
2. What context is missing
3. Whether external search is needed
4. Which search queries should be used
"""

import json
import os
import re
from typing import Any, Dict

from openai import OpenAI


### ---------------------------------------------------------------------------
### OpenAI client
### ---------------------------------------------------------------------------

def _get_client() -> OpenAI:
    """
    Create an OpenAI client using the OPENAI_API_KEY environment variable.
    Never hardcode API keys in source code.
    """

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError("OPENAI_API_KEY not set")

    return OpenAI(api_key=api_key)


### ---------------------------------------------------------------------------
### System prompt
### ---------------------------------------------------------------------------

SYSTEM_PROMPT = """
You are an expert at understanding short social media posts (Bluesky/Twitter-like)
and identifying what external knowledge is required to explain them.

You receive:
- post text
- optional context such as quoted post text, image description, or author info

You MUST output ONLY valid JSON. Do not include markdown, comments, or extra text.

INTERNAL REASONING (DO NOT OUTPUT):

1. Knowledge:
- What does this post likely mean using your existing knowledge?

2. Observation:
- Identify unclear concepts, ambiguous references, niche terms, unfamiliar terms,
  and time-sensitive elements such as events, sports games, breaking news, or dates.

3. Uncertainty:
- Determine what cannot be reliably explained without external context.
- This includes unknown terms, missing details, and recent/current information.

4. Act:
- Decide whether external search is needed.
- If search is needed, generate high-quality queries.

QUERY RULES:

- Generate queries ONLY if needs_search = true
- Maximum 2 queries total
- Each query must map to an unknown term or uncertainty
- Queries must be short, specific, and contextual

Query design:
- meme/slang -> use "term meaning" or "term reddit"
- technical -> use "term github" or "term docs"
- event/time/sports/news/date -> include "today", "latest", year, "match", "game", "score", "result", or "news"
- person/org/place -> use direct name or "term wikipedia"
- general -> use "term explanation"

OUTPUT JSON:

{
  "draft_explanation": "...",
  "unknown_terms": [
    {
      "term": "...",
      "reason": "...",
      "recency_sensitive": true
    }
  ],
  "confidence": "high | medium | low",
  "needs_search": true,
  "queries": ["..."]
}

IMPORTANT:
- Prefer your own knowledge first
- Avoid hallucinating unknown concepts
- If confidence = high, queries MUST be empty and needs_search MUST be false
- If the post depends on recent/current information, confidence cannot be high
"""


### ---------------------------------------------------------------------------
### Few-shot examples
### ---------------------------------------------------------------------------

FEW_SHOTS = """
Example 1 — Real-time sports

Post:
"Liverpool vs PSG today is going to be insane 🔥"

Thought:
- Knowledge: Liverpool and PSG are football teams.
- Observation: "today" indicates a live or recent event.
- Uncertainty: current match details and outcome are unknown.
- Act: search for latest match information.

Output:
{
  "draft_explanation": "The post refers to a football match between Liverpool and PSG happening today, expressing excitement.",
  "unknown_terms": [
    {
      "term": "Liverpool vs PSG today",
      "reason": "match details depend on real-time information",
      "recency_sensitive": true
    }
  ],
  "confidence": "medium",
  "needs_search": true,
  "queries": [
    "Liverpool vs PSG today match",
    "Liverpool PSG latest score"
  ]
}


Example 2 — News / formal concept

Post:
"FIFA is making big changes again"

Thought:
- Knowledge: FIFA is the global football governing body.
- Observation: reference to "changes" is vague.
- Uncertainty: unclear which changes and whether they are recent.
- Act: search for recent FIFA updates.

Output:
{
  "draft_explanation": "The post refers to FIFA, the global football governing body, and suggests it is introducing changes.",
  "unknown_terms": [
    {
      "term": "FIFA changes",
      "reason": "specific changes are not defined and may be recent",
      "recency_sensitive": true
    }
  ],
  "confidence": "medium",
  "needs_search": true,
  "queries": [
    "FIFA recent changes",
    "FIFA latest news"
  ]
}


Example 3 — Meme / niche concept

Post:
"This Ralph Wiggum technique is crazy 😂"

Thought:
- Knowledge: Ralph Wiggum is a Simpsons character.
- Observation: phrase suggests a meme or niche concept.
- Uncertainty: "Ralph Wiggum technique" is not a known standard concept.
- Act: search for explanation from community sources.

Output:
{
  "draft_explanation": "The post refers to a concept called 'Ralph Wiggum technique', likely a humorous or experimental idea.",
  "unknown_terms": [
    {
      "term": "Ralph Wiggum technique",
      "reason": "unclear meme or niche concept",
      "recency_sensitive": false
    }
  ],
  "confidence": "low",
  "needs_search": true,
  "queries": [
    "Ralph Wiggum technique explanation",
    "Ralph Wiggum technique reddit"
  ]
}


Example 4 — Technical concept

Post:
"New LangChain agent loop just dropped 🔥"

Thought:
- Knowledge: LangChain is a framework for LLM applications.
- Observation: "agent loop" suggests a technical feature.
- Uncertainty: unclear what the new loop does or how it works.
- Act: search for technical documentation or examples.

Output:
{
  "draft_explanation": "The post refers to a new agent loop feature in LangChain, likely related to iterative reasoning or tool-based workflows.",
  "unknown_terms": [
    {
      "term": "LangChain agent loop",
      "reason": "specific implementation details are unclear",
      "recency_sensitive": true
    }
  ],
  "confidence": "medium",
  "needs_search": true,
  "queries": [
    "LangChain agent loop github",
    "LangChain agent loop explanation"
  ]
}


Example 5 — Slang / informal language

Post:
"That update was mid fr 😭"

Thought:
- Knowledge: "mid" and "fr" are slang terms.
- Observation: informal tone expressing opinion.
- Uncertainty: exact meanings of slang terms may vary by context.
- Act: search for slang definitions.

Output:
{
  "draft_explanation": "The post expresses dissatisfaction, saying the update was mediocre and emphasizing sincerity.",
  "unknown_terms": [
    {
      "term": "mid",
      "reason": "slang meaning may not be universally known",
      "recency_sensitive": false
    },
    {
      "term": "fr",
      "reason": "slang abbreviation meaning unclear",
      "recency_sensitive": false
    }
  ],
  "confidence": "low",
  "needs_search": true,
  "queries": [
    "mid slang meaning",
    "fr slang meaning"
  ]
}
"""


### ---------------------------------------------------------------------------
### JSON parsing helpers
### ---------------------------------------------------------------------------

def _extract_json(content: str) -> Dict[str, Any]:
    """
    Parse JSON returned by the model.
    Falls back to extracting the first JSON object if the model adds extra text.
    """

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", content, re.DOTALL)

        if match:
            return json.loads(match.group())

    raise ValueError(f"Could not parse JSON from model output:\n{content}")


def _fallback_analysis(post_text: str, content: str = "") -> Dict[str, Any]:
    """
    Safe fallback when JSON parsing fails.
    Defaults to search because unstructured output is unreliable.
    """

    return {
        "draft_explanation": content or "The post could not be confidently analyzed.",
        "unknown_terms": [
            {
                "term": post_text[:120],
                "reason": "analysis output was not valid JSON",
                "recency_sensitive": False,
            }
        ],
        "confidence": "low",
        "needs_search": True,
        "queries": [post_text[:200]],
    }


### ---------------------------------------------------------------------------
### Main planner function
### ---------------------------------------------------------------------------

def analyze_text(
    post_text: str,
    model: str = "gpt-4o-mini",
) -> Dict[str, Any]:
    """
    Analyze a post and decide whether retrieval is needed.

    Args:
        post_text: Post text plus optional context.
        model: OpenAI chat model.

    Returns:
        Dictionary with draft explanation, unknown terms, confidence,
        needs_search flag, and search queries.
    """

    client = _get_client()

    user_prompt = f"""
{FEW_SHOTS}

Now analyze this post.

Post:
{post_text}
"""

    response = client.chat.completions.create(
        model=model,
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )

    content = response.choices[0].message.content.strip()

    try:
        return _extract_json(content)
    except Exception:
        return _fallback_analysis(post_text=post_text, content=content)


### ---------------------------------------------------------------------------
### Local smoke test
### ---------------------------------------------------------------------------

if __name__ == "__main__":
    examples = [
        "This Ralph Wiggum technique is crazy 😂",
        "FIFA is making big changes again",
        "Liverpool vs PSG today 🔥",
        "That update was mid fr 😭",
    ]

    for example in examples:
        print("\nPOST:", example)
        print(json.dumps(analyze_text(example), indent=2, ensure_ascii=False))