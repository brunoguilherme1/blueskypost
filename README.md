# 🧠 Bluesky Post Explainer

A lightweight AI agent that explains Bluesky posts by fetching the original post, analyzing text and images, retrieving external context when needed, and generating a concise explanation in 3–5 bullet points.

This project was built for the **Bluesky Post Explainer assignment**, where the goal is to create an agent that receives a Bluesky post URL, searches for relevant context, and returns a useful explanation. The assignment also expects a GitHub repo with setup instructions, design decisions, and an evaluation harness. :contentReference[oaicite:0]{index=0}

---

## 🎯 Goal

Social media posts often depend on missing context: memes, slang, recent events, quoted posts, images, screenshots, links, or niche references.

This agent helps users understand a post by answering:

- What does this post mean?
- What context is missing?
- Does it reference a meme, event, person, article, or image?
- Why is the post relevant?

---

## 🏗️ Architecture

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
