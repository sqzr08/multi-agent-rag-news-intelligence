"""
Retriever Agent
───────────────
1. Query SerpAPI Google News for today's AI articles.
2. Scrape full article text via trafilatura
3. Deduplicate by URL hash.
4. Filter out articles that are too short.
"""

import hashlib
import asyncio
from datetime import date
from typing import List

import trafilatura
import httpx
from serpapi import GoogleSearch

import config
from graph.state import PipelineState, RawArticle
import os
from dotenv import load_dotenv
load_dotenv(".env")

# SerpAPI 

def fetch_news_urls(query: str) -> List[dict]:
    """Return a list of {title, url, source, date} dicts from SerpAPI."""
    params = {
        "engine": "google_news",
        "q": query,
        "tbs": f"qdr:d",   #past 24h
        "num": 20,
        "api_key": os.getenv("SERPAPI_KEY", ""),
    }
    search = GoogleSearch(params)
    results = search.get_dict()

    articles = []
    for item in results.get("news_results", []):
        articles.append({
            "title": item.get("title", ""),
            "url": item.get("link", ""),
            "source": item.get("source", {}).get("name", "Unknown"),
            "date": item.get("date", date.today().isoformat()),
        })
    return articles


# ── Scraper ───────────────────────────────────────────────────────────────────

async def scrape_article(url: str) -> str:
    """
    Fetch and extract article text using trafilatura.
    Falls back to a raw httpx GET + trafilatura if needed.
    """
    for attempt in range(config.SCRAPE_MAX_RETRIES):
        try:
            downloaded = trafilatura.fetch_url(
                url,
                config=trafilatura.settings.use_config(),
            )
            text = trafilatura.extract(
                downloaded,
                include_comments=False,
                include_tables=False,
                no_fallback=False,
            )
            if text and len(text) >= config.MIN_ARTICLE_LENGTH:
                return text

            # Fallback: raw download via httpx
            async with httpx.AsyncClient(timeout=config.SCRAPE_TIMEOUT_SECONDS) as client:
                resp = await client.get(url, follow_redirects=True)
                text = trafilatura.extract(resp.text)
                if text and len(text) >= config.MIN_ARTICLE_LENGTH:
                    return text

        except Exception:
            if attempt == config.SCRAPE_MAX_RETRIES - 1:
                return ""
            await asyncio.sleep(1)
    return ""


def url_hash(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()[:16]


# Retriever LangGraph Node

async def retriever_node(state: PipelineState) -> PipelineState:
    print(f"\n🔍 [Retriever] Fetching news for: '{state['query']}'")

    # 1. Discover URLs
    try:
        candidates = fetch_news_urls(state["query"])
    except Exception as e:
        state["errors"].append(f"SerpAPI error: {e}")
        return state

    print(f"   Found {len(candidates)} candidate articles")

    # 2. Deduplicate by URL hash
    seen_hashes: set = set()
    unique = []
    for c in candidates:
        h = url_hash(c["url"])
        if h not in seen_hashes and c["url"]:
            seen_hashes.add(h)
            unique.append({**c, "hash": h})

    # 3. Scrape full text concurrently
    async def scrape_one(item: dict) -> RawArticle | None:
        text = await scrape_article(item["url"])
        if not text:
            return None
        return RawArticle(
            url=item["url"],
            title=item["title"],
            source=item["source"],
            date=item["date"],
            raw_text=text,
            url_hash=item["hash"],
        )

    tasks = [scrape_one(item) for item in unique]
    results = await asyncio.gather(*tasks)
    articles = [r for r in results if r is not None]

    print(f"   Successfully scraped {len(articles)} articles")
    state["raw_articles"] = articles
    return state
