import requests

DEVTO_ARTICLES_URL = "https://dev.to/api/articles"


def clean_tags(tags) -> list:
    """Dev.to allows max 4 tags, lowercase alphanumeric only."""
    if not isinstance(tags, list):
        tags = []
    cleaned_tags = []
    for t in tags:
        cleaned = "".join(c for c in str(t).lower() if c.isalnum())
        if cleaned and cleaned not in cleaned_tags:
            cleaned_tags.append(cleaned)
    cleaned_tags = cleaned_tags[:3]  # Leave room for 'ai'
    if "ai" not in cleaned_tags:
        cleaned_tags.append("ai")
    return cleaned_tags


def post_content(post: dict) -> tuple:
    """Title and body for a stored post. Prefers the user-edited fields over the original generation."""
    title = post.get("title") or post.get("title_viral") or post.get("topic") or "TrendFlow AI Digest"
    body = post.get("content_markdown") or post.get("draft_content") or ""
    return title, body


def publish_article(api_key: str, title: str, body_markdown: str, tags, published: bool = True) -> str:
    """Creates a Dev.to article and returns its URL. Raises RuntimeError on failure."""
    if not body_markdown.strip():
        raise RuntimeError("Post has no content to publish")

    article_payload = {
        "article": {
            "title": title[:128],  # Dev.to rejects titles over 128 characters
            "body_markdown": body_markdown,
            "published": published,
            "tags": clean_tags(tags),
            "series": "TrendFlow AI Digest",
        }
    }
    headers = {"api-key": api_key, "Content-Type": "application/json"}

    print(f"Sending article to Dev.to: '{article_payload['article']['title']}' tags={article_payload['article']['tags']}")
    response = requests.post(DEVTO_ARTICLES_URL, json=article_payload, headers=headers, timeout=30)
    if response.status_code != 201:
        print(f"❌ Dev.to Error ({response.status_code}): {response.text}")
        raise RuntimeError(f"Dev.to Error ({response.status_code}): {response.text}")
    return response.json()["url"]


def recent_titles(api_key: str, limit: int = 30) -> list:
    """Titles of the account's recent articles (published and drafts), used to avoid repeating topics."""
    try:
        response = requests.get(
            "https://dev.to/api/articles/me/all", params={"per_page": limit},
            headers={"api-key": api_key}, timeout=15,
        )
        if response.status_code == 200:
            return [a["title"] for a in response.json()]
        print(f"⚠️ Dev.to recent articles error: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Dev.to recent articles failed: {e}")
    return []
