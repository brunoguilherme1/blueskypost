import os
import re
import json
import time
import random
from typing import Dict, List, Any, Optional

from openai import OpenAI
from sklearn.datasets import fetch_20newsgroups


# -----------------------------
# OpenAI client
# -----------------------------

def get_openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set")
    return OpenAI(api_key=api_key)


# -----------------------------
# Cleaning helpers
# -----------------------------

def clean_article(text: str, max_chars: int = 3000) -> str:
    """
    Clean 20 Newsgroups text and truncate for GPT.
    """
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()[:max_chars]


def extract_json(text: str) -> Dict[str, Any]:
    """
    Robust JSON parser for GPT output.
    """
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())

    raise ValueError(f"Could not parse JSON:\n{text}")


# -----------------------------
# Prompt with ONE few-shot
# -----------------------------

SYSTEM_PROMPT = """
You generate synthetic Bluesky-style posts from longer forum/news-style texts.

Your task:
- Read the original text
- Rewrite it as a short Bluesky-style post
- Preserve the main topic
- Do NOT mention the gold topic label directly
- Do NOT mention 20 Newsgroups
- Make the post realistic, concise, and natural

Return ONLY valid JSON:

{
  "synthetic_post": "...",
  "expected_themes": ["...", "...", "..."],
  "post_style": "news | opinion | question | technical | debate | personal",
  "needs_search": true/false,
  "reasoning_hint": "short note explaining what context the post requires"
}
"""


FEW_SHOT = """
Example:

TOPIC LABEL:
sci.space

ARTICLE EXCERPT:
The discussion is about NASA missions, orbital mechanics, and the difficulty of navigating probes over very long distances. Small errors can become huge when spacecraft travel millions of miles.

OUTPUT:
{
  "synthetic_post": "Still wild how much precision space missions need. A tiny navigation mistake on Earth can become a massive miss when you're aiming a spacecraft across millions of miles. 🚀",
  "expected_themes": [
    "space missions require high precision",
    "small navigation errors can grow over long distances",
    "the post is about space engineering or orbital navigation"
  ],
  "post_style": "technical",
  "needs_search": false,
  "reasoning_hint": "The post is understandable from general space-engineering context."
}
"""


def generate_bluesky_post(
    client: OpenAI,
    topic_label: str,
    article_text: str,
    model: str = "gpt-4o-mini",
    max_retries: int = 3,
) -> Dict[str, Any]:
    """
    Use GPT to convert a 20 Newsgroups article into a Bluesky-style post.
    """

    user_prompt = f"""
{FEW_SHOT}

Now generate one new example.

TOPIC LABEL:
{topic_label}

ARTICLE EXCERPT:
{article_text}

OUTPUT:
"""

    last_error = None

    for attempt in range(1, max_retries + 1):
        try:
            response = client.chat.completions.create(
                model=model,
                temperature=0.4,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
            )

            content = response.choices[0].message.content.strip()
            parsed = extract_json(content)

            if "synthetic_post" not in parsed:
                raise ValueError("Missing synthetic_post")

            return parsed

        except Exception as e:
            last_error = e
            print(f"[retry {attempt}/{max_retries}] generation failed: {e}")
            time.sleep(1.5 * attempt)

    raise RuntimeError(f"Failed after retries: {last_error}")


# -----------------------------
# Sampling
# -----------------------------

def sample_by_topic(
    data,
    n_per_topic: int = 10,
    seed: int = 42,
    selected_topics: Optional[List[str]] = None,
) -> Dict[str, List[int]]:
    """
    Randomly sample N examples per topic.
    """

    rng = random.Random(seed)

    topic_to_indices = {topic: [] for topic in data.target_names}

    for idx, target_id in enumerate(data.target):
        topic = data.target_names[target_id]
        topic_to_indices[topic].append(idx)

    if selected_topics:
        topic_to_indices = {
            topic: indices
            for topic, indices in topic_to_indices.items()
            if topic in selected_topics
        }

    sampled = {}

    for topic, indices in topic_to_indices.items():
        if len(indices) <= n_per_topic:
            sampled[topic] = indices
        else:
            sampled[topic] = rng.sample(indices, n_per_topic)

    return sampled


# -----------------------------
# Main builder
# -----------------------------

def build_20news_bluesky_dataset(
    n_per_topic: int = 10,
    seed: int = 42,
    output_path: str = "evals/20news_bluesky_synthetic.json",
    model: str = "gpt-4o-mini",
    selected_topics: Optional[List[str]] = None,
    max_article_chars: int = 3000,
) -> List[Dict[str, Any]]:
    """
    Build synthetic Bluesky eval dataset from sklearn 20 Newsgroups.
    """

    print("Loading sklearn 20 Newsgroups dataset...")

    data = fetch_20newsgroups(
        subset="test",
        remove=("headers", "footers", "quotes")
    )

    sampled = sample_by_topic(
        data=data,
        n_per_topic=n_per_topic,
        seed=seed,
        selected_topics=selected_topics,
    )

    client = get_openai_client()

    examples = []
    total = sum(len(v) for v in sampled.values())
    count = 0

    print(f"Generating {total} examples...")

    for topic_label, indices in sampled.items():
        for local_idx, idx in enumerate(indices, 1):
            count += 1

            article = clean_article(
                data.data[idx],
                max_chars=max_article_chars
            )

            print(f"[{count}/{total}] Topic: {topic_label}")

            try:
                generated = generate_bluesky_post(
                    client=client,
                    topic_label=topic_label,
                    article_text=article,
                    model=model,
                )

                example = {
                    "id": f"synthetic_20news_{topic_label.replace('.', '_')}_{local_idx:03d}",
                    "category": "synthetic_20newsgroups",
                    "source_dataset": "sklearn.fetch_20newsgroups",

                    # Gold label for evaluation
                    "gold_topic": topic_label,
                    "gold_topic_id": int(data.target[idx]),

                    # No real URL because this is synthetic
                    "url": None,

                    # Main synthetic post
                    "post_text": generated["synthetic_post"],

                    # Original source for debugging/eval
                    "original_article_excerpt": article[:1500],

                    # Standard eval fields
                    "has_image": False,
                    "has_external_url": False,
                    "expected_themes": generated.get("expected_themes", []),
                    "expected_retrieval_behavior": {
                        "needs_search": generated.get("needs_search", False),
                        "reason": generated.get("reasoning_hint", "")
                    },
                    "modality_expectation": {
                        "should_use_text": True,
                        "should_use_image": False,
                        "should_use_external_url": False
                    },
                    "must_not_include": [
                        "claims the post has an image",
                        "claims there is a linked article",
                        "mentions 20 Newsgroups unless explicitly asked"
                    ],
                    "eval_focus": [
                        "topic recovery",
                        "theme coverage",
                        "grounded explanation",
                        "classification consistency"
                    ]
                }

                examples.append(example)

            except Exception as e:
                print(f"[failed] topic={topic_label}, idx={idx}: {e}")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(examples, f, indent=2, ensure_ascii=False)

    print(f"\nSaved {len(examples)} examples to: {output_path}")

    return examples