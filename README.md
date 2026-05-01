# Bluesky Post Explainer

A React + FastAPI application that explains Bluesky posts by fetching the original post, analyzing text and images, retrieving external context when needed, and returning a short explanation.

Stack:

- **Frontend:** React + Vite
- **Backend:** FastAPI
- **Agent layer:** Python orchestration modules
- **Retrieval:** DuckDuckGo Search via `ddgs`
- **Image understanding:** OpenAI vision model
- **Evaluation:** Real Bluesky evaluation harness + synthetic 20 Newsgroups benchmark

## Live Demo

The deployed app is available here:

[https://bluesky-explainer-666450702512.us-central1.run.app/](https://bluesky-explainer-666450702512.us-central1.run.app/)


Paste a Bluesky post URL in the app to run the full explanation flow from the browser.

## Index

1. [Goal](#goal)
2. [Architecture](#architecture)
3. [Repository Structure](#repository-structure)
4. [Main Components](#main-components)
5. [Setup](#setup)
6. [Run the App Locally](#run-the-app-locally)
7. [Evaluation](#evaluation)

## Goal

Social media posts often depend on context that is not visible in the text alone. A short post may reference a meme, current event, public figure, image, external article, quoted post, or previous conversation.

Given a Bluesky post URL, the app produces a short explanation that answers:

* What does the post mean?
* What context is missing?
* Does it reference a meme, event, person, article, image, or quoted post?
* Why is the post relevant?

The final output is a concise bullet-point explanation.

## Architecture

```text
User enters Bluesky URL
        ↓
React frontend
        ↓
FastAPI backend
        ↓
Fetch Bluesky post
        ↓
Analyze text + images
        ↓
Search external context when needed
        ↓
Generate final explanation
        ↓
Return concise bullets
```

<img width="1672" height="941" alt="image" src="https://github.com/user-attachments/assets/4b72bfb1-379b-4cad-840a-62c8864c9182" />

## Repository Structure

```text
blue_post/
├── backend/
│   └── app.py
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── App.jsx
│       ├── main.jsx
│       └── styles.css
├── agent/
│   ├── __init__.py
│   ├── text_analyzer.py
│   ├── explainer.py
│   └── orchestrator.py
├── tools/
│   ├── __init__.py
│   ├── fetch_post.py
│   ├── search.py
│   └── vision.py
├── evals/
│   ├── test_posts.json
│   ├── run_evals.py
│   ├── generate_20news_bluesky_dataset.py
│   └── run_20news_evals.py
├── requirements.txt
├── Dockerfile
├── .env.example
└── README.md
```

## Main Components

### 1. React Frontend

The frontend is built with **React + Vite**. It lets the user paste a Bluesky post URL, sends the request to FastAPI, and displays the original post beside the explanation.

Main files:

```text
frontend/src/App.jsx
frontend/src/main.jsx
frontend/src/styles.css
```

The UI includes:

* URL input
* loading state while the pipeline runs
* original Bluesky post card
* post text, author, metrics, image, quoted post, and external link if available
* explanation card next to the original post
* error message if the backend fails

In local development, the frontend runs on:

```text
http://localhost:5173
```

It calls the backend through:

```env
VITE_API_URL=http://localhost:8080
```

In the Docker build, React is compiled into `frontend/dist` and served by FastAPI.

### 2. FastAPI Backend

The backend exposes the explanation pipeline through REST endpoints.

Main file:

```text
backend/app.py
```

Main endpoints:

```text
GET  /health
POST /explain
```

The `/explain` endpoint receives:

```json
{
  "url": "https://bsky.app/profile/.../post/...",
  "analyze_images": true,
  "reanalyze_with_images": false
}
```

It returns the fetched post, planner output, image context, retrieved context, and final explanation.

In local development, the backend runs on:

```text
http://localhost:8080
```

### 3. Bluesky Post Fetching

The system uses the public Bluesky / AT Protocol API to fetch:

* Post text
* Author metadata
* Like, repost, and reply counts
* External link previews
* Quoted post context
* Image metadata

Main file:

```text
tools/fetch_post.py
```

This module parses the Bluesky URL, resolves the handle to a DID, retrieves the post thread, and returns a structured post object.

### 4. Text Planner

The planner reads the post and decides:

* What the post likely means
* What context may be missing
* Whether external search is required
* Which search queries should be generated

Main file:

```text
agent/text_analyzer.py
```

The planner returns structured JSON:

```json
{
  "draft_explanation": "...",
  "unknown_terms": [],
  "confidence": "high | medium | low",
  "needs_search": true,
  "queries": []
}
```

### 5. Search and Retrieval

When external context is needed, the system runs DuckDuckGo Search through `ddgs`, filters noisy results, deduplicates URLs, and formats snippets for the final explanation model.

Main file:

```text
tools/search.py
```

The retrieval layer supports:

* direct external URL fetching
* DuckDuckGo search
* lightweight relevance filtering
* result deduplication
* LLM-ready context formatting

### 6. Image Understanding

For posts with images, the agent downloads Bluesky image CIDs and analyzes them with an OpenAI vision model.

Main file:

```text
tools/vision.py
```

The vision module extracts:

* visible objects
* people or scenes
* visible text
* meme or cultural cues
* why the image matters for the post

### 7. Final Explanation

The final explanation model receives all available signals:

* Post text
* Author metadata
* Quoted post context
* Image insights
* External link context
* Search results
* Draft planner interpretation

Main file:

```text
agent/explainer.py
```

The output is a short bullet-point explanation.

### 8. Orchestration

The orchestrator connects all pieces into one pipeline.

Main file:

```text
agent/orchestrator.py
```

Pipeline:

```text
Bluesky URL
   ↓
fetch_post
   ↓
text_analyzer
   ↓
vision analysis, if images exist
   ↓
search/retrieval, if needed
   ↓
explainer
   ↓
final explanation
```

When images are available, the image context is added before the final explanation is generated.

<img width="1672" height="941" alt="image" src="https://github.com/user-attachments/assets/f49535c9-dcc1-48b6-a6ae-363757305676" />

## Setup

### 1. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

For Windows PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Install frontend dependencies

```bash
cd frontend
npm install
cd ..
```

### 4. Create `.env`

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
APP_TITLE=Bluesky Post Explainer
APP_ENV=local
```

Do not commit `.env` to GitHub.

### 5. Create frontend `.env`

For local React development, create:

```text
frontend/.env
```

with:

```env
VITE_API_URL=http://localhost:8080
```

This tells React to call the local FastAPI backend.

## Run the App Locally

### Option 1: Run FastAPI and React separately

Start the backend from the project root:

```bash
uvicorn backend.app:app --host 0.0.0.0 --port 8080 --reload
```

Check the health endpoint:

```text
http://localhost:8080/health
```

Expected response:

```json
{"status": "ok"}
```

Start the frontend in a second terminal:

```bash
cd frontend
npm run dev
```

Open:

```text
http://localhost:5173
```

Paste a Bluesky post URL:

```text
https://bsky.app/profile/<handle>/post/<post_id>
```

The app fetches the original post, analyzes text and images, searches for context when needed, and returns a concise explanation.

### Option 2: Run the production build with Docker

```bash
docker build -t bluesky-explainer .
docker run --env-file .env -p 8080:8080 bluesky-explainer
```

Open:

```text
http://localhost:8080
```

<img width="670" height="414" alt="image" src="https://github.com/user-attachments/assets/7a9f3abe-1d24-42e1-bfdd-411b96c42a4e" />


## Evaluation

The evaluation checks whether the agent produces explanations that are useful, grounded, concise, and faithful to the original post.

The project uses two evaluation tracks:

1. **Bluesky Eval Harness**
2. **20 Newsgroups Evaluation**

The Bluesky harness evaluates the real product flow, including post fetching, retrieval decisions, image usage, quoted-post context, and external links.

The 20 Newsgroups evaluation tests whether the explanation pipeline still works on posts created from labeled source documents, without relying on Bluesky metadata.

## Evaluation Input Format

Each evaluation example is stored as JSON.

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

| Field                         | Meaning                                                              |
| ----------------------------- | -------------------------------------------------------------------- |
| `id`                          | Unique evaluation example ID                                         |
| `category`                    | Type of post, such as news, meme, image post, or synthetic benchmark |
| `url`                         | Bluesky URL for real-post evaluation; `null` for synthetic examples  |
| `post_text`                   | Text that the agent must explain                                     |
| `has_image`                   | Whether the post contains an image                                   |
| `has_external_url`            | Whether the post contains a linked article or external source        |
| `expected_themes`             | Key ideas the explanation should cover                               |
| `expected_retrieval_behavior` | Whether search should be used and why                                |
| `modality_expectation`        | Whether text, image, or external link context should be used         |
| `must_not_include`            | Claims that would count as hallucinations or unsupported output      |
| `eval_focus`                  | What the example is testing                                          |

## Evaluation Output Format

Each evaluator writes a JSON result with the example ID, agent output, rule-based metrics, LLM-as-judge metrics, and aggregate summary statistics.

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

The `agent_result` stores the full pipeline output: post metadata, planner analysis, retrieved context, image context, and final explanation. The evaluator then attaches rule-based and LLM-as-judge metrics to each example.

## Evaluation Metrics

The evaluation combines rule-based checks with LLM-as-judge scoring.

### Rule-Based Metrics

Rule-based metrics are computed directly from the output and the expected JSON fields. They check formatting, theme coverage, retrieval behavior, modality usage, and forbidden content.

| Metric                   | Description                                                          |
| ------------------------ | -------------------------------------------------------------------- |
| `theme_coverage_rule`    | Measures whether expected themes appear in the generated explanation |
| `format_compliance_rule` | Checks whether the output follows the expected bullet format         |
| `bullet_count`           | Counts the number of bullets in the final explanation                |
| `no_forbidden_content`   | Checks whether the model avoided forbidden claims                    |
| `retrieval_rule_score`   | Checks whether retrieval was used when expected                      |
| `image_rule_score`       | Checks whether image context was used when expected                  |
| `external_rule_score`    | Checks whether external URLs were used when expected                 |
| `rule_score`             | Weighted aggregate score over rule-based metrics                     |

### LLM-as-Judge Metrics

LLM-as-judge metrics cover behavior that is harder to measure with exact matching.

| Metric                | Description                                                            |
| --------------------- | ---------------------------------------------------------------------- |
| `theme_coverage`      | Whether the explanation covers the expected meaning                    |
| `groundedness`        | Whether the explanation is supported by the post and retrieved context |
| `hallucination_score` | Whether unsupported claims were introduced                             |
| `usefulness`          | Whether the explanation helps the reader understand the post           |
| `format_compliance`   | Whether the response follows the expected bullet format                |
| `retrieval_success`   | Whether retrieved context was useful or correctly skipped              |
| `image_usage`         | Whether images were used when relevant                                 |
| `external_url_usage`  | Whether linked content was used when relevant                          |
| `quote_thread_usage`  | Whether quoted post or thread context was used when relevant           |
| `topic_confidence`    | Confidence of topic prediction in the 20 Newsgroups evaluation         |
| `llm_judge_score`     | Weighted aggregate score from the LLM judge                            |

## Eval Harness: Bluesky Posts

The Bluesky evaluation harness uses 12 Bluesky post examples with expected outputs. This track tests the full application flow on realistic social-media examples.

It covers:

* News and data posts
* Slang and meme references
* Posts with images
* Posts with external links
* Posts requiring search
* Posts where retrieval should not be used
* Numeric faithfulness
* Unsupported-claim prevention

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
<img width="1536" height="1024" alt="image" src="https://github.com/user-attachments/assets/87e302a6-9c33-417e-8829-d7c4bcbdb68b" />


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

This example checks numeric faithfulness, source awareness, retrieval behavior, and whether the explanation avoids overclaiming causality.

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

In this run, the Bluesky harness produced strong groundedness (`0.9083`) and usefulness (`4.4167 / 5`) scores.

The average bullet count was `3`, and the rule-based format compliance score was `2`, matching the expected concise format.

The keyword-based theme coverage score was lower (`0.4333`) because strict matching can miss valid paraphrases. The LLM judge gave a higher theme coverage score (`0.8417`), which suggests that many outputs captured the intended meaning even when the wording differed.

## 20 Newsgroups Synthetic Evaluation

The main Bluesky evaluation uses real posts, so it tests the actual product flow: post fetching, images, quoted posts, links, retrieval, and explanation generation.

Real social posts are hard to label at scale, and many do not have a clear ground-truth topic. To complement the Bluesky eval, this experiment builds a **synthetic labeled benchmark** using `sklearn.datasets.fetch_20newsgroups`.

The key idea is:

```text
Labeled 20 Newsgroups article
        ↓
LLM converts article into a short Bluesky-style post
        ↓
The original 20 Newsgroups topic is kept as the gold label
        ↓
The explainer explains the synthetic post
        ↓
An evaluator checks explanation quality and whether the topic is recovered
```

This gives the evaluator a controlled dataset where every generated post has a known source topic.

### Main objective

The goal is not to train on 20 Newsgroups. The goal is to create a **synthetic evaluation dataset** that tests whether the explanation pipeline generalizes beyond handpicked Bluesky examples.

This experiment checks whether the agent can:

* explain short posts derived from longer source documents
* preserve the meaning of the original article
* avoid hallucinating images or links that do not exist
* produce useful and grounded explanations
* recover the original high-level topic from the generated post and explanation

### Dataset source

The experiment uses the `fetch_20newsgroups` dataset from scikit-learn.

Each original example has:

* article text
* numeric topic ID
* human-readable topic label

Examples of topic labels include:

```text
sci.space
sci.med
sci.crypt
rec.sport.hockey
rec.autos
comp.graphics
talk.politics.guns
talk.religion.misc
alt.atheism
soc.religion.christian
```

The builder loads the test split and removes headers, footers, and quotes:

```python
data = fetch_20newsgroups(
    subset="test",
    remove=("headers", "footers", "quotes")
)
```

This keeps the source text cleaner and reduces metadata leakage.

### Synthetic dataset construction

The synthetic dataset is created by `build_20news_eval.py`.

The generation process has five steps.

#### 1. Load 20 Newsgroups

The builder loads the dataset from scikit-learn and keeps the topic labels.

#### 2. Sample examples by topic

The function `sample_by_topic` groups examples by topic and randomly samples `n_per_topic` examples from each topic using a fixed seed.

This makes the benchmark reproducible.

Default parameters:

```python
n_per_topic = 10
seed = 42
```

The script also supports selecting a subset of topics with `selected_topics`.

#### 3. Clean and truncate source articles

Each article is cleaned before being passed to GPT:

```python
def clean_article(text: str, max_chars: int = 3000) -> str:
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()[:max_chars]
```

This removes excessive whitespace and limits the prompt size.

#### 4. Generate a Bluesky-style post

GPT receives:

* the original topic label
* the cleaned article excerpt
* one few-shot example

The model is instructed to rewrite the article as a short Bluesky-style post while preserving the main topic. It must not mention the gold label directly and must not mention 20 Newsgroups.

The generation prompt returns JSON:

```json
{
  "synthetic_post": "...",
  "expected_themes": ["...", "...", "..."],
  "post_style": "news | opinion | question | technical | debate | personal",
  "needs_search": true,
  "reasoning_hint": "short note explaining what context the post requires"
}
```

This makes each synthetic example compatible with the same evaluation schema used for real Bluesky posts.

#### 5. Save a structured JSON example

Each generated example is saved with the original topic label preserved as ground truth:

```json
{
  "id": "synthetic_20news_sci_space_001",
  "category": "synthetic_20newsgroups",
  "source_dataset": "sklearn.fetch_20newsgroups",
  "gold_topic": "sci.space",
  "gold_topic_id": 14,
  "url": null,
  "post_text": "Still wild how much precision space missions need...",
  "original_article_excerpt": "...",
  "has_image": false,
  "has_external_url": false,
  "expected_themes": [
    "space missions require high precision",
    "small navigation errors can grow over long distances",
    "the post is about space engineering or orbital navigation"
  ],
  "expected_retrieval_behavior": {
    "needs_search": false,
    "reason": "The post is understandable from general space-engineering context."
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

### Why synthetic data helps here

Synthetic data is useful here because it gives controlled ground truth. Real Bluesky posts are realistic but hard to label. The 20 Newsgroups dataset already has topic labels, so the experiment converts labeled examples into short social-media-style posts while keeping the original labels.

This lets us test things that are hard to measure with real posts alone:

* whether the explainer preserves the original topic
* whether the explanation remains grounded in the post
* whether the model can handle many domains
* whether the output format stays stable
* whether the model invents unsupported image/link context
* whether retrieval is skipped when the post is self-contained

### Evaluation pipeline

The evaluator is implemented in `eval_20news.py`.

Because the synthetic examples do not have real Bluesky URLs, this track skips the Bluesky fetching step.

The pipeline is:

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

The function `explain_synthetic_post` runs the core agent pipeline directly on the synthetic `post_text`:

```python
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
```

This isolates reasoning and explanation quality from Bluesky-specific fetching.

### Rule-based evaluation

The rule-based evaluator checks deterministic properties of the output.

It measures:

| Metric                   | Meaning                                                   |
| ------------------------ | --------------------------------------------------------- |
| `theme_coverage_rule`    | Whether expected theme keywords appear in the explanation |
| `format_compliance_rule` | Whether the output follows the expected bullet format     |
| `bullet_count`           | Number of bullets in the explanation                      |
| `no_forbidden_content`   | Whether forbidden claims were avoided                     |
| `retrieval_rule_score`   | Whether retrieval behavior matched the expected behavior  |
| `rule_score`             | Weighted aggregate of rule-based metrics                  |

For this benchmark, images and external URLs are not expected. The evaluator gives full modality scores when the explanation does not invent them.

### LLM-as-judge evaluation

The LLM judge evaluates qualitative properties that are harder to measure with keyword rules.

It receives:

* valid 20 Newsgroups topic labels
* gold topic
* synthetic post
* original article excerpt
* expected themes
* forbidden claims
* retrieved context
* generated explanation

The judge returns JSON:

```json
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
```

The main added metric is `predicted_topic`.

The judge must choose exactly one topic from the official list:

```text
alt.atheism
comp.graphics
comp.os.ms-windows.misc
comp.sys.ibm.pc.hardware
comp.sys.mac.hardware
comp.windows.x
misc.forsale
rec.autos
rec.motorcycles
rec.sport.baseball
rec.sport.hockey
sci.crypt
sci.electronics
sci.med
sci.space
soc.religion.christian
talk.politics.guns
talk.politics.mideast
talk.politics.misc
talk.religion.misc
```

The evaluator compares the predicted topic against the original `gold_topic`.

```python
topic_correct = predicted_topic == gold_topic
topic_accuracy = 1.0 if topic_correct else 0.0
```

### Final scoring

The final LLM judge score combines explanation quality and topic recovery:

```text
llm_judge_score =
  0.30 * theme_coverage
+ 0.25 * groundedness
+ 0.20 * usefulness_normalized
+ 0.10 * retrieval_success_normalized
+ 0.10 * format_compliance_normalized
+ 0.05 * topic_correct
- 0.20 * hallucination_penalty
```

This rewards explanations that are complete, grounded, useful, correctly formatted, and aligned with the original topic.

### Example

#### Source topic

```text
sci.space
```

#### Original article idea

```text
The article discusses NASA missions, orbital mechanics, and the difficulty of navigating probes over long distances.
```

#### Synthetic Bluesky post

```text
Still wild how much precision space missions need. A tiny navigation mistake on Earth can become a massive miss when you're aiming a spacecraft across millions of miles. 🚀
```

#### Expected themes

```json
[
  "space missions require high precision",
  "small navigation errors can grow over long distances",
  "the post is about space engineering or orbital navigation"
]
```

#### Agent explanation

```text
- The post is about the precision required in space missions, where small navigation errors can grow over huge distances.
- It uses a simple comparison to explain why orbital navigation and spacecraft targeting are difficult.
- The rocket emoji reinforces that the topic is space exploration and engineering.
```

#### Judge result

```json
{
  "theme_coverage": 1.0,
  "groundedness": 1.0,
  "hallucination_score": 0,
  "usefulness": 5,
  "format_compliance": 2,
  "retrieval_success": 2,
  "predicted_topic": "sci.space",
  "topic_confidence": 0.95,
  "topic_correct": true,
  "topic_accuracy": 1.0,
  "llm_judge_score": 0.95
}
```

### Reported results

A sample run with 20 examples produced:

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

The synthetic 20 Newsgroups benchmark suggests that the explanation pipeline can generalize beyond a small set of handcrafted Bluesky examples.

The high `topic_accuracy` indicates that the explanations preserved enough topic signal for the judge to recover the original source label. High `groundedness` and low `hallucination_score` suggest that explanations stayed close to the synthetic post.

The lower `retrieval_success` score is expected because many synthetic posts are self-contained. In this benchmark, the main goal is topic preservation, explanation quality, and generalization.


Together, the two evaluations cover different risks: the Bluesky harness tests product realism, while the 20 Newsgroups benchmark tests controlled generalization.
