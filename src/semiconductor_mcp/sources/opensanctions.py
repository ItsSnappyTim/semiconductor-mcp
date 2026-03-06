"""OpenSanctions entity screening — free, no API key required.

Checks a company or individual name against 100+ global sanctions datasets
including OFAC SDN, EU/UN/UK sanctions, and national lists.
"""

from typing import Any

import httpx

_BASE = "https://api.opensanctions.org"
_TIMEOUT = 20


async def screen_entity(name: str) -> dict[str, Any]:
    """Screen an entity name against OpenSanctions consolidated dataset.

    Returns a dict with:
      total      — number of matches found
      risk       — "CLEAR" | "FLAGGED"
      matches    — list of matching entities with list details
      source_url — permalink to OpenSanctions results for review
    """
    params = {
        "q": name,
        "schema": "LegalEntity",
        "datasets": "default",
        "limit": 10,
    }
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(f"{_BASE}/entities/", params=params)
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

    source_url = f"https://www.opensanctions.org/search/?q={name.replace(' ', '+')}"
    return {
        "query": name,
        "total": data.get("total", {}).get("value", len(matches)),
        "risk": "FLAGGED" if matches else "CLEAR",
        "matches": matches,
        "source_url": source_url,
    }
