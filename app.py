"""
app.py

Minimal Streamlit UI for the Bluesky Post Explainer.

User flow:
1. Paste a Bluesky post URL
2. Fetch and display the original post
3. Run the agent
4. Show the explanation side by side with the post
"""

import os
from io import BytesIO

import streamlit as st
from dotenv import load_dotenv
from PIL import Image

from agent.orchestrator import explain_bluesky_url
from tools.fetch_post import fetch_post, download_image


### ---------------------------------------------------------------------------
### App setup
### ---------------------------------------------------------------------------

load_dotenv()

st.set_page_config(
    page_title=os.getenv("APP_TITLE", "Bluesky Post Explainer"),
    page_icon="🧠",
    layout="wide",
)


### ---------------------------------------------------------------------------
### Helpers
### ---------------------------------------------------------------------------

def display_compact_post(post) -> None:
    """
    Render a compact Bluesky-like post card.
    """

    with st.container(border=True):
        ##### Author
        st.markdown(
            f"""
            **{post.author_display_name}**  
            <span style="color: #6b7280;">@{post.author_handle} · {post.created_at}</span>
            """,
            unsafe_allow_html=True,
        )

        ##### Text
        st.markdown(post.text.replace("\n", "  \n") or "_No text found._")

        ##### External link preview
        if post.external_url:
            st.markdown(
                f"""
                <div style="
                    border: 1px solid #e5e7eb;
                    border-radius: 12px;
                    padding: 12px;
                    margin-top: 10px;
                    background-color: #f9fafb;
                ">
                    <strong>{post.external_title or "External link"}</strong><br>
                    <span style="color: #6b7280;">{post.external_url}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        ##### Quoted post
        if post.quoted_text:
            st.markdown(
                f"""
                <div style="
                    border-left: 3px solid #d1d5db;
                    padding-left: 12px;
                    margin-top: 10px;
                    color: #374151;
                ">
                    <strong>Quoted @{post.quoted_author or "unknown"}</strong><br>
                    {post.quoted_text}
                </div>
                """,
                unsafe_allow_html=True,
            )

        ##### Images
        if post.images:
            for index, image_meta in enumerate(post.images, 1):
                try:
                    image_bytes = download_image(post.did, image_meta.cid)
                    image = Image.open(BytesIO(image_bytes))

                    st.image(
                        image,
                        caption=image_meta.alt or None,
                        use_container_width=True,
                    )

                except Exception as exc:
                    st.warning(f"Could not display image {index}: {exc}")

        ##### Engagement metrics
        st.caption(
            f"💬 {post.reply_count} replies · "
            f"🔁 {post.repost_count} reposts · "
            f"❤️ {post.like_count} likes"
        )


def display_explanation(result: dict) -> None:
    """
    Render the final explanation card.
    """

    with st.container(border=True):
        st.markdown(result.get("explanation", "_No explanation generated._"))


### ---------------------------------------------------------------------------
### Main UI
### ---------------------------------------------------------------------------

st.title("🧠 Bluesky Post Explainer")
st.caption("Paste a Bluesky post URL and get a concise contextual explanation.")

url = st.text_input(
    "Bluesky post URL",
    placeholder="https://bsky.app/profile/.../post/...",
)

run_button = st.button("Explain post", type="primary")


if run_button:
    if not url.strip():
        st.warning("Please paste a Bluesky post URL.")
        st.stop()

    if not os.getenv("OPENAI_API_KEY"):
        st.error("OPENAI_API_KEY is not set. Add it to your .env file.")
        st.stop()

    try:
        ##### Fetch post and run explanation
        with st.spinner("Fetching post and generating explanation..."):
            post = fetch_post(url.strip())

            result = explain_bluesky_url(
                url=url.strip(),
                analyze_images=True,
                reanalyze_with_images=False,
            )

        ##### Side-by-side layout
        left_col, right_col = st.columns([1, 1], gap="large")

        with left_col:
            st.markdown("### Original post")
            display_compact_post(post)

        with right_col:
            st.markdown("### Explanation")
            display_explanation(result)

    except Exception as exc:
        st.error(f"Failed to explain post: {exc}")