from typing import Any

import httpx

_BASE = "https://api.semanticscholar.org/graph/v1/paper/search"
_FIELDS = "title,abstract,year,authors,citationCount,externalIds,url"


async def search(query: str, max_results: int = 5) -> list[dict[str, Any]]:
    params = {
        "query": query,
        "fields": _FIELDS,
        "limit": max_results,
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(_BASE, params=params)
        if resp.status_code == 429:
            return []  # rate limited; arXiv results will still be returned
        resp.raise_for_status()

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
