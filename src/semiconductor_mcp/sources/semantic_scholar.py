import httpx

from ..cache import TTLCache
from ..http_client import request_with_retry
from ..schemas import PaperResult

_BASE = "https://api.semanticscholar.org/graph/v1/paper/search"
_FIELDS = "title,abstract,year,authors,citationCount,externalIds,url"
_HEADERS = {"User-Agent": "semiconductor-mcp-research/1.0"}
_TIMEOUT = 30.0
_RETRY_DELAYS = [5.0, 15.0]  # Semantic Scholar enforces per-IP rate limits

_cache: TTLCache = TTLCache(ttl_seconds=1800, name="semantic_scholar")  # 30 min


async def search(query: str, max_results: int = 5) -> list[PaperResult]:
    cache_key = f"{query}:{max_results}"
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached

    params = {
        "query": query,
        "fields": _FIELDS,
        "limit": max_results,
    }

    try:
        resp = await request_with_retry(
            _BASE,
            params=params,
            headers=_HEADERS,
            timeout=_TIMEOUT,
            retry_delays=_RETRY_DELAYS,
        )
        if resp.status_code == 429:
            return []
        resp.raise_for_status()
    except httpx.TimeoutException:
        return []
    except httpx.HTTPStatusError:
        return []

    data = resp.json()
    results: list[PaperResult] = []
    for paper in data.get("data", []):
        external_ids = paper.get("externalIds") or {}
        doi = external_ids.get("DOI")
        authors = [a.get("name", "") for a in (paper.get("authors") or [])]
        results.append(
            PaperResult(
                source="semantic_scholar",
                title=paper.get("title", ""),
                abstract=paper.get("abstract", "") or "",
                year=str(paper.get("year", "")) if paper.get("year") else "",
                authors=authors,
                url=paper.get("url", ""),
                doi=doi,
                citation_count=paper.get("citationCount"),
            )
        )

    _cache.set(cache_key, results)
    return results
