"""OpenSanctions entity screening — optional, requires free OPENSANCTIONS_API_KEY.

Checks a company or individual name against 100+ global sanctions datasets
including OFAC SDN, EU/UN/UK sanctions, and national lists.

Free API key (100 searches/month) at https://www.opensanctions.org/api/
Rate limiting: 100 searches/month on free tier — retry conservatively on 429.
"""

import asyncio
from typing import Any

import httpx

_BASE = "https://api.opensanctions.org"
_TIMEOUT = 20
_RETRY_DELAYS = [3.0, 8.0]  # conservative: free tier has only 100 searches/month

# Module-level cache keyed by normalised name (lower-stripped).
# Conserves the 100 searches/month free tier quota across all callers.
_cache: dict[str, dict] = {}


async def screen_entity(name: str, api_key: str = "") -> dict[str, Any]:
    """Screen an entity name against OpenSanctions consolidated dataset.

    Returns a dict with:
      total      — number of matches found
      risk       — "CLEAR" | "FLAGGED" | "UNKNOWN"
      matches    — list of matching entities with list details
      source_url — permalink to OpenSanctions results for review
    """
    source_url = f"https://www.opensanctions.org/search/?q={name.replace(' ', '+')}"

    cache_key = name.strip().lower()
    if cache_key in _cache:
        return _cache[cache_key]

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

    params = {
        "q": name,
        "limit": 10,
    }
    headers = {"Authorization": f"ApiKey {api_key}"}
    last_error = ""
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            for delay in [0.0] + _RETRY_DELAYS:
                if delay:
                    await asyncio.sleep(delay)
                resp = await client.get(f"{_BASE}/search/default", params=params, headers=headers)
                if resp.status_code == 429:
                    last_error = "OpenSanctions rate limited (429)"
                    continue
                resp.raise_for_status()
                data = resp.json()
                break
            else:
                return {"total": 0, "risk": "UNKNOWN", "matches": [], "error": last_error}
    except httpx.TimeoutException:
        return {"total": 0, "risk": "UNKNOWN", "matches": [], "error": "OpenSanctions API timeout"}
    except httpx.HTTPStatusError as exc:
        return {"total": 0, "risk": "UNKNOWN", "matches": [], "error": f"OpenSanctions HTTP {exc.response.status_code}"}
    except Exception as exc:
        return {"total": 0, "risk": "UNKNOWN", "matches": [], "error": str(exc)}

    results = data.get("results", [])
    matches = []
    for entity in results:
        props = entity.get("properties", {})
        datasets = entity.get("datasets", [])
        matches.append({
            "id": entity.get("id"),
            "caption": entity.get("caption", ""),
            "schema": entity.get("schema", ""),
            "datasets": datasets,
            "countries": props.get("country", []),
            "aliases": props.get("name", [])[:5],
        })

    result = {
        "query": name,
        "total": data.get("total", {}).get("value", len(matches)),
        "risk": "FLAGGED" if matches else "CLEAR",
        "matches": matches,
        "source_url": source_url,
    }
    _cache[cache_key] = result
    return result
