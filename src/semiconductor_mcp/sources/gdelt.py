"""GDELT DOC 2.0 API client — free, no API key required.

GDELT monitors global news in near real-time. We use it for two purposes:
  1. General supply chain news signals for a component
  2. Grey market / enforcement signals (smuggling, sanctions evasion, counterfeit)

Rate limiting: GDELT enforces a per-IP rate limit. A module-level lock
serialises all outgoing requests so concurrent tool calls never hit GDELT
simultaneously. Retry delays are conservative to avoid repeated 429s.
"""

import asyncio
from typing import Any

import httpx

_BASE = "http://api.gdeltproject.org/api/v2/doc/doc"
_TIMEOUT = 25
_RETRY_DELAYS = [3.0, 6.0]  # seconds to wait after 429 before retrying
_HEADERS = {"User-Agent": "semiconductor-mcp-research/1.0"}

# Serialise all GDELT requests — only one in-flight at a time per process.
# Lazily initialised so it is created inside the running event loop.
_lock: asyncio.Lock | None = None


def _get_lock() -> asyncio.Lock:
    global _lock
    if _lock is None:
        _lock = asyncio.Lock()
    return _lock


async def _search(query: str, days: int, max_records: int = 10) -> list[dict[str, Any]]:
    params = {
        "query": query,
        "mode": "ArtList",
        "maxrecords": min(max_records, 25),
        "format": "json",
        "timespan": f"{max(1, min(days, 365))}d",
        "sort": "DateDesc",
    }
    last_error: str = ""
    async with _get_lock():
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                for delay in [0] + _RETRY_DELAYS:
                    if delay:
                        await asyncio.sleep(delay)
                    resp = await client.get(_BASE, params=params, headers=_HEADERS)
                    if resp.status_code == 429:
                        last_error = "GDELT rate limit (429)"
                        continue
                    resp.raise_for_status()
                    data = resp.json()
                    break
                else:
                    return [{"error": last_error}]
        except httpx.TimeoutException:
            return [{"error": "GDELT API timeout"}]
        except httpx.HTTPStatusError as exc:
            return [{"error": f"GDELT HTTP {exc.response.status_code}"}]
        except Exception as exc:
            return [{"error": str(exc)}]

    articles = data.get("articles", []) if data else []
    return [
        {
            "title": a.get("title", ""),
            "url": a.get("url", ""),
            "domain": a.get("domain", ""),
            "date": a.get("seendate", ""),
            "language": a.get("language", ""),
        }
        for a in articles
    ]


async def search_supply_chain_news(query: str, days: int = 90) -> list[dict[str, Any]]:
    """Search GDELT for recent supply chain news related to a query."""
    full_query = f'"{query}" semiconductor supply chain'
    return await _search(full_query, days)


async def search_grey_market_signals(query: str, days: int = 180) -> list[dict[str, Any]]:
    """Search GDELT for grey market, smuggling, and enforcement signals."""
    grey_terms = (
        "(smuggling OR \"sanctions evasion\" OR counterfeit OR "
        "\"grey market\" OR diversion OR \"export control violation\" OR "
        "\"black market\" OR trafficking)"
    )
    full_query = f'"{query}" semiconductor {grey_terms}'
    return await _search(full_query, days, max_records=15)
