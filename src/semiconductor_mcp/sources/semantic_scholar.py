import asyncio
from typing import Any

import httpx

_BASE = "https://api.semanticscholar.org/graph/v1/paper/search"
_FIELDS = "title,abstract,year,authors,citationCount,externalIds,url"
_HEADERS = {"User-Agent": "semiconductor-mcp-research/1.0"}
_TIMEOUT = 30
_RETRY_DELAYS = [5.0, 15.0]  # Semantic Scholar enforces per-IP rate limits without a key


async def search(query: str, max_results: int = 5) -> list[dict[str, Any]]:
    params = {
        "query": query,
        "fields": _FIELDS,
        "limit": max_results,
    }

    last_error = ""
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            for delay in [0.0] + _RETRY_DELAYS:
                if delay:
                    await asyncio.sleep(delay)
                resp = await client.get(_BASE, params=params, headers=_HEADERS)
                if resp.status_code == 429:
                    last_error = "Semantic Scholar rate limited (429)"
                    continue
                resp.raise_for_status()
                break
            else:
                return []  # all retries exhausted; arXiv results will still be returned
    except httpx.TimeoutException:
        return []
    except httpx.HTTPStatusError:
        return []

    data = resp.json()
    results = []
    for paper in data.get("data", []):
        external_ids = paper.get("externalIds") or {}
        doi = external_ids.get("DOI")
        authors = [a.get("name", "") for a in (paper.get("authors") or [])]
        results.append(
            {
                "source": "semantic_scholar",
                "title": paper.get("title", ""),
                "abstract": paper.get("abstract", "") or "",
                "year": str(paper.get("year", "")) if paper.get("year") else "",
                "authors": authors,
                "url": paper.get("url", ""),
                "doi": doi,
                "citation_count": paper.get("citationCount"),
            }
        )
    return results
