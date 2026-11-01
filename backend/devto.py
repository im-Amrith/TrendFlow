import time
import requests
from datetime import datetime, timedelta, timezone

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


USER_AGENT = "TrendFlow/1.0 (+https://github.com/im-Amrith/TrendFlow)"
RETRY_WAITS = (20, 60, 120)  # seconds before each retry of a 429/5xx response


def _find_existing(api_key: str, title: str):
    """URL of an article with this exact title created in the last day, if any.

    Dev.to sometimes answers 500 even though it saved the article, so this is checked
    before every retry to make sure a retry never creates a duplicate post."""
    try:
        response = requests.get(
            "https://dev.to/api/articles/me/all", params={"per_page": 10},
            headers={"api-key": api_key, "User-Agent": USER_AGENT}, timeout=15,
        )
        if response.status_code != 200:
            return None
        cutoff = datetime.now(timezone.utc) - timedelta(days=1)
        for a in response.json():
            created = a.get("published_at") or a.get("created_at")
            recent = not created or datetime.fromisoformat(created.replace("Z", "+00:00")) > cutoff
            if a.get("title", "").strip() == title.strip() and recent:
                return a.get("url")
    except Exception as e:
        print(f"⚠️ Could not check for an existing article: {e}")
    return None


def publish_article(api_key: str, title: str, body_markdown: str, tags, published: bool = True) -> str:
    """Creates a Dev.to article and returns its URL. Raises RuntimeError on failure.

    Rate limits (429) and server errors (5xx) are retried with backoff. Before each retry it checks
    whether the failed request actually created the article. The last retry is sent without the
    series field, which is the only optional part of the payload."""
    if not body_markdown.strip():
        raise RuntimeError("Post has no content to publish")

    article = {
        "title": title[:128],  # Dev.to rejects titles over 128 characters
        "body_markdown": body_markdown,
        "published": published,
        "tags": clean_tags(tags),
        "series": "TrendFlow AI Digest",
    }
    headers = {"api-key": api_key, "Content-Type": "application/json", "User-Agent": USER_AGENT}

    print(f"Sending article to Dev.to: '{article['title']}' tags={article['tags']}")
    last_error = ""
    for attempt in range(len(RETRY_WAITS) + 1):
        try:
            response = requests.post(DEVTO_ARTICLES_URL, json={"article": article}, headers=headers, timeout=60)
            status, text = response.status_code, response.text[:500]
        except requests.RequestException as e:  # timeouts and dropped connections are retryable too
            status, text = 0, str(e)

        if status == 201:
            return response.json()["url"]

        last_error = f"Dev.to Error ({status}): {text}"
        print(f"❌ {last_error}")
        retryable = status == 0 or status == 429 or status >= 500
        if not retryable or attempt == len(RETRY_WAITS):
            break

        wait = RETRY_WAITS[attempt]
        print(f"   ⏳ Retrying in {wait}s (attempt {attempt + 2} of {len(RETRY_WAITS) + 1})...")
        time.sleep(wait)
        existing = _find_existing(api_key, article["title"])
        if existing:
            print(f"   ✅ The earlier request did create the article: {existing}")
            return existing
        if attempt == len(RETRY_WAITS) - 1:
            article.pop("series", None)
            print("   ↪️ Last attempt: sending without the series field")

    raise RuntimeError(last_error)


def published_within(api_key: str, hours: float) -> bool:
    """True if the account published an article in the last `hours` hours."""
    response = requests.get(
        "https://dev.to/api/articles/me/published", params={"per_page": 5},
        headers={"api-key": api_key}, timeout=15,
    )
    response.raise_for_status()
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    return any(
        a.get("published_at") and datetime.fromisoformat(a["published_at"].replace("Z", "+00:00")) > cutoff
        for a in response.json()
    )


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
