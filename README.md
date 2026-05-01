# Bluesky Post Explainer

A React + FastAPI application that explains Bluesky posts with the help of an AI agent.

The user pastes a Bluesky post URL, and the system:

- fetches the original post
- displays the post in the UI
- analyzes the post text
- analyzes attached images when available
- retrieves external context when needed
- returns a short explanation in bullet points

Live app:

```text
https://bluesky-explainer-666450702512.us-central1.run.app/
```

## Why this project exists

Social posts often rely on context that is not obvious from the text alone. A post can reference a meme, a current event, a public figure, an image, an external article, or a quoted post.

The goal of this project is to make that context easier to understand.

Given a Bluesky post URL, the app answers:

- What is this post saying?
- What context is missing?
- Is there an image, link, quoted post, or external reference that matters?
- Why would someone care about this post?

The final answer is intentionally short: usually three bullet points.

## Architecture

```text
User enters Bluesky URL
        ↓
React frontend
        ↓
FastAPI backend
        ↓
Bluesky post fetcher
        ↓
Text planner
        ↓
Image analysis, if images exist
        ↓
Search / retrieval, if needed
        ↓
Final explanation
        ↓
UI displays original post + explanation
```

<img width="1672" height="941" alt="Architecture diagram" src="https://github.com/user-attachments/assets/4b72bfb1-379b-4cad-840a-62c8864c9182" />

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

### React frontend

The frontend is built with React and Vite.

It contains:

- a Bluesky URL input
- a loading state while the agent runs
- a card with the original post
- image, quoted post, and external link display when available
- a card with the final explanation
- basic error handling

Main files:

```text
frontend/src/App.jsx
frontend/src/main.jsx
frontend/src/styles.css
```

During local development, the frontend runs on:

```text
http://localhost:5173
```

It calls the backend using:

```env
VITE_API_URL=http://localhost:8080
```

In production, the React build is served by FastAPI.

### FastAPI backend

The backend exposes the explanation pipeline through a REST API.

Main file:

```text
backend/app.py
```

Endpoints:

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

### Bluesky post fetcher

The fetcher reads the Bluesky URL, resolves the handle, retrieves the post thread, and converts the result into a structured object.

Main file:

```text
tools/fetch_post.py
```

It extracts:

- post text
- author information
- reply, repost, and like counts
- external link previews
- quoted post context
- image metadata

### Text planner

The text planner decides whether the post can be explained directly or whether the agent needs more context.

Main file:

```text
agent/text_analyzer.py
```

The planner returns structured output like:

```json
{
  "draft_explanation": "...",
  "unknown_terms": [],
  "confidence": "high | medium | low",
  "needs_search": true,
  "queries": []
}
```

### Search and retrieval

Search is used only when extra context is needed.

Main file:

```text
tools/search.py
```

The retrieval layer handles:

- external URL fetching
- DuckDuckGo search through `ddgs`
- result filtering
- URL deduplication
- formatting retrieved snippets for the final explanation model

### Image understanding

When a post has images, the system downloads the image assets and sends them to an OpenAI vision model.

Main file:

```text
tools/vision.py
```

The image step looks for:

- visible objects
- visible text
- people, places, or scenes
- meme or cultural cues
- how the image changes the meaning of the post

This matters because some posts cannot be explained from text alone. In those cases, the image can carry the joke, the claim, or the missing context.

### Final explanation

The final explanation combines:

- post text
- author metadata
- quoted post context
- image context
- external link context
- retrieved search context
- planner interpretation

Main file:

```text
agent/explainer.py
```

The output is a short bullet-point explanation.

### Orchestration

The orchestrator connects the full pipeline.

Main file:

```text
agent/orchestrator.py
```

```text
Bluesky URL
   ↓
fetch_post
   ↓
text_analyzer
   ↓
vision analysis, if images exist
   ↓
search / retrieval, if needed
   ↓
explainer
   ↓
final explanation
```

Text planning and image analysis can run independently when both are needed.

<img width="1672" height="941" alt="Orchestration diagram" src="https://github.com/user-attachments/assets/f49535c9-dcc1-48b6-a6ae-363757305676" />

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

Do not commit `.env`.

### 5. Create frontend `.env`

For local React development, create:

```text
frontend/.env
```

with:

```env
VITE_API_URL=http://localhost:8080
```

## Run the App Locally

### Option 1: FastAPI and React separately

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

### Option 2: Docker

```bash
docker build -t bluesky-explainer .
docker run --env-file .env -p 8080:8080 bluesky-explainer
```

Open:

```text
http://localhost:8080
```

## Evaluation

The project has two evaluation tracks:

1. Bluesky post evaluation
2. Synthetic 20 Newsgroups evaluation

They test different things.

The Bluesky evaluation checks the real product flow: URL fetching, post metadata, images, quoted posts, links, retrieval, and explanation generation.

The 20 Newsgroups evaluation checks whether the explanation pipeline works across many topics using a controlled synthetic dataset.

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

| Field | Meaning |
|---|---|
| `id` | Unique evaluation example ID |
| `category` | Type of post, such as news, meme, image post, or synthetic benchmark |
| `url` | Bluesky URL for real-post evaluation; `null` for synthetic examples |
| `post_text` | Text that the agent must explain |
| `has_image` | Whether the post contains an image |
| `has_external_url` | Whether the post contains a linked article or external source |
| `expected_themes` | Key ideas the explanation should cover |
| `expected_retrieval_behavior` | Whether search should be used and why |
| `modality_expectation` | Whether text, image, or external link context should be used |
| `must_not_include` | Unsupported claims the explanation should avoid |
| `eval_focus` | What the example is testing |

## Metrics

The evaluation combines rule-based metrics and LLM-as-judge metrics.

### Rule-based metrics

| Metric | Description |
|---|---|
| `theme_coverage_rule` | Checks whether expected themes appear in the explanation |
| `format_compliance_rule` | Checks whether the output follows the expected bullet format |
| `bullet_count` | Counts the number of bullets |
| `no_forbidden_content` | Checks whether forbidden claims were avoided |
| `retrieval_rule_score` | Checks whether retrieval was used when expected |
| `image_rule_score` | Checks whether image context was used when expected |
| `external_rule_score` | Checks whether external URLs were used when expected |
| `rule_score` | Weighted aggregate score over rule-based metrics |

### LLM-as-judge metrics

| Metric | Description |
|---|---|
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

## Bluesky Evaluation

The Bluesky harness uses real Bluesky post examples with expected behavior.

It covers:

- news and data posts
- slang and meme references
- image-based posts
- posts with external links
- posts where search is required
- posts where search should be skipped
- numeric faithfulness
- unsupported-claim prevention

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
search / retrieval, if needed
   ↓
explainer
   ↓
evaluation
```

<img width="1536" height="1024" alt="Evaluation diagram" src="https://github.com/user-attachments/assets/87e302a6-9c33-417e-8829-d7c4bcbdb68b" />

### Example

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

This example tests whether the agent preserves the numbers, recognizes that AAA is the cited source, triggers retrieval for time-sensitive context, and avoids unsupported causal claims.

### Sample Bluesky Eval Results

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

The main takeaway is that the real-post harness produced strong groundedness and usefulness scores. The strict keyword-based theme score was lower because it depends on exact phrasing, while the LLM judge gave a higher theme score for semantically correct explanations.

## 20 Newsgroups Synthetic Evaluation

The Bluesky evaluation is useful because it tests the real application flow. The limitation is that real social posts are difficult to label at scale.

To add a controlled benchmark, this project also builds a synthetic dataset from `sklearn.datasets.fetch_20newsgroups`.

The core idea:

```text
Labeled 20 Newsgroups article
        ↓
LLM rewrites it as a short Bluesky-style post
        ↓
Original 20 Newsgroups topic is kept as the gold label
        ↓
Explainer explains the synthetic post
        ↓
Evaluator checks explanation quality and topic recovery
```

This creates social-post-like examples while keeping a known ground-truth topic.

### Objective

The goal is not to train on 20 Newsgroups.

The goal is to test whether the explanation pipeline can generalize beyond a small set of handpicked Bluesky examples.

This benchmark checks whether the agent can:

- explain short posts derived from longer documents
- preserve the original topic
- avoid inventing images or links
- produce grounded explanations
- recover the original high-level topic from the post and explanation

### Dataset source

The experiment uses `fetch_20newsgroups` from scikit-learn.

Each example includes:

- article text
- numeric topic ID
- topic label

Example topic labels:

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

This reduces metadata leakage and keeps the source text closer to the actual article content.

### Synthetic dataset construction

The synthetic dataset is generated by:

```text
evals/generate_20news_bluesky_dataset.py
```

Process:

1. Load 20 Newsgroups.
2. Sample examples by topic using a fixed seed.
3. Clean and truncate each article.
4. Ask the LLM to rewrite the article as a short Bluesky-style post.
5. Store the generated post together with the original topic label.

Default sampling:

```python
n_per_topic = 10
seed = 42
```

Cleaning:

```python
def clean_article(text: str, max_chars: int = 3000) -> str:
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()[:max_chars]
```

The generated example follows the same structure as the real Bluesky eval examples:

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

### 20 Newsgroups evaluation pipeline

Because synthetic examples do not have real Bluesky URLs, this track skips post fetching.

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

The important part is that the same core text-analysis and explanation modules are reused.

### Topic recovery

The evaluator asks the LLM judge to choose exactly one topic from the official 20 Newsgroups labels.

Example labels:

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

The predicted topic is compared with the original `gold_topic`:

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

### Example

Source topic:

```text
sci.space
```

Synthetic post:

```text
Still wild how much precision space missions need. A tiny navigation mistake on Earth can become a massive miss when you're aiming a spacecraft across millions of miles. 🚀
```

Expected themes:

```json
[
  "space missions require high precision",
  "small navigation errors can grow over long distances",
  "the post is about space engineering or orbital navigation"
]
```

Agent explanation:

```text
- The post is about the precision required in space missions, where small navigation errors can grow over huge distances.
- It uses a simple comparison to explain why orbital navigation and spacecraft targeting are difficult.
- The rocket emoji reinforces that the topic is space exploration and engineering.
```

Judge result:

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

### Sample 20 Newsgroups Results

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

The 20 Newsgroups benchmark is mainly a generalization check.

The reported sample run suggests that the explanations preserved enough topic signal for the judge to recover the original label in most cases. It also gives a controlled way to check whether the system invents unsupported context, such as images or links, when the input does not contain them.

Together, the two evaluation tracks cover different risks:

- Bluesky evaluation tests the real user flow.
- 20 Newsgroups evaluation tests controlled topic generalization.
