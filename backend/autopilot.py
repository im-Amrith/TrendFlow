"""
Autopilot: picks the most interesting AI/tech topic right now, writes a post with the agent graph
and publishes it to Dev.to.

Scheduled by .github/workflows/autopilot.yml at 06:00 and 18:00 IST.

Usage:
    python backend/autopilot.py            # pick, generate, publish
    python backend/autopilot.py --dry-run  # pick and generate only, nothing is published or saved

Environment:
    GROQ_API_KEY              required
    DEVTO_API_KEY             required to publish (also used to avoid repeating recent topics)
    FIREBASE_SERVICE_ACCOUNT  optional, with AUTOPILOT_USER_ID: also saves the post to that user's TrendFlow feed
    AUTOPILOT_USER_ID         optional, Firebase UID of the account that should own autopilot posts
    GNEWS_API_KEY etc.        optional news sources, same as the backend
"""
import os
import sys
import argparse
from typing import List

import requests
from pydantic import BaseModel, Field

from main import db, build_post_data
from agents import app_graph, ask_llm
from devto import publish_article, recent_titles


class TopicPick(BaseModel):
    topic: str = Field(description="Short, search-friendly topic phrase (2-8 words), e.g. 'Jev decision model architecture'")
    reason: str = Field(description="One sentence on why this is the most interesting topic right now")


def trending_candidates() -> List[str]:
    """Collects what's trending right now in AI research, developer communities and tech news."""
    candidates = []

    try:
        papers = requests.get("https://huggingface.co/api/daily_papers", params={"limit": 30}, timeout=15).json()
        papers.sort(key=lambda p: p.get("paper", {}).get("upvotes", 0), reverse=True)
        for p in papers[:10]:
            paper = p.get("paper", {})
            candidates.append(f"[HF Daily Papers, {paper.get('upvotes', 0)} upvotes] {paper.get('title')}")
    except Exception as e:
        print(f"⚠️ HF daily papers failed: {e}")

    try:
        hits = requests.get(
            "https://hn.algolia.com/api/v1/search", params={"tags": "front_page", "hitsPerPage": 30}, timeout=15
        ).json().get("hits", [])
        hits.sort(key=lambda h: h.get("points") or 0, reverse=True)
        for h in hits[:15]:
            candidates.append(f"[Hacker News front page, {h.get('points', 0)} points] {h.get('title')}")
    except Exception as e:
        print(f"⚠️ Hacker News front page failed: {e}")

    if os.getenv("GNEWS_API_KEY"):
        try:
            articles = requests.get(
                "https://gnews.io/api/v4/top-headlines",
                params={"category": "technology", "lang": "en", "max": 10, "apikey": os.getenv("GNEWS_API_KEY")},
                timeout=15,
            ).json().get("articles", [])
            for a in articles:
                candidates.append(f"[Tech headline, {a['source']['name']}] {a['title']}")
        except Exception as e:
            print(f"⚠️ GNews headlines failed: {e}")

    return candidates


def pick_topic(candidates: List[str], already_covered: List[str]) -> TopicPick:
    covered = "\n".join(f"- {t}" for t in already_covered) or "- (nothing yet)"
    trending = "\n".join(f"- {c}" for c in candidates)
    prompt = f"""
    You are the editor of a tech blog for developers and AI practitioners.
    From the trending items below, pick the ONE topic that would make the most interesting, substantive post right now.

    PREFER: new AI models, architectures, research results, developer tools, major technical launches or incidents.
    AVOID: politics, celebrity news, obituaries, pure finance, and anything already covered by our recent posts.

    TRENDING NOW:
    {trending}

    OUR RECENT POSTS (do not repeat these topics):
    {covered}

    Return the topic as a short search-friendly phrase that a research tool could look up.
    """
    return ask_llm(prompt, max_tokens=800, schema=TopicPick)


def write_summary(lines: List[str]):
    """Shows the result on the GitHub Actions run page."""
    print("\n".join(lines))
    summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser(description="TrendFlow autopilot")
    parser.add_argument("--dry-run", action="store_true", help="Generate the post but don't publish or save it")
    args = parser.parse_args()

    devto_key = os.getenv("DEVTO_API_KEY")
    if not devto_key and not args.dry_run:
        sys.exit("DEVTO_API_KEY is required to publish (use --dry-run to test without it)")

    print("--- 🛰️ Autopilot: Finding the most interesting topic ---")
    candidates = trending_candidates()
    if not candidates:
        sys.exit("No trending candidates found, aborting")
    already_covered = recent_titles(devto_key) if devto_key else []
    pick = pick_topic(candidates, already_covered)
    print(f"   🎯 Topic: {pick.topic}\n   💡 Why: {pick.reason}")

    final_state = app_graph.invoke({"topic": pick.topic, "revision_count": 0, "is_approved": False})
    metadata = final_state.get("final_metadata", {})
    title = metadata.get("title_viral") or f"Deep Dive: {pick.topic}"
    body = final_state.get("draft", "")
    tags = metadata.get("tags", [])

    summary = [
        "## TrendFlow Autopilot",
        f"- **Topic:** {pick.topic}",
        f"- **Why:** {pick.reason}",
        f"- **Title:** {title}",
        f"- **Words:** {len(body.split())}",
    ]

    if args.dry_run:
        write_summary(summary + ["- **Dry run:** not published", "", "---", "", body[:3000]])
        return

    url = publish_article(devto_key, title, body, tags, published=True)
    summary.append(f"- **Published:** {url}")

    owner = os.getenv("AUTOPILOT_USER_ID")
    if db and owner:
        try:
            post_data = build_post_data(pick.topic, final_state, owner, status="published")
            post_data["devto_url"] = url
            post_data["source"] = "autopilot"
            db.collection("drafts").document().set(post_data)
            summary.append("- **Saved** to the TrendFlow feed")
        except Exception as e:
            summary.append(f"- ⚠️ Published, but saving to Firestore failed: {e}")

    write_summary(summary)


if __name__ == "__main__":
    main()
