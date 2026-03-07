"""OpenSanctions entity screening — optional, requires free OPENSANCTIONS_API_KEY.

Checks a company or individual name against 100+ global sanctions datasets
including OFAC SDN, EU/UN/UK sanctions, and national lists.

Free API key (100 searches/month) at https://www.opensanctions.org/api/
Rate limiting: 100 searches/month on free tier — retry conservatively on 429.
"""

from typing import Any

import httpx

from ..cache import TTLCache
from ..http_client import request_with_retry
from ..schemas import SanctionsMatch, SanctionsResult

_BASE = "https://api.opensanctions.org"
_TIMEOUT = 20.0
_RETRY_DELAYS = [3.0, 8.0]  # conservative: free tier has only 100 searches/month

# TTL cache with a long window — sanctions lists don't change hourly, and the
# free tier quota (100/month) makes re-querying expensive.
_cache: TTLCache = TTLCache(ttl_seconds=86400, name="opensanctions")  # 24 hours


async def screen_entity(name: str, api_key: str = "") -> SanctionsResult | dict[str, Any]:
    """Screen an entity name against OpenSanctions consolidated dataset."""
    source_url = f"https://www.opensanctions.org/search/?q={name.replace(' ', '+')}"

    cache_key = name.strip().lower()
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached

    if not api_key:
        return {
            "total": 0,
            "risk": "UNKNOWN",
            "matches": [],
            "source_url": source_url,
            "note": (
                "OPENSANCTIONS_API_KEY not configured. Get a free key (100 searches/month) "
                "at https://www.opensanctions.org/api/ to enable 100+ sanctions list screening. "
                f"Manual check: {source_url}"
            ),
        }

    params = {"q": name, "limit": 10}
    headers = {"Authorization": f"ApiKey {api_key}"}
    try:
        resp = await request_with_retry(
            f"{_BASE}/search/default",
            params=params,
            headers=headers,
            timeout=_TIMEOUT,
            retry_delays=_RETRY_DELAYS,
        )
        if resp.status_code == 429:
            return {"total": 0, "risk": "UNKNOWN", "matches": [], "error": "OpenSanctions rate limited (429)"}
        resp.raise_for_status()
        data = resp.json()
    except httpx.TimeoutException:
        return {"total": 0, "risk": "UNKNOWN", "matches": [], "error": "OpenSanctions API timeout"}
    except httpx.HTTPStatusError as exc:
        return {"total": 0, "risk": "UNKNOWN", "matches": [], "error": f"OpenSanctions HTTP {exc.response.status_code}"}
    except Exception as exc:
        return {"total": 0, "risk": "UNKNOWN", "matches": [], "error": str(exc)}

    raw_results = data.get("results", [])
    matches: list[SanctionsMatch] = []
    for entity in raw_results:
        props = entity.get("properties", {})
        matches.append({
            "id": entity.get("id"),
            "caption": entity.get("caption", ""),
            "schema": entity.get("schema", ""),
            "datasets": entity.get("datasets", []),
            "countries": props.get("country", []),
            "aliases": props.get("name", [])[:5],
        })

    result = SanctionsResult(
        query=name,
        total=data.get("total", {}).get("value", len(matches)),
        risk="FLAGGED" if matches else "CLEAR",
        matches=matches,
        source_url=source_url,
    )
    _cache.set(cache_key, result)
    return result
