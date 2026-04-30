"""
agent/explainer.py

Final explanation model for the Bluesky Post Explainer.

This module receives all available signals:
- post text
- quoted post context
- author metadata
- image insights
- external URL/article context
- search results
- draft planner interpretation

It returns 3 concise bullet points explaining the post.
"""

import os
from typing import Optional

from openai import OpenAI


### ---------------------------------------------------------------------------
### OpenAI client
### ---------------------------------------------------------------------------

def _get_client() -> OpenAI:
    """
    Create the OpenAI client from environment variables.
    """

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError("OPENAI_API_KEY not set")

    return OpenAI(api_key=api_key)


### ---------------------------------------------------------------------------
### Few-shot examples
### ---------------------------------------------------------------------------

FEW_SHOTS = """
Example 1 — Art / personal post with image

POST TEXT:
This is a watercolour of a grey heron from my local nature reserve, I painted a couple years ago. I always love how prehistoric they look!
#watercolours #greyheron #birdart

IMAGE INSIGHTS:
Image 1:
- Description: A watercolor painting of a grey heron standing in shallow water. The bird has long legs, a long pointed beak, grey and white feathers, and a soft green background.

RETRIEVED CONTEXT:
No additional context needed.

OUTPUT:
- The post is mainly sharing original artwork: a watercolor painting of a grey heron.
- The author adds personal context by saying it was inspired by a local nature reserve and painted a few years earlier.
- The hashtags signal that the intended audience includes watercolor artists, bird enthusiasts, and nature-art communities.


Example 2 — News post with external article

POST TEXT:
Thom Tillis is doubling down on his latest Trump personnel ultimatum — that he won't confirm for attorney general anyone who excuses the events of Jan. 6.

EXTERNAL LINK:
Title: Thom Tillis doubles down on his latest Trump personnel ultimatum
URL: https://www.politico.com/...

RETRIEVED CONTEXT:
Politico article about Thom Tillis saying he would not support attorney general nominees who excuse Jan. 6.

OUTPUT:
- The post is summarizing a Politico story about Senator Thom Tillis taking a hard line on Trump’s future attorney general nominees.
- The key issue is Jan. 6: Tillis is saying he will not confirm anyone for attorney general who minimizes or excuses the events of that day.
- This matters because attorney general confirmations require Senate approval, so even one Republican senator’s opposition can complicate a nomination.


Example 3 — Historical / political meme with image

POST TEXT:
If American history was taught correctly.

IMAGE INSIGHTS:
Image 1:
- Description: A historical-style illustration showing European colonizers and Indigenous people. The overlaid text says: “After they had stolen our land and killed most of our people” and “They gave us a book that says ‘Thou shalt not STEAL’ and ‘Thou shalt not KILL.’”

RETRIEVED CONTEXT:
No additional context needed.

OUTPUT:
- The post is making a political and historical critique of how colonial history is taught in the United States.
- The image contrasts European colonization of Indigenous peoples with Christian commandments against stealing and killing, highlighting what the author sees as hypocrisy.
- The phrase “If American history was taught correctly” suggests the author believes mainstream history education often softens or omits the violence of colonization.
"""


### ---------------------------------------------------------------------------
### System prompt
### ---------------------------------------------------------------------------

SYSTEM_PROMPT = """
You are an AI agent that explains short Bluesky/social media posts.

Your goal:
- Explain what the post means
- Add missing background context
- Use the provided evidence
- Return exactly 3 concise bullet points

You may receive:
- post text
- author information
- quoted post context
- image descriptions
- external article/link content
- search results
- draft interpretation

Rules:
- Use external article/link content as the strongest source when available
- Use image insights when they explain the meaning, meme, screenshot, artwork, or visual reference
- Use search results to explain unknown terms, recent events, slang, technical references, or claims
- Do not hallucinate facts
- If evidence is weak, say the context is unclear
- Keep the tone neutral, concise, and factual
- Output ONLY the final 3 bullets
"""


### ---------------------------------------------------------------------------
### Main explanation function
### ---------------------------------------------------------------------------

def explain_post(
    post_text: str,
    draft_explanation: str,
    author: str = "",
    created_at: str = "",
    quoted_text: str = "",
    external_url: str = "",
    external_title: str = "",
    image_context: str = "",
    retrieval_context: str = "",
    model: Optional[str] = None,
) -> str:
    """
    Generate the final explanation for a Bluesky/social post.

    Args:
        post_text: Original post text.
        draft_explanation: Planner-generated initial interpretation.
        author: Display name or handle.
        created_at: Post timestamp.
        quoted_text: Quoted post context, if any.
        external_url: External link URL, if any.
        external_title: External link title, if any.
        image_context: Image descriptions produced by vision.py.
        retrieval_context: Search or external URL context.
        model: Optional OpenAI model override.

    Returns:
        Exactly 3 concise bullet points as a string.
    """

    client = _get_client()
    model_name = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    user_prompt = f"""
{FEW_SHOTS}

Now explain this post.

POST TEXT:
{post_text}

AUTHOR:
{author or "Unknown"}

CREATED AT:
{created_at or "Unknown"}

QUOTED POST CONTEXT:
{quoted_text or "None"}

EXTERNAL LINK:
Title: {external_title or "None"}
URL: {external_url or "None"}

IMAGE INSIGHTS:
{image_context or "No image insights."}

DRAFT UNDERSTANDING:
{draft_explanation or "No draft understanding."}

RETRIEVED CONTEXT:
{retrieval_context or "No retrieved context."}

TASK:
Explain the post in exactly 3 bullet points.
Each bullet should add useful context, not just repeat the post.
"""

    response = client.chat.completions.create(
        model=model_name,
        temperature=0.2,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )

    return response.choices[0].message.content.strip()


### ---------------------------------------------------------------------------
### Local smoke test
### ---------------------------------------------------------------------------

if __name__ == "__main__":
    example_output = explain_post(
        post_text="If American history was taught correctly.",
        draft_explanation="The post is likely a critique of how American history is taught.",
        image_context=(
            "Image 1:\n"
            "- Description: A historical-style illustration about colonization "
            "with text contrasting land theft and violence with commandments "
            "against stealing and killing."
        ),
    )

    print(example_output)