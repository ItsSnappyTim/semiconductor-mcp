import httpx

from ..config import NEWSAPI_KEY
from ..http_client import request_with_retry
from ..schemas import NewsResult

_BASE = "https://newsapi.org/v2/everything"


async def search(query: str, max_results: int = 5) -> list[NewsResult]:
    params = {
        "q": query,
        "sortBy": "relevancy",
        "language": "en",
        "pageSize": max_results,
    }
    headers = {
        "User-Agent": "semiconductor-mcp-research/1.0",
        "X-Api-Key": NEWSAPI_KEY,
    }
    try:
        resp = await request_with_retry(_BASE, params=params, headers=headers, timeout=30.0)
        resp.raise_for_status()
    except httpx.TimeoutException:
        return []
    except httpx.HTTPStatusError:
        return []

    data = resp.json()
    results: list[NewsResult] = []
    for article in data.get("articles", []):
        results.append(
            NewsResult(
                source=article.get("source", {}).get("name", ""),
                title=article.get("title", ""),
                description=article.get("description", "") or "",
                url=article.get("url", ""),
                published_at=article.get("publishedAt", ""),
            )
        )
    return results
