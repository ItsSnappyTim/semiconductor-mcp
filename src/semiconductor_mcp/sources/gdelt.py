"""GDELT DOC 2.0 API client — free, no API key required.

GDELT monitors global news in near real-time. We use it for two purposes:
  1. General supply chain news signals for a component
  2. Grey market / enforcement signals (smuggling, sanctions evasion, counterfeit)

Rate limiting: GDELT enforces a per-IP rate limit. A module-level semaphore
caps concurrent outgoing requests at 2 — enough to parallelise the two calls
inside research_and_verify_supply_chain while preventing pile-ups from
simultaneous tool invocations. Retry delays are conservative to avoid 429s.
"""

import asyncio
from typing import Any

import httpx

from ..cache import TTLCache
from ..http_client import request_with_retry
from ..schemas import GdeltArticle

_BASE = "https://api.gdeltproject.org/api/v2/doc/doc"
_TIMEOUT = 15.0
_RETRY_DELAYS = [3.0, 6.0]

# Allow at most 2 concurrent GDELT requests per process.
# Lazily initialised so it is created inside the running event loop.
_sem: asyncio.Semaphore | None = None

# GDELT news is relatively fresh — 30 min cache is a good balance between
# freshness and avoiding hammering the rate limit.
_cache: TTLCache = TTLCache(ttl_seconds=1800, name="gdelt")


def _get_sem() -> asyncio.Semaphore:
    global _sem
    if _sem is None:
        _sem = asyncio.Semaphore(2)
    return _sem


async def _search(query: str, days: int, max_records: int = 10) -> list[GdeltArticle | dict[str, Any]]:
    cache_key = f"{query}:{days}:{max_records}"
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached

    params = {
        "query": query,
        "mode": "ArtList",
        "maxrecords": min(max_records, 25),
        "format": "json",
        "timespan": f"{max(1, min(days, 365))}d",
        "sort": "DateDesc",
    }
    async with _get_sem():
        try:
            resp = await request_with_retry(
                _BASE,
                params=params,
                timeout=_TIMEOUT,
                retry_delays=_RETRY_DELAYS,
            )
            if resp.status_code == 429:
                return [{"error": "GDELT rate limit (429)"}]
            resp.raise_for_status()
            data = resp.json()
        except httpx.TimeoutException:
            return [{"error": "GDELT API timeout"}]
        except httpx.HTTPStatusError as exc:
            return [{"error": f"GDELT HTTP {exc.response.status_code}"}]
        except Exception as exc:
            return [{"error": str(exc)}]

    articles = data.get("articles", []) if data else []
    results: list[GdeltArticle] = [
        GdeltArticle(
            title=a.get("title", ""),
            url=a.get("url", ""),
            domain=a.get("domain", ""),
            date=a.get("seendate", ""),
        )
        for a in articles
    ]
    _cache.set(cache_key, results)
    return results


async def search_supply_chain_news(query: str, days: int = 90) -> list[GdeltArticle | dict[str, Any]]:
    """Search GDELT for recent supply chain news related to a query."""
    full_query = f'"{query}" semiconductor supply chain'
    return await _search(full_query, days)


async def search_grey_market_signals(query: str, days: int = 180) -> list[GdeltArticle | dict[str, Any]]:
    """Search GDELT for grey market, smuggling, and enforcement signals."""
    grey_terms = (
        "(smuggling OR \"sanctions evasion\" OR counterfeit OR "
        "\"grey market\" OR diversion OR \"export control violation\" OR "
        "\"black market\" OR trafficking)"
    )
    full_query = f'"{query}" semiconductor {grey_terms}'
    return await _search(full_query, days, max_records=15)
