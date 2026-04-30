# 🧠 Bluesky Post Explainer

A lightweight agent that explains Bluesky posts by fetching the original post, analyzing text and images, retrieving external context when needed, and returning a concise explanation in 3–5 bullet points.

## Live Demo

A deployed version of the application is available here:

```text
https://bluesky-explainer-666450702512.us-central1.run.app/
```

Use the live app by pasting a Bluesky post URL and running the explanation pipeline directly from the browser.

## Index

1. [Live Demo](#live-demo)
2. [Goal](#goal)
3. [Architecture](#architecture)
4. [Main Components](#main-components)
5. [Setup](#setup)
6. [Run the App](#run-the-app)
7. [Example Output](#example-output)
8. [Evaluation](#evaluation)
   - [Evaluation Input Format](#evaluation-input-format)
   - [Evaluation Output Format](#evaluation-output-format)
   - [Metrics](#metrics)
   - [Eval Harness: Bluesky Posts](#eval-harness-bluesky-posts)
   - [20 Newsgroups Evaluation](#20-newsgroups-evaluation)
   - [Final Combined Metrics](#final-combined-metrics)
9. [Design Decisions](#design-decisions)
10. [Future Improvements](#future-improvements)

## Goal

Social media posts are often difficult to understand without extra context. A short post may reference a meme, current event, public figure, image, external article, or previous conversation.

This project takes a Bluesky post URL and produces a short explanation that answers:

- What does the post mean?
- What context is missing?
- Does it reference a meme, event, person, article, image, or quoted post?
- Why is the post relevant?

## Architecture

```text
User enters Bluesky URL
        ↓
Streamlit UI
        ↓
Fetch Bluesky post
        ↓
Analyze text + images
        ↓
Search external context when needed
        ↓
Generate final explanation
        ↓
Return 3–5 concise bullets
```

<img width="1672" height="941" alt="Bluesky Post Explainer architecture" src="https://github.com/user-attachments/assets/53e0af25-51f6-4245-8d17-8d58b97e0b8e" />

## Main Components

### 1. Streamlit UI

The app provides a simple interface where the user pastes a Bluesky post URL. It fetches the original post, displays it, runs the explanation pipeline, and shows the final explanation beside the source post.

Main file:

```text
app.py
```

Run with:

```bash
streamlit run app.py
```

### 2. Bluesky Post Fetching

The system uses the public Bluesky / AT Protocol API to fetch:

- Post text
- Author metadata
- Like, repost, and reply counts
- External link previews
- Quoted post context
- Image metadata

Main file:

```text
tools/fetch_post.py
```

This module parses the Bluesky URL, resolves the handle to a DID, retrieves the post thread, and returns a structured `BlueskyPost` object.

### 3. Text Planner

The planner reads the post and decides:

- What the post likely means
- What context may be missing
- Whether external search is required
- Which search queries should be generated

Main file:

```text
agent/text_analyzer.py
```

The planner returns structured JSON with a draft interpretation, unknown terms, confidence level, retrieval decision, and search queries.

### 4. Search and Retrieval

When external context is needed, the system runs web search using DuckDuckGo Search (`ddgs`), filters irrelevant results, and formats retrieved snippets into context that can be used by the final explanation model.

Main file:

```text
tools/search.py
```

### 5. Image Understanding

For posts with images, the agent can download Bluesky image CIDs and analyze them with an OpenAI vision model. The image module extracts concise visual context, including visible objects, embedded text, meme cues, and symbolic meaning.

Main file:

```text
tools/vision.py
```

### 6. Final Explanation

The final explanation model receives all available signals:

- Post text
- Author metadata
- Quoted post context
- Image insights
- External link context
- Search results
- Draft planner interpretation

Main file:

```text
agent/explainer.py
```

The output is a short explanation in 3–5 bullets.

### 7. Orchestration

The orchestrator connects all pieces into one pipeline:

1. Fetch the Bluesky post
2. Analyze images if present
3. Analyze text and decide whether retrieval is needed
4. Retrieve external context if needed
5. Generate the final explanation

Main file:

```text
agent/orchestrator.py
```

Text planning and image analysis can run in parallel when both are needed.

<img width="1536" height="1024" alt="Agent and tools workflow" src="https://github.com/user-attachments/assets/5ce2bc20-7c60-4d7a-a0d8-8cfbe095abfe" />

## Setup

### 1. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

For Windows:

```bash
.venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

The project uses OpenAI, AT Protocol, DuckDuckGo Search, Streamlit, Pillow, Matplotlib, scikit-learn, and python-dotenv.

### 3. Create `.env`

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
APP_TITLE=Bluesky Post Explainer
```

Do not hardcode API keys in the source code.

## Run the App

### Live version

The app is already deployed and can be tested here:

```text
https://bluesky-explainer-666450702512.us-central1.run.app/
```

### Local version

From the project root:

```bash
streamlit run app.py
```

Then open:

```text
http://localhost:8501
```

Paste a Bluesky post URL:

```text
https://bsky.app/profile/<handle>/post/<post_id>
```

The app will fetch and display the original post, analyze text and images, search for context when needed, and generate a concise explanation.

## Example Output

Input:

```text
https://bsky.app/profile/example.com/post/abc123
```

Output:

```text
- The post is referencing a niche meme or cultural phrase that may not be obvious from the text alone.
- The agent searched for additional context and used the retrieved information to explain the reference.
- The explanation summarizes what the post means and why it matters in the conversation.
```

## Evaluation

The evaluation measures whether the agent produces explanations that are useful, grounded, concise, and faithful to the original post.

The project uses two evaluation tracks:

1. **Bluesky Eval Harness**: real or representative Bluesky posts with expected outputs.
2. **20 Newsgroups Evaluation**: synthetic Bluesky-style posts generated from 20 Newsgroups articles to test broader topic generalization.

The Bluesky harness evaluates the real product flow, including post fetching, retrieval decisions, image usage, quoted-post context, and external links. The 20 Newsgroups evaluation tests whether the core explanation pipeline can generalize across many domains, even without platform-specific metadata.

## Evaluation Input Format

Each evaluation example is stored as JSON. The input defines what the agent receives, which concepts the explanation should cover, and which behaviors should be checked.

```json
{
  "id": "example_id",
  "category": "example_category",
  "url": "https://bsky.app/profile/.../post/...",
  "post_text": "Original post text",
  "has_image": false,
  "has_external_url": false,
  "expected_themes": [
    "theme the explanation should mention"
  ],
  "expected_retrieval_behavior": {
    "needs_search": true,
    "reason": "why retrieval is or is not expected"
  },
  "modality_expectation": {
    "should_use_text": true,
    "should_use_image": false,
    "should_use_external_url": false
  },
  "must_not_include": [
    "claims the explanation must avoid"
  ],
  "eval_focus": [
    "main evaluation objective"
  ]
}
```

| Field | Meaning |
| --- | --- |
| `id` | Unique evaluation example ID |
| `category` | Type of post, such as news, meme, image post, or synthetic benchmark |
| `url` | Bluesky URL for real-post evaluation; `null` for synthetic examples |
| `post_text` | Text that the agent must explain |
| `has_image` | Whether the post contains an image |
| `has_external_url` | Whether the post contains a linked article or external source |
| `expected_themes` | Key ideas the explanation should cover |
| `expected_retrieval_behavior` | Whether search should be used and why |
| `modality_expectation` | Whether text, image, or external link context should be used |
| `must_not_include` | Claims that would count as hallucinations or unsupported output |
| `eval_focus` | What the example is testing |

## Evaluation Output Format

Each evaluator produces a JSON result containing the original example ID, agent output, rule-based metrics, LLM-as-judge metrics, and aggregate summary statistics.

```json
{
  "summary": {
    "num_examples": 12,
    "num_errors": 0,
    "rule_based_means": {
      "theme_coverage_rule": 0.4333,
      "format_compliance_rule": 2,
      "bullet_count": 3,
      "retrieval_rule_score": 1.5833,
      "rule_score": 0.7842
    },
    "llm_judge_means": {
      "theme_coverage": 0.8417,
      "groundedness": 0.9083,
      "hallucination_score": 0.0833,
      "usefulness": 4.4167,
      "format_compliance": 1.5,
      "retrieval_success": 1.4167,
      "llm_judge_score": 0.7822
    }
  },
  "results": [
    {
      "id": "real_news_gas_prices_001",
      "agent_result": {
        "post": {},
        "analysis": {},
        "retrieval_context": "...",
        "image_context": "",
        "explanation": "- bullet 1\n- bullet 2\n- bullet 3"
      },
      "rule_based": {},
      "llm_judge": {}
    }
  ]
}
```

The `agent_result` stores the full pipeline output: post metadata, planner analysis, retrieved context, image context, and final explanation. The evaluator then attaches deterministic and LLM-as-judge metrics to each example.

## Metrics

The evaluation combines deterministic rule-based metrics with LLM-as-judge metrics.

### Rule-Based Metrics

Rule-based metrics are computed directly from the output and expected JSON fields. They check formatting, expected theme coverage, retrieval behavior, modality usage, and forbidden content.

| Metric | Description |
| --- | --- |
| `theme_coverage_rule` | Measures whether expected themes appear in the generated explanation |
| `format_compliance_rule` | Checks whether the output follows the expected 3–5 bullet format |
| `bullet_count` | Counts the number of bullets in the final explanation |
| `no_forbidden_content` | Checks whether the model avoided forbidden claims |
| `retrieval_rule_score` | Checks whether retrieval was used when expected |
| `image_rule_score` | Checks whether image context was used when expected |
| `external_rule_score` | Checks whether external URLs were used when expected |
| `rule_score` | Weighted aggregate score over rule-based metrics |

### LLM-as-Judge Metrics

LLM-as-judge metrics evaluate qualitative behavior that is harder to measure with exact matching.

| Metric | Description |
| --- | --- |
| `theme_coverage` | Whether the explanation covers the expected meaning |
| `groundedness` | Whether the explanation is supported by the post and retrieved context |
| `hallucination_score` | Whether unsupported claims were introduced |
| `usefulness` | Whether the explanation helps the reader understand the post |
| `format_compliance` | Whether the response follows the expected bullet format |
| `retrieval_success` | Whether retrieved context was useful or correctly skipped |
| `image_usage` | Whether images were used when relevant |
| `external_url_usage` | Whether linked content was used when relevant |
| `quote_thread_usage` | Whether quoted post or thread context was used when relevant |
| `topic_confidence` | Confidence of topic prediction in the 20 Newsgroups evaluation |
| `llm_judge_score` | Weighted aggregate score from the LLM judge |

## Eval Harness: Bluesky Posts

The Bluesky evaluation harness uses 12 Bluesky post examples with expected outputs. This track tests the full application flow and focuses on realistic social-media behavior.

It covers:

- News and data posts
- Slang and meme references
- Posts with images
- Posts with external links
- Posts requiring search
- Posts where retrieval should not be used
- Numeric faithfulness
- Unsupported-claim prevention

Pipeline:

```text
Bluesky URL
   ↓
fetch_post
   ↓
text_analyzer
   ↓
vision analysis, if needed
   ↓
search/retrieval, if needed
   ↓
explainer
   ↓
evaluation
```

### Example Input JSON

```json
{
  "id": "real_news_gas_prices_001",
  "category": "news_data_post",
  "url": "https://bsky.app/profile/nbcnews.com/post/3mkpojrx3rk2u",
  "post_text": "Average U.S. gas prices per gallon on April 30, per AAA:\n\n• Regular: $4.30 (up $1.32 since war in Iran began on Feb. 28)\n• Premium: $5.16 (up $1.30 since war began)\n• Diesel: $5.50 (up $1.74 since war began)",
  "has_image": false,
  "has_external_url": false,
  "expected_themes": [
    "identifies this as a news/data post about U.S. gas prices",
    "mentions AAA as the source cited by the post",
    "explains that prices are being compared against the start of the Iran war on Feb. 28",
    "explains that diesel had the largest listed increase",
    "states that recent geopolitical conflict can affect fuel markets without overclaiming causality"
  ],
  "expected_retrieval_behavior": {
    "needs_search": true,
    "reason": "gas prices and war-related context are time-sensitive and should be verified",
    "suggested_queries": [
      "AAA gas prices April 30 regular premium diesel",
      "US gas prices Iran war Feb 28 latest"
    ]
  },
  "modality_expectation": {
    "should_use_text": true,
    "should_use_image": false,
    "should_use_external_url": false
  },
  "must_not_include": [
    "claims that the post proves the war is the only cause of price increases",
    "invented gas prices not present in the post",
    "unsupported political claims"
  ],
  "eval_focus": [
    "recency handling",
    "numeric faithfulness",
    "source-aware explanation"
  ]
}
```

This example checks whether the model preserves numeric values, recognizes the cited source, treats the topic as time-sensitive, triggers retrieval, and avoids overclaiming causality.

### Example Output JSON

```json
{
  "id": "real_news_gas_prices_001",
  "agent_result": {
    "post": {
      "url": "https://bsky.app/profile/nbcnews.com/post/3mkpojrx3rk2u",
      "text": "Average U.S. gas prices per gallon on April 30...",
      "has_image": false,
      "has_external_url": false
    },
    "analysis": {
      "draft_explanation": "The post reports U.S. gas prices and compares them with prices at the start of the Iran war.",
      "unknown_terms": [
        {
          "term": "AAA gas prices April 30",
          "reason": "price and source context are time-sensitive",
          "recency_sensitive": true
        }
      ],
      "confidence": "medium",
      "needs_search": true,
      "queries": [
        "AAA gas prices April 30 regular premium diesel",
        "US gas prices Iran war Feb 28 latest"
      ]
    },
    "retrieval_context": "Retrieved context from search results...",
    "image_context": "",
    "explanation": "- The post is a news/data update about U.S. fuel prices, citing AAA as the source.\n- It compares regular, premium, and diesel prices against the start of the Iran war on Feb. 28.\n- Diesel shows the largest listed increase, but the post should not be read as proving the war was the only cause."
  },
  "rule_based": {
    "theme_coverage_rule": 0.8,
    "format_compliance_rule": 2,
    "bullet_count": 3,
    "retrieval_rule_score": 2,
    "rule_score": 0.9
  },
  "llm_judge": {
    "theme_coverage": 0.9,
    "groundedness": 0.95,
    "hallucination_score": 0,
    "usefulness": 5,
    "format_compliance": 2,
    "retrieval_success": 2,
    "llm_judge_score": 0.92
  }
}
```

### Bluesky Eval Results

```text
Examples evaluated: 12
Errors: 0

Rule-based means:
- theme_coverage_rule: 0.4333
- format_compliance_rule: 2
- bullet_count: 3
- image_rule_score: 1.5
- external_rule_score: 2
- retrieval_rule_score: 1.5833
- rule_score: 0.7842

LLM-as-judge means:
- theme_coverage: 0.8417
- groundedness: 0.9083
- hallucination_score: 0.0833
- usefulness: 4.4167
- format_compliance: 1.5
- retrieval_success: 1.4167
- image_usage: 1.3333
- external_url_usage: 0.5
- quote_thread_usage: 0
- llm_judge_score: 0.7822
```

The Bluesky harness shows that the system produces useful and grounded explanations on realistic posts. Groundedness reached `0.9083`, and usefulness reached `4.4167 / 5`, which indicates that the explanations are generally supported by the post and retrieved context.

The average bullet count is exactly `3`, and the rule-based format compliance score is `2`, showing that the system consistently follows the concise output format.

The lower keyword-based theme coverage score (`0.4333`) is expected because strict matching can miss semantically correct explanations that use different wording. The LLM judge gives a higher theme coverage score (`0.8417`), suggesting that many outputs captured the intended meaning even when they did not match the expected phrases exactly.

## 20 Newsgroups Evaluation

The 20 Newsgroups evaluation tests whether the explanation pipeline generalizes beyond curated Bluesky examples.

The dataset builder loads articles from `sklearn.fetch_20newsgroups`, removes headers, footers, and quotes, and converts articles into short Bluesky-style posts. The synthetic posts preserve the underlying topic, but the topic label is not shown to the explainer.

This creates a broader stress test across domains such as:

- Religion
- Politics
- Sports
- Space
- Medicine
- Cryptography
- Hardware
- Software
- Autos
- Motorcycles
- Electronics

### Dataset Construction

The default configuration samples `n_per_topic = 10` with `seed = 42`. The evaluation can also be limited to a smaller subset for faster runs.

The builder supports selecting specific topics through `selected_topics`. If no topic filter is provided, examples can be sampled across all available 20 Newsgroups labels.

The synthetic post generation prompt instructs the model to preserve the main topic while avoiding direct mention of the gold label or the 20 Newsgroups dataset. This forces the explainer to infer the topic from the post content itself.

### 20 Newsgroups Input JSON

```json
{
  "id": "synthetic_20news_alt_atheism_001",
  "category": "synthetic_20newsgroups",
  "source_dataset": "sklearn.fetch_20newsgroups",
  "gold_topic": "alt.atheism",
  "gold_topic_id": 0,
  "url": null,
  "post_text": "It's fascinating how some people attribute natural disasters to moral failings. The recent earthquake was in Santa Cruz, yet the blame game started in San Francisco. 🤔",
  "original_article_excerpt": "I'm sure you are not. After the \"San Francisco\" Earthquake a couple of years ago, there was a flurry of traffic on talk.religion.misc about how this was the result of the notorious homo- this that and t'other in the City. The fact that the Earthquake was actually down the road in Santa Cruz/Watsonville didn't seem to phase them any.",
  "has_image": false,
  "has_external_url": false,
  "expected_themes": [
    "natural disasters and morality",
    "misattribution of events",
    "discussion about societal reactions to disasters"
  ],
  "expected_retrieval_behavior": {
    "needs_search": false,
    "reason": "The post reflects on societal reactions to events and can be explained from the text alone."
  },
  "modality_expectation": {
    "should_use_text": true,
    "should_use_image": false,
    "should_use_external_url": false
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
```

### 20 Newsgroups Pipeline

Synthetic examples do not have real Bluesky URLs, so this track skips `fetch_post` and runs the core reasoning pipeline directly on `post_text`.

```text
Synthetic post_text
        ↓
text_analyzer
        ↓
retrieve_context, if needed
        ↓
explainer
        ↓
rule-based evaluation
        ↓
LLM-as-judge evaluation
        ↓
topic prediction against gold_topic
```

### 20 Newsgroups Output JSON

```json
{
  "id": "synthetic_20news_alt_atheism_001",
  "gold_topic": "alt.atheism",
  "post_text": "It's fascinating how some people attribute natural disasters to moral failings...",
  "agent_result": {
    "post": {
      "text": "It's fascinating how some people attribute natural disasters to moral failings...",
      "source": "synthetic_20newsgroups"
    },
    "analysis": {
      "draft_explanation": "The post comments on how some people interpret natural disasters as moral punishment.",
      "unknown_terms": [],
      "confidence": "high",
      "needs_search": false,
      "queries": []
    },
    "retrieval_context": "",
    "image_context": "",
    "explanation": "- The post criticizes the idea that natural disasters should be interpreted as punishment for moral behavior.\n- It points out a mismatch between where the earthquake actually happened and where blame was directed.\n- The broader theme is how people sometimes use disasters to reinforce social or religious narratives."
  },
  "rule_based": {
    "theme_coverage_rule": 0.6667,
    "format_compliance_rule": 2,
    "bullet_count": 3,
    "no_forbidden_content": true,
    "retrieval_rule_score": 2,
    "rule_score": 0.8333
  },
  "llm_judge": {
    "theme_coverage": 1.0,
    "groundedness": 1.0,
    "hallucination_score": 0,
    "usefulness": 5,
    "format_compliance": 2,
    "retrieval_success": 2,
    "predicted_topic": "alt.atheism",
    "topic_confidence": 0.9,
    "gold_topic": "alt.atheism",
    "topic_correct": true,
    "topic_accuracy": 1.0,
    "llm_judge_score": 0.95
  }
}
```

### 20 Newsgroups Metrics

This evaluation adds topic-level scoring on top of explanation quality.

| Metric | Meaning |
| --- | --- |
| `predicted_topic` | Topic predicted by the LLM judge from the post and explanation |
| `gold_topic` | Original 20 Newsgroups label |
| `topic_correct` | Whether predicted topic matches the gold topic |
| `topic_accuracy` | Binary accuracy for each example |
| `topic_confidence` | Judge confidence in the predicted topic |

The evaluator uses the official list of 20 Newsgroups topic labels and requires the judge to select exactly one. It then compares `predicted_topic` with `gold_topic` to compute topic accuracy.

### 20 Newsgroups Results

```text
Examples evaluated: 20
Errors: 0

Rule-based means:
- theme_coverage_rule: 0.7667
- format_compliance_rule: 2
- bullet_count: 3
- retrieval_rule_score: 1.1
- rule_score: 0.8508

LLM-as-judge means:
- theme_coverage: 0.97
- groundedness: 0.975
- hallucination_score: 0.05
- usefulness: 4.8
- format_compliance: 1.95
- retrieval_success: 0.95
- topic_confidence: 0.9125
- llm_judge_score: 0.9143

Topic accuracy: 0.95
```

The 20 Newsgroups evaluation shows strong generalization across broader content domains. The model achieved `0.95` topic accuracy, meaning the judge recovered the correct source topic from the synthetic post and generated explanation in most cases.

Groundedness reached `0.975`, and hallucination score stayed low at `0.05`, which suggests that explanations were well supported by the synthetic post and rarely introduced unsupported claims. Usefulness reached `4.8 / 5`, indicating that the generated explanations were informative across diverse topics.

## Final Combined Metrics

| Metric | Bluesky Eval Harness | 20 Newsgroups Eval |
| --- | ---: | ---: |
| Examples evaluated | 12 | 20 |
| Errors | 0 | 0 |
| Theme coverage rule | 0.4333 | 0.7667 |
| Format compliance rule | 2.0000 | 2.0000 |
| Bullet count | 3.0000 | 3.0000 |
| Image rule score | 1.5000 | N/A |
| External rule score | 2.0000 | N/A |
| Retrieval rule score | 1.5833 | 1.1000 |
| Rule score | 0.7842 | 0.8508 |
| LLM theme coverage | 0.8417 | 0.9700 |
| Groundedness | 0.9083 | 0.9750 |
| Hallucination score | 0.0833 | 0.0500 |
| Usefulness | 4.4167 | 4.8000 |
| LLM format compliance | 1.5000 | 1.9500 |
| Retrieval success | 1.4167 | 0.9500 |
| Image usage | 1.3333 | N/A |
| External URL usage | 0.5000 | N/A |
| Quote/thread usage | 0.0000 | N/A |
| Topic confidence | N/A | 0.9125 |
| Topic accuracy | N/A | 0.9500 |
| LLM judge score | 0.7822 | 0.9143 |

## Overall Interpretation

The two evaluation tracks measure different strengths.

The **Bluesky Eval Harness** is closer to the real product setting. It tests realistic posts, retrieval decisions, image usage, external URL usage, and social-media-specific explanation quality. The results show strong groundedness and usefulness, while also identifying opportunities to improve image, quote/thread, and external URL usage.

The **20 Newsgroups Evaluation** measures broader generalization. It abstracts away platform-specific fetching and focuses on whether the explanation pipeline can handle short posts derived from diverse topics. The strong topic accuracy, groundedness, and LLM judge score suggest that the core explanation pipeline generalizes well beyond the curated Bluesky set.

Together, the evaluations show that the system can explain real social-media posts and generalize to wider topic distributions while keeping a stable format, low hallucination rate, and useful explanations.
