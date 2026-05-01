import { useState } from "react";

const API_URL = import.meta.env.VITE_API_URL || "";

function formatText(text) {
  if (!text) return "No text found.";
  return text;
}

function PostCard({ post }) {
  return (
    <div className="card">
      <div className="author">
        <div className="authorName">{post.author_display_name}</div>
        <div className="handle">
          @{post.author_handle} · {post.created_at}
        </div>
      </div>

      <div className="postText">{formatText(post.text)}</div>

      {post.external_url && (
        <div className="externalBox">
          <div className="externalTitle">
            {post.external_title || "External link"}
          </div>
          <div className="externalUrl">{post.external_url}</div>
        </div>
      )}

      {post.quoted_text && (
        <div className="quoteBox">
          <div className="quoteAuthor">
            Quoted @{post.quoted_author || "unknown"}
          </div>
          <div>{post.quoted_text}</div>
        </div>
      )}

      {post.images && post.images.length > 0 && (
        <div className="imageGrid">
          {post.images.map((image, index) => (
            <img
              key={`${image.cid}-${index}`}
              src={image.url}
              alt={image.alt || `Post image ${index + 1}`}
              className="postImage"
            />
          ))}
        </div>
      )}

      <div className="metrics">
        💬 {post.reply_count} replies · 🔁 {post.repost_count} reposts · ❤️{" "}
        {post.like_count} likes
      </div>
    </div>
  );
}

function ExplanationCard({ explanation }) {
  return (
    <div className="card explanationCard">
      <div className="explanationText">{explanation}</div>
    </div>
  );
}

export default function App() {
  const [url, setUrl] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function explainPost() {
    setLoading(true);
    setError("");
    setResult(null);

    try {
      const response = await fetch(`${API_URL}/explain`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          url,
          analyze_images: true,
          reanalyze_with_images: false,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Failed to explain post.");
      }

      setResult(data);
    } catch (err) {
      setError(String(err.message || err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="page">
      <section className="hero">
        <h1>Bluesky Post Explainer</h1>
        <p>
          Paste a Bluesky post URL and get a concise contextual explanation.
        </p>
      </section>

      <section className="inputRow">
        <input
          value={url}
          onChange={(event) => setUrl(event.target.value)}
          placeholder="https://bsky.app/profile/.../post/..."
        />

        <button onClick={explainPost} disabled={loading || !url.trim()}>
          {loading ? "Explaining..." : "Explain post"}
        </button>
      </section>

      {error && <div className="errorBox">{error}</div>}

      {result && (
        <section className="resultsGrid">
          <div>
            <h2>Original post</h2>
            <PostCard post={result.post} />
          </div>

          <div>
            <h2>Explanation</h2>
            <ExplanationCard explanation={result.explanation} />
          </div>
        </section>
      )}
    </main>
  );
}