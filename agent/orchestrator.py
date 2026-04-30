"""
agent/orchestrator.py

End-to-end Bluesky Post Explainer.

Pipeline:
1. Fetch Bluesky post
2. Analyze images, if present
3. Analyze text and decide if retrieval is needed
4. Retrieve external context
5. Generate final 3-5 bullet explanation
"""

import json
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict

from agent.explainer import explain_post
from agent.text_analyzer import analyze_text
from tools.fetch_post import fetch_post
from tools.search import retrieve_context
from tools.vision import analyze_post_images, merge_image_insights


### ---------------------------------------------------------------------------
### Planner input builder
### ---------------------------------------------------------------------------

def _build_analysis_input(
    post: Any,
    image_context: str = "",
) -> str:
    """
    Build the input passed to the text planner.

    The planner uses this to decide:
    - what the post means
    - whether search is needed
    - which queries to generate
    """

    parts = [f"Post text:\n{post.text}"]

    if post.quoted_text:
        parts.append(f"Quoted post:\n{post.quoted_text}")

    if post.external_title:
        parts.append(f"External link title:\n{post.external_title}")

    if image_context:
        parts.append(f"Image context:\n{image_context}")

    return "\n\n".join(parts)


def _post_metadata(post: Any) -> Dict[str, Any]:
    """
    Convert a BlueskyPost object into JSON-safe metadata.
    """

    return {
        "url": post.url,
        "text": post.text,
        "author_handle": post.author_handle,
        "author_display_name": post.author_display_name,
        "created_at": post.created_at,
        "like_count": post.like_count,
        "repost_count": post.repost_count,
        "reply_count": post.reply_count,
        "external_url": post.external_url,
        "external_title": post.external_title,
        "quoted_text": post.quoted_text,
        "quoted_author": post.quoted_author,
        "image_count": len(post.images),
    }


### ---------------------------------------------------------------------------
### Main orchestration
### ---------------------------------------------------------------------------

def explain_bluesky_url(
    url: str,
    analyze_images: bool = True,
    reanalyze_with_images: bool = False,
) -> Dict[str, Any]:
    """
    Run the full Bluesky explanation pipeline.

    Args:
        url: Bluesky post URL.
        analyze_images: Whether to run image understanding.
        reanalyze_with_images: If True, reruns text planning after image context
            is available. This improves quality for image-heavy posts but adds
            one extra LLM call.

    Returns:
        Dictionary containing post metadata, planner output, image insights,
        retrieval context, and final explanation.
    """

    ##### Step 1: Fetch post first
    post = fetch_post(url)

    image_insights = []
    image_context = ""
    analysis: Dict[str, Any] = {}

    ##### Step 2: Run image analysis and text planning in parallel
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {}

        if analyze_images and post.images:
            futures["images"] = executor.submit(analyze_post_images, post)

        initial_analysis_input = _build_analysis_input(post)
        futures["analysis"] = executor.submit(analyze_text, initial_analysis_input)

        for key, future in futures.items():
            try:
                result = future.result()

                if key == "images":
                    image_insights = result
                    image_context = merge_image_insights(image_insights)

                elif key == "analysis":
                    analysis = result

            except Exception as exc:
                if key == "images":
                    image_insights = []
                    image_context = ""
                elif key == "analysis":
                    analysis = {
                        "draft_explanation": "Planner failed to analyze the post.",
                        "unknown_terms": [],
                        "confidence": "low",
                        "needs_search": True,
                        "queries": [post.text],
                    }

                print(f"[orchestrator warning] {key} failed: {exc}")

    ##### Optional: rerun planner with image context
    if reanalyze_with_images and image_context:
        analysis_input = _build_analysis_input(
            post=post,
            image_context=image_context,
        )
        analysis = analyze_text(analysis_input)

    ##### Step 3: Retrieve context
    retrieval_context = retrieve_context(
        needs_search=analysis.get("needs_search", False),
        queries=analysis.get("queries", []),
        external_url=post.external_url,
    )

    ##### Step 4: Final explanation
    explanation = explain_post(
        post_text=post.text,
        draft_explanation=analysis.get("draft_explanation", ""),
        author=post.author_display_name,
        created_at=post.created_at,
        quoted_text=post.quoted_text or "",
        external_url=post.external_url or "",
        external_title=post.external_title or "",
        image_context=image_context,
        retrieval_context=retrieval_context,
    )

    return {
        "post": _post_metadata(post),
        "analysis": analysis,
        "image_insights": image_insights,
        "image_context": image_context,
        "retrieval_context": retrieval_context,
        "explanation": explanation,
    }


### ---------------------------------------------------------------------------
### Local smoke test
### ---------------------------------------------------------------------------

if __name__ == "__main__":
    test_url = "https://bsky.app/profile/us.theguardian.com/post/3mkn4xj4p6725"

    result = explain_bluesky_url(
        url=test_url,
        analyze_images=True,
        reanalyze_with_images=False,
    )

    print("\nFINAL EXPLANATION:\n")
    print(result["explanation"])

    print("\nSUMMARY:\n")
    print(
        json.dumps(
            {
                "post": result["post"],
                "analysis": result["analysis"],
                "has_image_context": bool(result["image_context"]),
            },
            indent=2,
            ensure_ascii=False,
        )
    )