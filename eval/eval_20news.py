"""
evals/run_20news_evals.py

Evaluation for synthetic Bluesky-style posts generated from sklearn 20 Newsgroups.

It evaluates:
- rule-based metrics
- LLM-as-judge metrics
- topic prediction accuracy against gold_topic
- mean metrics at the end
"""

import os
import re
import json
from typing import Dict, List, Any, Optional
from statistics import mean
from openai import OpenAI

from text_analyzer import analyze_text
from search import retrieve_context
from explainer import explain_post


# ─────────────────────────────────────────────────────────────────────────────
# OpenAI client
# ─────────────────────────────────────────────────────────────────────────────

def get_openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set")
    return OpenAI(api_key=api_key)


# ─────────────────────────────────────────────────────────────────────────────
# Utilities
# ─────────────────────────────────────────────────────────────────────────────

def load_json(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data: Any, path: str) -> None:
    output_dir = os.path.dirname(path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def safe_mean(values: List[float]) -> float:
    values = [v for v in values if v is not None]
    return mean(values) if values else 0.0


def normalize_text(text: str) -> str:
    return (text or "").lower()


def count_bullets(text: str) -> int:
    return sum(
        1 for line in (text or "").splitlines()
        if line.strip().startswith(("-", "•", "*"))
    )


def extract_json(text: str) -> Dict[str, Any]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())

    raise ValueError(f"Could not parse JSON:\n{text}")


# ─────────────────────────────────────────────────────────────────────────────
# Topic labels
# ─────────────────────────────────────────────────────────────────────────────

TWENTY_NEWS_TOPICS = [
    "alt.atheism",
    "comp.graphics",
    "comp.os.ms-windows.misc",
    "comp.sys.ibm.pc.hardware",
    "comp.sys.mac.hardware",
    "comp.windows.x",
    "misc.forsale",
    "rec.autos",
    "rec.motorcycles",
    "rec.sport.baseball",
    "rec.sport.hockey",
    "sci.crypt",
    "sci.electronics",
    "sci.med",
    "sci.space",
    "soc.religion.christian",
    "talk.politics.guns",
    "talk.politics.mideast",
    "talk.politics.misc",
    "talk.religion.misc",
]


# ─────────────────────────────────────────────────────────────────────────────
# Run explainer for synthetic post
# ─────────────────────────────────────────────────────────────────────────────

def explain_synthetic_post(post_text: str) -> Dict[str, Any]:
    """
    Runs the same core pipeline, but without fetch_post.
    """

    analysis = analyze_text(post_text)

    retrieval_context = retrieve_context(
        needs_search=analysis.get("needs_search", False),
        queries=analysis.get("queries", []),
        external_url=None,
    )

    explanation = explain_post(
        post_text=post_text,
        draft_explanation=analysis.get("draft_explanation", ""),
        author="synthetic_20newsgroups",
        created_at="",
        quoted_text="",
        external_url="",
        external_title="",
        image_context="",
        retrieval_context=retrieval_context,
    )

    return {
        "post": {
            "text": post_text,
            "source": "synthetic_20newsgroups",
        },
        "analysis": analysis,
        "retrieval_context": retrieval_context,
        "image_context": "",
        "explanation": explanation,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Rule-based evaluator
# ─────────────────────────────────────────────────────────────────────────────

def rule_based_eval(
    example: Dict[str, Any],
    agent_result: Dict[str, Any]
) -> Dict[str, Any]:

    explanation = agent_result.get("explanation", "")
    explanation_lower = normalize_text(explanation)

    expected_themes = example.get("expected_themes", [])
    must_not_include = example.get("must_not_include", [])

    # 1. Format compliance
    bullet_count = count_bullets(explanation)

    if 3 <= bullet_count <= 5:
        format_compliance = 2
    elif bullet_count > 0:
        format_compliance = 1
    else:
        format_compliance = 0

    # 2. Lightweight expected theme coverage
    covered_themes = []
    missed_themes = []

    for theme in expected_themes:
        theme_words = [
            w for w in re.findall(r"\w+", theme.lower())
            if len(w) > 4
        ]

        if not theme_words:
            continue

        hits = sum(1 for w in theme_words if w in explanation_lower)
        coverage_ratio = hits / len(theme_words)

        if coverage_ratio >= 0.35:
            covered_themes.append(theme)
        else:
            missed_themes.append(theme)

    theme_coverage_rule = (
        len(covered_themes) / len(expected_themes)
        if expected_themes else 0.0
    )

    # 3. Forbidden content
    forbidden_hits = [
        phrase for phrase in must_not_include
        if phrase and phrase.lower() in explanation_lower
    ]

    no_forbidden_content = len(forbidden_hits) == 0

    # 4. Retrieval behavior
    expected_needs_search = example.get(
        "expected_retrieval_behavior", {}
    ).get("needs_search")

    actual_needs_search = agent_result.get("analysis", {}).get("needs_search")

    if expected_needs_search is None:
        retrieval_rule_score = 1
    elif expected_needs_search == actual_needs_search:
        retrieval_rule_score = 2
    else:
        retrieval_rule_score = 0

    # 5. Since 20news has no images / external URLs
    image_rule_score = 2
    external_rule_score = 2

    rule_score = (
        0.35 * theme_coverage_rule
        + 0.20 * (format_compliance / 2)
        + 0.20 * (1.0 if no_forbidden_content else 0.0)
        + 0.15 * (retrieval_rule_score / 2)
        + 0.05 * (image_rule_score / 2)
        + 0.05 * (external_rule_score / 2)
    )

    return {
        "theme_coverage_rule": round(theme_coverage_rule, 4),
        "format_compliance_rule": format_compliance,
        "bullet_count": bullet_count,
        "no_forbidden_content": no_forbidden_content,
        "forbidden_hits": forbidden_hits,
        "retrieval_rule_score": retrieval_rule_score,
        "image_rule_score": image_rule_score,
        "external_rule_score": external_rule_score,
        "rule_score": round(rule_score, 4),
    }


# ─────────────────────────────────────────────────────────────────────────────
# LLM-as-judge + topic prediction
# ─────────────────────────────────────────────────────────────────────────────

JUDGE_SYSTEM_PROMPT = """
You evaluate an AI system that explains synthetic Bluesky-style posts.

You also predict which 20 Newsgroups topic the post/explanation belongs to.

Return ONLY valid JSON:

{
  "theme_coverage": 0.0,
  "groundedness": 0.0,
  "hallucination_score": 0,
  "usefulness": 1,
  "format_compliance": 0,
  "retrieval_success": 0,
  "predicted_topic": "",
  "topic_confidence": 0.0,
  "comments": ""
}

Scoring guide:
- theme_coverage: 0.0 to 1.0
- groundedness: 0.0 to 1.0
- hallucination_score: 0 = none, 1 = minor, 2 = major
- usefulness: 1 to 5
- format_compliance: 0 = bad, 1 = partial, 2 = perfect 3-5 bullets
- retrieval_success: 0 = bad, 1 = partial, 2 = useful/not needed
- predicted_topic must be exactly one label from the provided topic list
- topic_confidence: 0.0 to 1.0
"""


def llm_judge_eval_20news(
    example: Dict[str, Any],
    agent_result: Dict[str, Any],
    model: str = "gpt-4o-mini"
) -> Dict[str, Any]:

    client = get_openai_client()

    prompt = f"""
VALID TOPIC LABELS:
{json.dumps(TWENTY_NEWS_TOPICS, indent=2)}

GOLD TOPIC:
{example.get("gold_topic")}

SYNTHETIC POST:
{example.get("post_text")}

ORIGINAL ARTICLE EXCERPT:
{example.get("original_article_excerpt", "")[:2000]}

EXPECTED THEMES:
{json.dumps(example.get("expected_themes", []), indent=2, ensure_ascii=False)}

MUST NOT INCLUDE:
{json.dumps(example.get("must_not_include", []), indent=2, ensure_ascii=False)}

RETRIEVED CONTEXT:
{agent_result.get("retrieval_context", "")[:3000]}

GENERATED EXPLANATION:
{agent_result.get("explanation", "")}

Evaluate the explanation and predict the topic.
"""

    response = client.chat.completions.create(
        model=model,
        temperature=0,
        messages=[
            {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    )

    result = extract_json(response.choices[0].message.content.strip())

    predicted_topic = result.get("predicted_topic", "")
    gold_topic = example.get("gold_topic")

    topic_correct = predicted_topic == gold_topic

    usefulness_norm = result.get("usefulness", 0) / 5
    retrieval_norm = result.get("retrieval_success", 0) / 2
    format_norm = result.get("format_compliance", 0) / 2
    hallucination_penalty = result.get("hallucination_score", 0) / 2

    final_score = (
        0.30 * result.get("theme_coverage", 0)
        + 0.25 * result.get("groundedness", 0)
        + 0.20 * usefulness_norm
        + 0.10 * retrieval_norm
        + 0.10 * format_norm
        + 0.05 * (1.0 if topic_correct else 0.0)
        - 0.20 * hallucination_penalty
    )

    result["gold_topic"] = gold_topic
    result["topic_correct"] = topic_correct
    result["topic_accuracy"] = 1.0 if topic_correct else 0.0
    result["llm_judge_score"] = round(max(final_score, 0.0), 4)

    return result


# ─────────────────────────────────────────────────────────────────────────────
# Aggregation
# ─────────────────────────────────────────────────────────────────────────────

def aggregate_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    valid_results = [r for r in results if "error" not in r]

    if not valid_results:
        return {
            "num_examples": 0,
            "num_errors": len(results),
            "rule_based_means": {},
            "llm_judge_means": {},
            "topic_accuracy": 0.0,
        }

    rule = [r["rule_based"] for r in valid_results]
    judge = [r["llm_judge"] for r in valid_results if r.get("llm_judge")]

    summary = {
        "num_examples": len(valid_results),
        "num_errors": len(results) - len(valid_results),
        "rule_based_means": {
            "theme_coverage_rule": round(safe_mean([r["theme_coverage_rule"] for r in rule]), 4),
            "format_compliance_rule": round(safe_mean([r["format_compliance_rule"] for r in rule]), 4),
            "bullet_count": round(safe_mean([r["bullet_count"] for r in rule]), 4),
            "retrieval_rule_score": round(safe_mean([r["retrieval_rule_score"] for r in rule]), 4),
            "rule_score": round(safe_mean([r["rule_score"] for r in rule]), 4),
        },
        "llm_judge_means": {},
        "topic_accuracy": 0.0,
    }

    if judge:
        summary["llm_judge_means"] = {
            "theme_coverage": round(safe_mean([j["theme_coverage"] for j in judge]), 4),
            "groundedness": round(safe_mean([j["groundedness"] for j in judge]), 4),
            "hallucination_score": round(safe_mean([j["hallucination_score"] for j in judge]), 4),
            "usefulness": round(safe_mean([j["usefulness"] for j in judge]), 4),
            "format_compliance": round(safe_mean([j["format_compliance"] for j in judge]), 4),
            "retrieval_success": round(safe_mean([j["retrieval_success"] for j in judge]), 4),
            "topic_confidence": round(safe_mean([j.get("topic_confidence", 0) for j in judge]), 4),
            "llm_judge_score": round(safe_mean([j["llm_judge_score"] for j in judge]), 4),
        }

        summary["topic_accuracy"] = round(
            safe_mean([j["topic_accuracy"] for j in judge]),
            4,
        )

    return summary


def print_summary(summary: Dict[str, Any]) -> None:
    print("\n" + "=" * 70)
    print("FINAL 20NEWS MEAN METRICS")
    print("=" * 70)

    print(f"Examples evaluated: {summary.get('num_examples', 0)}")
    print(f"Errors: {summary.get('num_errors', 0)}")

    print("\nRule-based means:")
    for k, v in summary.get("rule_based_means", {}).items():
        print(f"- {k}: {v}")

    if summary.get("llm_judge_means"):
        print("\nLLM-as-judge means:")
        for k, v in summary.get("llm_judge_means", {}).items():
            print(f"- {k}: {v}")

    print(f"\nTopic accuracy: {summary.get('topic_accuracy', 0.0)}")


# ─────────────────────────────────────────────────────────────────────────────
# Main runner
# ─────────────────────────────────────────────────────────────────────────────

def run_20news_evals(
    dataset_path: str = "evals/20news_bluesky_synthetic.json",
    output_path: str = "evals/results/20news_eval_results.json",
    use_llm_judge: bool = True,
    judge_model: str = "gpt-4o-mini",
    limit: Optional[int] = None,
) -> Dict[str, Any]:

    dataset = load_json(dataset_path)

    if limit:
        dataset = dataset[:limit]

    all_results = []
    total = len(dataset)

    for i, example in enumerate(dataset, 1):
        example_id = example.get("id", "unknown_id")
        gold_topic = example.get("gold_topic", "unknown_topic")

        print(f"Example {i}/{total}: {example_id} | gold_topic={gold_topic}")

        try:
            agent_result = explain_synthetic_post(example["post_text"])

            rule_result = rule_based_eval(example, agent_result)

            judge_result = None
            if use_llm_judge:
                judge_result = llm_judge_eval_20news(
                    example=example,
                    agent_result=agent_result,
                    model=judge_model,
                )

                print(
                    f"  predicted_topic={judge_result.get('predicted_topic')} "
                    f"| correct={judge_result.get('topic_correct')}"
                )

            all_results.append({
                "id": example_id,
                "gold_topic": gold_topic,
                "post_text": example.get("post_text"),
                "agent_result": agent_result,
                "rule_based": rule_result,
                "llm_judge": judge_result,
            })

        except Exception as e:
            print(f"  ERROR: {e}")

            all_results.append({
                "id": example_id,
                "gold_topic": gold_topic,
                "post_text": example.get("post_text"),
                "error": str(e),
            })

        partial_output = {
            "summary": aggregate_results(all_results),
            "results": all_results,
        }
        save_json(partial_output, output_path)

    summary = aggregate_results(all_results)

    final_output = {
        "summary": summary,
        "results": all_results,
    }

    save_json(final_output, output_path)

    print_summary(summary)

    return final_output