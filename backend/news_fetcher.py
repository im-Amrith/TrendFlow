import os
import requests
import httpx
import asyncio
from gnews import GNews
from dotenv import load_dotenv

load_dotenv()

async def fetch_structured_news(topic: str = "Technology", limit: int = 5):
    news_items = []

    async def fetch_gnews(client):
        if not os.getenv("GNEWS_API_KEY"): return []
        try:
            url = f"https://gnews.io/api/v4/search?q={topic}&lang=en&max={limit}&apikey={os.getenv('GNEWS_API_KEY')}"
            resp = await client.get(url)
            data = resp.json()
            return [{
                "title": article['title'],
                "url": article['url'],
                "source": article['source']['name'],
                "summary": article['description'],
                "published_at": article['publishedAt'],
                "image_url": article.get('image')
            } for article in data.get('articles', [])]
        except Exception as e:
            print(f"GNews failed: {e}")
            return []

    async def fetch_newsdata(client):
        if not os.getenv("NEWSDATA_API_KEY"): return []
        try:
            url = f"https://newsdata.io/api/1/news?apikey={os.getenv('NEWSDATA_API_KEY')}&q={topic}&language=en"
            resp = await client.get(url)
            data = resp.json()
            return [{
                "title": article['title'],
                "url": article['link'],
                "source": article['source_id'],
                "summary": article['description'],
                "published_at": article['pubDate'],
                "image_url": article.get('image_url')
            } for article in data.get('results', [])[:limit]]
        except Exception as e:
            print(f"NewsData failed: {e}")
            return []

    def fetch_google_scraper():
        try:
            # Scraper can be slow, so we cap it to avoid timeouts if limit is huge
            scraper_limit = min(limit, 20) 
            google_news = GNews(max_results=scraper_limit)
            g_results = google_news.get_news(topic)
            return [{
                "title": r['title'],
                "url": r['url'],
                "source": r['publisher']['title'],
                "summary": "Read full article on Google News...",
                "published_at": r['published date'],
                "image_url": None
            } for r in g_results]
        except Exception as e:
            print(f"Google News failed: {e}")
            return []

    async with httpx.AsyncClient() as client:
        # Run API calls in parallel
        # Run scraper in a thread so it doesn't block
        results = await asyncio.gather(
            fetch_gnews(client),
            fetch_newsdata(client),
            asyncio.to_thread(fetch_google_scraper)
        )
        
    # Flatten results
    for res in results:
        news_items.extend(res)
        
    return news_items[:limit]
