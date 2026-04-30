"""tools_lib/search.py — Real search integrations for ResearcherAgent.

All sources degrade gracefully when credentials are absent:
  - Hacker News   : always available (Algolia public API)
  - Reddit        : public JSON API (no auth needed for basic search)
  - YouTube       : requires YOUTUBE_API_KEY in .env
  - Web (DuckDuckGo) : always available (instant answer API, no key)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import httpx


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    source: str
    score: int = 0  # upvotes / views / relevance


class SearchTools:
    HEADERS = {"User-Agent": "OpenClaw/1.0 research-agent"}

    def __init__(self, youtube_api_key: str = ""):
        self.youtube_api_key = youtube_api_key

    # -------------------------------------------------------------------------
    # Hacker News — Algolia public API (always available)
    # -------------------------------------------------------------------------

    async def search_hackernews(self, query: str, limit: int = 10) -> list[SearchResult]:
        async with httpx.AsyncClient(timeout=10.0, headers=self.HEADERS) as client:
            resp = await client.get(
                "https://hn.algolia.com/api/v1/search",
                params={"query": query, "hitsPerPage": limit, "tags": "story"},
            )
            resp.raise_for_status()
        hits = resp.json().get("hits", [])
        return [
            SearchResult(
                title=h.get("title", ""),
                url=h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID')}",
                snippet=h.get("story_text") or "",
                source="hackernews",
                score=h.get("points", 0),
            )
            for h in hits
            if h.get("title")
        ]

    # -------------------------------------------------------------------------
    # Reddit — public JSON API (no auth required for search)
    # -------------------------------------------------------------------------

    async def search_reddit(
        self, query: str, subreddit: str = "all", limit: int = 10, sort: str = "relevance"
    ) -> list[SearchResult]:
        url = (
            f"https://www.reddit.com/r/{subreddit}/search.json"
            if subreddit != "all"
            else "https://www.reddit.com/search.json"
        )
        async with httpx.AsyncClient(timeout=10.0, headers=self.HEADERS, follow_redirects=True) as client:
            resp = await client.get(
                url,
                params={"q": query, "limit": limit, "sort": sort, "t": "month"},
            )
            resp.raise_for_status()
        posts = resp.json().get("data", {}).get("children", [])
        return [
            SearchResult(
                title=p["data"].get("title", ""),
                url=f"https://reddit.com{p['data'].get('permalink', '')}",
                snippet=p["data"].get("selftext", "")[:300],
                source=f"reddit/r/{p['data'].get('subreddit', '')}",
                score=p["data"].get("score", 0),
            )
            for p in posts
            if p.get("data", {}).get("title")
        ]

    # -------------------------------------------------------------------------
    # YouTube — requires YOUTUBE_API_KEY
    # -------------------------------------------------------------------------

    async def search_youtube(self, query: str, limit: int = 10) -> list[SearchResult]:
        if not self.youtube_api_key:
            return []
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://www.googleapis.com/youtube/v3/search",
                params={
                    "q": query,
                    "part": "snippet",
                    "maxResults": limit,
                    "type": "video",
                    "order": "relevance",
                    "key": self.youtube_api_key,
                },
            )
            resp.raise_for_status()
        items = resp.json().get("items", [])
        return [
            SearchResult(
                title=i["snippet"].get("title", ""),
                url=f"https://youtube.com/watch?v={i['id'].get('videoId', '')}",
                snippet=i["snippet"].get("description", "")[:300],
                source="youtube",
                score=0,
            )
            for i in items
            if i.get("snippet")
        ]

    # -------------------------------------------------------------------------
    # DuckDuckGo instant answers — always available, no key
    # -------------------------------------------------------------------------

    async def search_web(self, query: str) -> list[SearchResult]:
        async with httpx.AsyncClient(timeout=10.0, headers=self.HEADERS) as client:
            resp = await client.get(
                "https://api.duckduckgo.com/",
                params={"q": query, "format": "json", "no_html": "1", "skip_disambig": "1"},
            )
            resp.raise_for_status()
        data = resp.json()
        results = []

        if data.get("AbstractText"):
            results.append(SearchResult(
                title=data.get("Heading", query),
                url=data.get("AbstractURL", ""),
                snippet=data["AbstractText"][:500],
                source="duckduckgo",
                score=100,
            ))

        for topic in data.get("RelatedTopics", [])[:5]:
            if isinstance(topic, dict) and topic.get("Text"):
                results.append(SearchResult(
                    title=topic.get("Text", "")[:80],
                    url=topic.get("FirstURL", ""),
                    snippet=topic.get("Text", "")[:300],
                    source="duckduckgo",
                    score=50,
                ))

        return results

    # -------------------------------------------------------------------------
    # Combined search — queries all available sources
    # -------------------------------------------------------------------------

    async def search_all(self, query: str, limit_per_source: int = 5) -> list[SearchResult]:
        """Run all available sources in parallel and merge results."""
        import asyncio

        tasks = [
            self.search_hackernews(query, limit_per_source),
            self.search_reddit(query, limit=limit_per_source),
            self.search_web(query),
        ]
        if self.youtube_api_key:
            tasks.append(self.search_youtube(query, limit_per_source))

        results_by_source = await asyncio.gather(*tasks, return_exceptions=True)
        merged: list[SearchResult] = []
        for batch in results_by_source:
            if isinstance(batch, list):
                merged.extend(batch)

        # Sort by score descending, deduplicate by URL
        seen_urls: set[str] = set()
        unique: list[SearchResult] = []
        for r in sorted(merged, key=lambda x: x.score, reverse=True):
            if r.url not in seen_urls:
                seen_urls.add(r.url)
                unique.append(r)
        return unique

    @staticmethod
    def format_for_prompt(results: list[SearchResult]) -> str:
        """Format search results as a readable block for an inference prompt."""
        if not results:
            return "No search results found."
        lines = []
        for i, r in enumerate(results, 1):
            lines.append(f"{i}. [{r.source}] {r.title}")
            if r.snippet:
                lines.append(f"   {r.snippet[:200]}")
            lines.append(f"   {r.url}")
        return "\n".join(lines)
