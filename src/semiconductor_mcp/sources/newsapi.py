from typing import Any

import httpx

from ..config import NEWSAPI_KEY

_BASE = "https://newsapi.org/v2/everything"


async def search(query: str, max_results: int = 5) -> list[dict[str, Any]]:
    params = {
        "q": query,
        "sortBy": "relevancy",
        "language": "en",
        "pageSize": max_results,
        "apiKey": NEWSAPI_KEY,
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(_BASE, params=params)
        resp.raise_for_status()

    data = resp.json()
    results = []
    for article in data.get("articles", []):
        results.append(
            {
                "source": article.get("source", {}).get("name", ""),
                "title": article.get("title", ""),
                "description": article.get("description", "") or "",
                "url": article.get("url", ""),
                "published_at": article.get("publishedAt", ""),
            }
        )
    return results
