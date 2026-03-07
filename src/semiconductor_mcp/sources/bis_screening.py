"""ITA Consolidated Screening List — optional, requires free ITA_API_KEY.

Combines: BIS Entity List, BIS Denied Persons List, BIS Unverified List,
OFAC SDN, OFAC Consolidated Non-SDN, State AECA Debarred, plus more.
Free API key available at https://developer.trade.gov/

Without a key, this module returns an informational response directing the
user to obtain the free key.
"""

from typing import Any

import httpx

from ..cache import TTLCache
from ..http_client import request_with_retry
from ..schemas import ITAMatch, ITAResult

_BASE = "https://data.trade.gov/consolidated_screening_list/v1/search"
_TIMEOUT = 20.0

_cache: TTLCache = TTLCache(ttl_seconds=3600, name="bis_screening")  # 1 hour


async def screen_entity(name: str, api_key: str) -> ITAResult | dict[str, Any]:
    """Screen an entity name against the ITA Consolidated Screening List."""
    if not api_key:
        return {
            "total": 0,
            "results": [],
            "risk": "UNKNOWN",
            "note": (
                "ITA_API_KEY not configured. Get a free key at "
                "https://developer.trade.gov/ to enable BIS Entity List, "
                "Denied Persons, and Unverified List screening."
            ),
        }

    cache_key = name.strip().lower()
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached

    params = {"name": name, "subscription-key": api_key}
    try:
        resp = await request_with_retry(_BASE, params=params, timeout=_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except httpx.TimeoutException:
        return {"total": 0, "results": [], "risk": "UNKNOWN", "error": "ITA API timeout"}
    except httpx.HTTPStatusError as exc:
        return {"total": 0, "results": [], "risk": "UNKNOWN", "error": f"ITA API HTTP {exc.response.status_code}"}
    except Exception as exc:
        return {"total": 0, "results": [], "risk": "UNKNOWN", "error": str(exc)}

    total = data.get("total", 0)
    raw_results = data.get("results", [])

    results: list[ITAMatch] = []
    for r in raw_results[:10]:
        results.append({
            "name": r.get("name", ""),
            "source_list": r.get("source", ""),
            "country": r.get("country", ""),
            "addresses": r.get("addresses", [])[:2],
            "federal_register_notice": r.get("federal_register_notice", ""),
            "end_date": r.get("end_date", ""),
        })

    # Risk classification
    def _matches(source: str, keywords: list[str]) -> bool:
        s = source.lower()
        return any(k in s for k in keywords)

    blocked_keywords = ["entity list", "denied persons", "ofac sdn", "sdn list", "military-industrial"]
    flagged_keywords = ["unverified list", "non-sdn", "aeca debarred", "debarred"]
    risk = "CLEAR"
    if any(_matches(r["source_list"], blocked_keywords) for r in results):
        risk = "BLOCKED"
    elif any(_matches(r["source_list"], flagged_keywords) for r in results):
        risk = "FLAGGED"
    elif results:
        risk = "FLAGGED"

    result = ITAResult(
        query=name,
        total=total,
        results=results,
        risk=risk,
        note=f"{total} match(es) found across ITA Consolidated Screening List.",
    )
    _cache.set(cache_key, result)
    return result
