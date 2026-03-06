"""OpenSanctions entity screening — optional, requires free OPENSANCTIONS_API_KEY.

Checks a company or individual name against 100+ global sanctions datasets
including OFAC SDN, EU/UN/UK sanctions, and national lists.

Free API key (100 searches/month) at https://www.opensanctions.org/api/
"""

from typing import Any

import httpx

_BASE = "https://api.opensanctions.org"
_TIMEOUT = 20


async def screen_entity(name: str, api_key: str = "") -> dict[str, Any]:
    """Screen an entity name against OpenSanctions consolidated dataset.

    Returns a dict with:
      total      — number of matches found
      risk       — "CLEAR" | "FLAGGED" | "UNKNOWN"
      matches    — list of matching entities with list details
      source_url — permalink to OpenSanctions results for review
    """
    source_url = f"https://www.opensanctions.org/search/?q={name.replace(' ', '+')}"

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
        "schema": "LegalEntity",
        "datasets": "default",
        "limit": 10,
    }
    headers = {"Authorization": f"ApiKey {api_key}"}
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(f"{_BASE}/search/default", params=params, headers=headers)
            resp.raise_for_status()
        data = resp.json()
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

    return {
        "query": name,
        "total": data.get("total", {}).get("value", len(matches)),
        "risk": "FLAGGED" if matches else "CLEAR",
        "matches": matches,
        "source_url": source_url,
    }
