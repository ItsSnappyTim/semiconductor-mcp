
import defusedxml.ElementTree as ET
import httpx

from ..cache import TTLCache
from ..http_client import request_with_retry
from ..schemas import PaperResult

_NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
}

_BASE = "https://export.arxiv.org/api/query"
_HEADERS = {"User-Agent": "semiconductor-mcp-research/1.0"}
_TIMEOUT = 30.0
_RETRY_DELAYS = [5.0, 15.0]  # arXiv asks for delays between requests

_cache: TTLCache = TTLCache(ttl_seconds=1800, name="arxiv")  # 30 min


async def search(query: str, max_results: int = 5) -> list[PaperResult]:
    cache_key = f"{query}:{max_results}"
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached

    # Require all terms in title OR abstract to cut noise
    terms = query.strip().split()
    if len(terms) == 1:
        search_query = f"all:{terms[0]}"
    else:
        ti_clause = " AND ".join(f"ti:{t}" for t in terms)
        abs_clause = " AND ".join(f"abs:{t}" for t in terms)
        search_query = f"({ti_clause}) OR ({abs_clause})"
    params = {
        "search_query": search_query,
        "max_results": max_results,
        "sortBy": "relevance",
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

    root = ET.fromstring(resp.text)
    results: list[PaperResult] = []
    for entry in root.findall("atom:entry", _NS):
        title_el = entry.find("atom:title", _NS)
        summary_el = entry.find("atom:summary", _NS)
        published_el = entry.find("atom:published", _NS)
        id_el = entry.find("atom:id", _NS)

        doi = None
        doi_el = entry.find("arxiv:doi", _NS)
        if doi_el is not None and doi_el.text:
            doi = doi_el.text.strip()

        authors = [
            a.find("atom:name", _NS).text  # type: ignore[union-attr]
            for a in entry.findall("atom:author", _NS)
            if a.find("atom:name", _NS) is not None
        ]

        results.append(
            PaperResult(
                source="arxiv",
                title=(title_el.text or "").strip() if title_el is not None else "",
                abstract=(summary_el.text or "").strip() if summary_el is not None else "",
                year=(published_el.text or "")[:4] if published_el is not None else "",
                authors=authors,
                url=(id_el.text or "").strip() if id_el is not None else "",
                doi=doi,
                citation_count=None,
            )
        )

    _cache.set(cache_key, results)
    return results
