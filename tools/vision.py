"""
tools/vision.py

Analyze Bluesky post images using GPT-4o vision.

Bluesky images are represented by:
- post.did
- image.cid

This module downloads image bytes using tools.fetch_post.download_image
and sends the image to the OpenAI vision model.
"""

import base64
import os
from typing import Any, Dict, List

from openai import OpenAI

from tools.fetch_post import download_image


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
### Image encoding helpers
### ---------------------------------------------------------------------------

def _bytes_to_base64(image_bytes: bytes) -> str:
    """
    Convert image bytes to a base64 string for OpenAI vision input.
    """

    return base64.b64encode(image_bytes).decode("utf-8")


### ---------------------------------------------------------------------------
### Core vision analysis
### ---------------------------------------------------------------------------

VISION_PROMPT = """
Describe this image for understanding a social media post.

Focus on:
- what is happening
- visible objects, people, or scene
- visible text, if any
- meme, cultural, or symbolic meaning
- why it may matter for the post

Be concise: 2-4 sentences.
"""


def analyze_image_bytes(
    image_bytes: bytes,
    model: str | None = None,
) -> str:
    """
    Analyze one image from raw bytes using an OpenAI vision model.

    Args:
        image_bytes: Raw image bytes.
        model: Optional OpenAI model override.

    Returns:
        Concise image description.
    """

    client = _get_client()
    model_name = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    try:
        image_base64 = _bytes_to_base64(image_bytes)

        response = client.chat.completions.create(
            model=model_name,
            temperature=0,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": VISION_PROMPT},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            },
                        },
                    ],
                }
            ],
        )

        return response.choices[0].message.content.strip()

    except Exception as exc:
        print(f"[vision error] failed to analyze image bytes: {exc}")
        return ""


### ---------------------------------------------------------------------------
### Bluesky post image analysis
### ---------------------------------------------------------------------------

def analyze_post_images(
    post: Any,
    model: str | None = None,
) -> List[Dict[str, str]]:
    """
    Analyze all images from a BlueskyPost-like object.

    Expected post fields:
        post.did
        post.images -> list of objects with img.cid and img.alt

    Returns:
        [
            {
                "cid": "...",
                "alt": "...",
                "description": "..."
            }
        ]
    """

    insights: List[Dict[str, str]] = []

    if not getattr(post, "images", None):
        return insights

    for image in post.images:
        cid = getattr(image, "cid", "")
        alt = getattr(image, "alt", "") or ""

        if not cid:
            continue

        try:
            print(f"[vision] analyzing CID: {cid}")

            ##### Download image from Bluesky CDN
            image_bytes = download_image(post.did, cid)

            ##### Analyze image with OpenAI vision
            description = analyze_image_bytes(
                image_bytes=image_bytes,
                model=model,
            )

            if description:
                insights.append(
                    {
                        "cid": cid,
                        "alt": alt,
                        "description": description,
                    }
                )

        except Exception as exc:
            print(f"[vision error] CID={cid}: {exc}")

    return insights


### ---------------------------------------------------------------------------
### Context formatting
### ---------------------------------------------------------------------------

def merge_image_insights(image_insights: List[Dict[str, str]]) -> str:
    """
    Convert image insights into a single LLM-ready context block.
    """

    if not image_insights:
        return ""

    lines: List[str] = []

    for index, image in enumerate(image_insights, 1):
        lines.append(f"Image {index}:")

        if image.get("alt"):
            lines.append(f"- Alt text: {image['alt']}")

        lines.append(f"- Description: {image.get('description', '')}")
        lines.append("")

    return "\n".join(lines).strip()


def show_image_insights(image_insights: List[Dict[str, str]]) -> None:
    """
    Print image insights for local debugging.
    """

    if not image_insights:
        print("No image insights found.")
        return

    for index, image in enumerate(image_insights, 1):
        print(f"\nIMAGE {index}")
        print("CID:", image.get("cid"))

        if image.get("alt"):
            print("ALT:", image["alt"])

        print("DESCRIPTION:", image.get("description"))


### ---------------------------------------------------------------------------
### Local smoke test
### ---------------------------------------------------------------------------

if __name__ == "__main__":
    from tools.fetch_post import fetch_post, show_images

    test_url = "https://bsky.app/profile/katdevittwrites.bsky.social/post/3mkn43kbaw62n"

    post = fetch_post(test_url)

    print("\nTEXT:\n", post.text)
    print("\nAUTHOR:", post.author_display_name)
    print("\nEXTERNAL:", post.external_url)

    show_images(post)

    image_insights = analyze_post_images(post)
    show_image_insights(image_insights)

    print("\nMERGED IMAGE CONTEXT:\n")
    print(merge_image_insights(image_insights))