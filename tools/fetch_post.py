"""
tools/fetch_post.py

Fetch a Bluesky post using the public AT Protocol API.

Returns:
- post text
- author metadata
- external link preview
- quoted post context
- image CIDs
"""

import re
from dataclasses import dataclass, field
from io import BytesIO
from typing import List, Optional

import httpx
import matplotlib.pyplot as plt
from atproto import Client
from PIL import Image


### ---------------------------------------------------------------------------
### Global configuration
### ---------------------------------------------------------------------------

BSKY_PUBLIC_API = "https://public.api.bsky.app"

# Use an explicit name to avoid collisions with OpenAI clients.
bsky_client = Client(base_url=BSKY_PUBLIC_API)


### ---------------------------------------------------------------------------
### Data models
### ---------------------------------------------------------------------------

@dataclass
class BlueskyImage:
    """
    Image metadata from a Bluesky post.

    Bluesky images are stored as CIDs.
    To display/analyze them, combine:
    - post.did
    - image.cid
    """

    alt: str
    cid: str


@dataclass
class BlueskyPost:
    """
    Structured representation of a Bluesky post.
    """

    url: str
    did: str
    text: str
    author_handle: str
    author_display_name: str
    created_at: str
    like_count: int
    repost_count: int
    reply_count: int
    images: List[BlueskyImage] = field(default_factory=list)
    external_url: Optional[str] = None
    external_title: Optional[str] = None
    quoted_text: Optional[str] = None
    quoted_author: Optional[str] = None


### ---------------------------------------------------------------------------
### URL parsing
### ---------------------------------------------------------------------------

def _parse_url(url: str) -> tuple[str, str]:
    """
    Extract handle and post rkey from a Bluesky post URL.

    Expected:
        https://bsky.app/profile/<handle>/post/<rkey>

    Returns:
        (handle, rkey)
    """

    match = re.search(r"bsky\.app/profile/([^/]+)/post/([^/?#]+)", url)

    if not match:
        raise ValueError(
            f"Invalid Bluesky URL: {url}. "
            "Expected: https://bsky.app/profile/<handle>/post/<rkey>"
        )

    return match.group(1), match.group(2)


### ---------------------------------------------------------------------------
### Core fetch
### ---------------------------------------------------------------------------

def fetch_post(url: str) -> BlueskyPost:
    """
    Fetch one public Bluesky post and return a structured BlueskyPost.
    """

    handle, rkey = _parse_url(url)

    ##### Resolve handle -> DID
    profile = bsky_client.app.bsky.actor.get_profile({"actor": handle})
    did = profile.did

    ##### Fetch post thread
    at_uri = f"at://{did}/app.bsky.feed.post/{rkey}"
    thread = bsky_client.app.bsky.feed.get_post_thread({"uri": at_uri})

    post = thread.thread.post
    record = post.record

    ##### Extract embedded metadata
    images = _extract_images(record)
    external_url, external_title = _extract_external(record)
    quoted_text, quoted_author = _extract_quote(record)

    return BlueskyPost(
        url=url,
        did=did,
        text=getattr(record, "text", "") or "",
        author_handle=getattr(post.author, "handle", "") or "",
        author_display_name=(
            getattr(post.author, "display_name", None)
            or getattr(post.author, "handle", "")
            or ""
        ),
        created_at=getattr(record, "created_at", "") or "",
        like_count=getattr(post, "like_count", 0) or 0,
        repost_count=getattr(post, "repost_count", 0) or 0,
        reply_count=getattr(post, "reply_count", 0) or 0,
        images=images,
        external_url=external_url,
        external_title=external_title,
        quoted_text=quoted_text,
        quoted_author=quoted_author,
    )


### ---------------------------------------------------------------------------
### Embed extractors
### ---------------------------------------------------------------------------

def _extract_images(record) -> List[BlueskyImage]:
    """
    Extract image CIDs and alt text from supported Bluesky embeds.

    Supports:
    - app.bsky.embed.images
    - app.bsky.embed.recordWithMedia
    """

    embed = getattr(record, "embed", None)

    if not embed:
        return []

    images: List[BlueskyImage] = []

    ##### Direct image embed
    raw_images = getattr(embed, "images", None)

    ##### Quote + media embed
    if not raw_images:
        media = getattr(embed, "media", None)
        raw_images = getattr(media, "images", None) if media else None

    for img in raw_images or []:
        image_obj = getattr(img, "image", None)

        if not image_obj:
            continue

        try:
            cid = image_obj.ref.link if hasattr(image_obj, "ref") else str(image_obj)

            images.append(
                BlueskyImage(
                    alt=getattr(img, "alt", "") or "",
                    cid=cid,
                )
            )

        except Exception:
            continue

    return images


def _extract_external(record) -> tuple[Optional[str], Optional[str]]:
    """
    Extract external link preview URL and title, if present.
    """

    embed = getattr(record, "embed", None)

    if not embed:
        return None, None

    external = getattr(embed, "external", None)

    if not external:
        return None, None

    return (
        getattr(external, "uri", None),
        getattr(external, "title", None),
    )


def _extract_quote(record) -> tuple[Optional[str], Optional[str]]:
    """
    Extract quoted post text and quoted author handle, if present.
    """

    embed = getattr(record, "embed", None)

    if not embed:
        return None, None

    embedded_record = getattr(embed, "record", None)

    if not embedded_record:
        return None, None

    ##### recordWithMedia may wrap the actual record
    inner = getattr(embedded_record, "record", embedded_record)

    quoted_value = getattr(inner, "value", None)
    quoted_author = getattr(inner, "author", None)

    text = (
        getattr(quoted_value, "text", None)
        or getattr(inner, "text", None)
    )

    author = getattr(quoted_author, "handle", None)

    return text, author


### ---------------------------------------------------------------------------
### Image helpers
### ---------------------------------------------------------------------------

def build_image_url(did: str, cid: str) -> str:
    """
    Build a Bluesky CDN URL from DID + CID.
    """

    return f"https://cdn.bsky.app/img/feed_thumbnail/plain/{did}/{cid}@jpeg"


def download_image(did: str, cid: str) -> bytes:
    """
    Download image bytes from Bluesky CDN.
    """

    image_url = build_image_url(did, cid)

    response = httpx.get(
        image_url,
        timeout=15,
        follow_redirects=True,
    )
    response.raise_for_status()

    return response.content


def show_images(post: BlueskyPost) -> None:
    """
    Display post images using PIL + matplotlib.

    Useful for notebooks / Colab debugging.
    """

    if not post.images:
        print("No images found.")
        return

    for index, img in enumerate(post.images, 1):
        try:
            image_bytes = download_image(post.did, img.cid)
            image = Image.open(BytesIO(image_bytes))

            plt.figure(figsize=(6, 6))
            plt.imshow(image)
            plt.axis("off")
            plt.title(img.alt or f"Image {index}")
            plt.show()

        except Exception as exc:
            print(f"Failed to load image {index} CID={img.cid}: {exc}")


### ---------------------------------------------------------------------------
### Local smoke test
### ---------------------------------------------------------------------------

if __name__ == "__main__":
    test_url = "https://bsky.app/profile/katdevittwrites.bsky.social/post/3mkn43kbaw62n"

    post = fetch_post(test_url)

    print("\nTEXT:\n", post.text)
    print("\nAUTHOR:", post.author_display_name)
    print("\nEXTERNAL URL:", post.external_url)
    print("\nEXTERNAL TITLE:", post.external_title)
    print("\nIMAGES:", post.images)

    show_images(post)