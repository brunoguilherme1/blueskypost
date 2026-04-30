# 🧠 Bluesky Post Explainer

A lightweight AI agent that explains Bluesky posts by fetching the original post, analyzing text and images, retrieving external context when needed, and generating a concise explanation in 3–5 bullet points.

This project was built for the **Bluesky Post Explainer assignment**, where the agent must take a Bluesky post URL, search for relevant context, and return useful explanations. The expected submission includes a GitHub repo with the agent, an evaluation harness with 10+ Bluesky posts and expected outputs, and a README with setup instructions and design decisions. :contentReference[oaicite:0]{index=0}

## Index

1. [Goal](#goal)  
2. [Architecture](#architecture)  
3. [Main Components](#main-components)  
4. [Setup](#setup)  
5. [Run the App](#run-the-app)  
6. [Example Output](#example-output)  
7. [Evaluation](#evaluation)  
   - [Eval Harness: 10+ Bluesky Posts with Expected Outputs](#eval-harness-10-bluesky-posts-with-expected-outputs)  
   - [20 Newsgroups Evaluation](#20-newsgroups-evaluation)  
8. [Evaluation Metrics](#evaluation-metrics)  
9. [Design Decisions](#design-decisions)  
10. [Future Improvements](#future-improvements)  

## Goal

Social media posts often depend on missing context: memes, slang, recent events, quoted posts, images, screenshots, links, or niche references.

This agent helps users understand a post by answering:

- What does this post mean?
- What context is missing?
- Does it reference a meme, event, person, article, or image?
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
Search external context if needed
        ↓
Generate final explanation
        ↓
Return 3–5 concise bullets
````

## Main Components

### 1. Streamlit UI

The app provides a simple interface where the user pastes a Bluesky post URL. It fetches the original post, displays it, runs the agent, and shows the explanation side by side. 

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

* Post text
* Author metadata
* Like / repost / reply counts
* External link previews
* Quoted post context
* Image metadata

Main file:

```text
tools/fetch_post.py
```

This module parses the Bluesky URL, resolves the handle to a DID, retrieves the post thread, and returns a structured `BlueskyPost` object. 

### 3. Text Planner

The planner analyzes the post and decides:

* What the post likely means
* What context is missing
* Whether external search is required
* Which search queries should be generated

It returns structured JSON containing a draft explanation, unknown terms, confidence level, search decision, and queries. 

Main file:

```text
agent/text_analyzer.py
```

### 4. Search and Retrieval

If the planner decides that external context is needed, the system runs web search using DuckDuckGo Search (`ddgs`), filters irrelevant results, and formats the retrieved snippets into LLM-ready context. 

Main file:

```text
tools/search.py
```

### 5. Image Understanding

For posts with images, the agent can download Bluesky image CIDs and analyze them using an OpenAI vision model. The image module produces concise visual context such as visible objects, text, meme meaning, or symbolic context. 

Main file:

```text
tools/vision.py
```

### 6. Final Explanation

The final explanation model receives all available signals:

* Post text
* Author metadata
* Quoted post context
* Image insights
* External link context
* Search results
* Draft planner interpretation

It returns a concise explanation in bullet points. 

Main file:

```text
agent/explainer.py
```

### 7. Orchestration

The orchestrator connects all pieces into one pipeline:

1. Fetch Bluesky post
2. Analyze images if present
3. Analyze text and decide whether search is needed
4. Retrieve external context
5. Generate final explanation

Main file:

```text
agent/orchestrator.py
```

The orchestrator also runs text planning and image analysis in parallel when possible. 

## Setup

### 1. Create virtual environment

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

The project uses dependencies such as OpenAI, AT Protocol, DuckDuckGo Search, Streamlit, Pillow, Matplotlib, scikit-learn, and python-dotenv. 

### 3. Create `.env`

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
APP_TITLE=Bluesky Post Explainer
```

Never hardcode API keys in the source code.

## Run the App

From the project root:

```bash
streamlit run app.py
```

Then open:

```text
http://localhost:8501
```

Paste a Bluesky post URL like:

```text
https://bsky.app/profile/<handle>/post/<post_id>
```

The app will:

1. Fetch and display the original post
2. Analyze text and images
3. Search for context when needed
4. Generate a concise explanation

## Example Output

Input:

```text
https://bsky.app/profile/example.com/post/abc123
```

Output:

```text
- The post is referencing a niche meme or cultural phrase that may not be obvious from the text alone.
- The agent searched for additional context and used the retrieved information to explain the reference.
- The final explanation summarizes what the post means and why it matters in the current conversation.
```

## Evaluation

The project includes two evaluation tracks:

1. **Eval Harness: 10+ Bluesky posts with expected outputs**
2. **20 Newsgroups Evaluation**

The first evaluation track focuses on real Bluesky-style posts and checks whether the agent can explain actual social content with expected themes, retrieval behavior, image usage, and external URL usage.

The second evaluation track uses synthetic Bluesky-style posts generated from the 20 Newsgroups dataset to evaluate topic recovery, theme coverage, groundedness, and classification consistency at a broader scale.

## Eval Harness: 10+ Bluesky Posts with Expected Outputs

This evaluation uses curated Bluesky post examples. Each example includes:

* A real or representative Bluesky post URL
* The post text
* Whether the post has images
* Whether the post has an external URL
* Expected themes
* Expected retrieval behavior
* Modality expectations
* Forbidden claims
* Evaluation focus

The evaluator runs the full agent pipeline on each example and compares the generated explanation against the expected behavior.

Main evaluator file:

```text
eval.py
```

The evaluator checks expected themes, forbidden content, modality usage, retrieval behavior, and final explanation quality. 

### Example JSON: Bluesky Eval Harness

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

### What this evaluates

This harness is designed to verify whether the agent can:

* Explain real Bluesky posts
* Use retrieval when the content is time-sensitive
* Preserve numeric facts from the post
* Avoid unsupported claims
* Use images when relevant
* Use external URLs when relevant
* Produce a clean 3–5 bullet explanation

### Run Bluesky Eval Harness

```bash
python eval.py
```

### Final Mean Metrics

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

### Interpretation

The Bluesky harness shows that the system performs well on groundedness and usefulness while maintaining clean output formatting. The average bullet count is exactly 3, matching the required explanation style. The rule score of `0.7842` indicates that the agent generally follows expected behavior across theme coverage, retrieval, modality usage, and forbidden-content checks.

The LLM-as-judge score of `0.7822` suggests the explanations are usually useful and grounded, but there is still room to improve image usage, external URL usage, and quote/thread context handling.

## 20 Newsgroups Evaluation

The 20 Newsgroups evaluation converts longer forum/news-style texts into synthetic Bluesky-style posts. This allows the project to test explanation quality across many domains, including religion, politics, sports, science, hardware, software, medicine, space, and more.

The dataset builder uses `sklearn.fetch_20newsgroups`, samples examples by topic, and uses an LLM to rewrite each longer article into a realistic short Bluesky-style post. The generated dataset includes the original gold topic, expected themes, retrieval expectations, and forbidden claims. 

Main files:

```text
build_20news_eval.py
eval_20news.py
```

The 20 Newsgroups evaluator runs the same core explanation pipeline without fetching a real Bluesky URL. It then evaluates rule-based metrics, LLM-as-judge metrics, and topic prediction accuracy against the original gold topic. 

### Build the Synthetic Dataset

```bash
python build_20news_eval.py
```

This generates a JSON file like:

```text
evals/20news_bluesky_synthetic.json
```

### Example JSON: 20 Newsgroups Synthetic Eval

```json
{
  "id": "synthetic_20news_alt_atheism_001",
  "category": "synthetic_20newsgroups",
  "source_dataset": "sklearn.fetch_20newsgroups",
  "gold_topic": "alt.atheism",
  "gold_topic_id": 0,
  "url": null,
  "post_text": "It's fascinating how some people attribute natural disasters to moral failings. The recent earthquake was in Santa Cruz, yet the blame game started in San Francisco. 🤔",
  "original_article_excerpt": "I'm sure you are not. After the \"San Francisco\" Earthquake \na couple of years ago, there was a flurry of traffic on \ntalk.religion.misc about how this was the result of the \nnotorious homo- this that and t'other in the City.\n\nThe fact that the Earthquake was actually down the road in\nSanta Cruz/Watsonville didn't seem to phase them any.",
  "has_image": false,
  "has_external_url": false,
  "expected_themes": [
    "natural disasters and morality",
    "misattribution of events",
    "discussion about societal reactions to disasters"
  ],
  "expected_retrieval_behavior": {
    "needs_search": false,
    "reason": "The post reflects on societal reactions to events, making it relatable without needing specific context."
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

### What this evaluates

This evaluation checks whether the agent can:

* Recover the likely topic behind a short social-style post
* Explain the post without seeing the original topic label
* Cover expected themes
* Avoid forbidden claims
* Maintain groundedness
* Decide correctly whether retrieval is needed
* Support broader domain coverage beyond the curated Bluesky examples

### Run 20 Newsgroups Evaluation

```bash
python eval_20news.py
```

### Final 20News Mean Metrics

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

### Interpretation

The 20 Newsgroups evaluation shows strong generalization across different topics. The model achieved a topic accuracy of `0.95`, meaning it was able to recover the correct source topic for most synthetic posts. The high groundedness score of `0.975` and low hallucination score of `0.05` suggest that the generated explanations were strongly supported by the post and context.

The rule-based score of `0.8508` indicates solid alignment with expected themes and output formatting. The LLM-as-judge score of `0.9143` shows that the explanations were generally useful, grounded, and well-formatted.

## Evaluation Metrics

| Metric              | Description                                                      |
| ------------------- | ---------------------------------------------------------------- |
| Theme Coverage      | Whether the explanation covers the expected meaning              |
| Groundedness        | Whether the explanation is supported by post/context             |
| Hallucination Score | Whether unsupported claims were introduced                       |
| Usefulness          | Whether the explanation helps the user understand the post       |
| Format Compliance   | Whether the answer follows the 3–5 bullet format                 |
| Retrieval Success   | Whether search was used correctly when needed                    |
| Image Usage         | Whether image context was used when relevant                     |
| External URL Usage  | Whether linked article/context was used when relevant            |
| Quote Thread Usage  | Whether quoted post/thread context was used when relevant        |
| Topic Accuracy      | Whether the predicted topic matches the gold 20 Newsgroups topic |

## Design Decisions

### Planner-first architecture

The agent first analyzes the post before searching. This avoids unnecessary retrieval when the post is already understandable.

### Search only when needed

The planner returns `needs_search = true` only when the post includes unknown terms, current events, niche references, slang, or incomplete context.

### Multimodal support

Images are analyzed when present, which helps explain memes, screenshots, artwork, and visual references.

### Structured final output

The final explanation is constrained to concise bullet points so the user gets a fast and readable answer.

### Evaluation-focused design

The project includes both curated Bluesky examples and synthetic benchmark evaluation to measure explanation quality, groundedness, retrieval behavior, and robustness across different post types.

## Future Improvements

* Add citations directly in the final explanation
* Support more social platforms beyond Bluesky
* Add model comparison across GPT-4o, GPT-4o-mini, Gemini, and Claude
* Add cached retrieval to reduce repeated searches
* Improve quote/thread context handling
* Improve external URL usage when linked content is important
* Add user feedback scoring for explanation quality
* Deploy the app to Cloud Run or Streamlit Community Cloud

## Author

Bruno Gomes

GitHub: [https://github.com/brunoguilherme1](https://github.com/brunoguilherme1)

```
```
