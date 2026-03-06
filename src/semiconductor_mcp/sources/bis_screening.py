"""ITA Consolidated Screening List — optional, requires free ITA_API_KEY.

Combines: BIS Entity List, BIS Denied Persons List, BIS Unverified List,
OFAC SDN, OFAC Consolidated Non-SDN, State AECA Debarred, plus more.
Free API key available at https://developer.trade.gov/

Without a key, this module returns an informational response directing the
user to obtain the free key.
"""

from typing import Any

import httpx

_BASE = "https://api.trade.gov/consolidated_screening_list/search"
_TIMEOUT = 20


async def screen_entity(name: str, api_key: str) -> dict[str, Any]:
    """Screen an entity name against the ITA Consolidated Screening List.

    Returns:
      total    — number of matching records
      results  — list of matches with name, list source, and addresses
      risk     — "CLEAR" | "FLAGGED" | "BLOCKED"
      note     — human-readable summary
    """
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

    params = {"q": name, "api_key": api_key}
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(_BASE, params=params)
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

    results = []
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
    blocked_sources = {"Entity List", "Denied Persons List", "OFAC SDN"}
    flagged_sources = {"Unverified List", "OFAC Non-SDN", "AECA Debarred"}
    risk = "CLEAR"
    if any(r["source_list"] in blocked_sources for r in results):
        risk = "BLOCKED"
    elif any(r["source_list"] in flagged_sources for r in results):
        risk = "FLAGGED"
    elif results:
        risk = "FLAGGED"

    return {
        "query": name,
        "total": total,
        "results": results,
        "risk": risk,
        "note": f"{total} match(es) found across ITA Consolidated Screening List.",
    }
