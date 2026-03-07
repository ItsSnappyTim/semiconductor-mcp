"""Federal Register API client — free, no API key required.

Searches for U.S. regulatory documents relevant to semiconductor export controls,
entity list additions, EAR amendments, and OFAC sanctions rules.

Key agencies for semiconductor controls:
  - BIS  (Bureau of Industry and Security): EAR, Entity List, CCL changes
  - OFAC (Office of Foreign Assets Control): SDN updates, sanctions rules
"""

from typing import Any

import httpx

from ..cache import TTLCache
from ..http_client import request_with_retry
from ..schemas import RegulationDoc

_BASE = "https://www.federalregister.gov/api/v1/documents.json"
_TIMEOUT = 20.0
_HEADERS = {"User-Agent": "semiconductor-mcp-research/1.0"}

_AGENCIES = {
    "bis": "industry-and-security-bureau",
    "ofac": "foreign-assets-control-office",
    "commerce": "commerce-department",
}

_DOC_TYPES = ["RULE", "PRORULE", "NOTICE"]

_cache: TTLCache = TTLCache(ttl_seconds=3600, name="federal_register")  # 1 hour


async def search_regulations(
    query: str,
    days: int = 180,
    agencies: list[str] | None = None,
) -> list[RegulationDoc | dict[str, Any]]:
    """Search Federal Register for recent regulatory documents."""
    from datetime import date, timedelta

    if agencies is None:
        agencies = [_AGENCIES["bis"], _AGENCIES["ofac"]]

    cache_key = f"{query}:{days}:{','.join(sorted(agencies))}"
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached

    start_date = (date.today() - timedelta(days=min(days, 365))).isoformat()

    params: list[tuple[str, str]] = [
        ("conditions[term]", query),
        ("conditions[publication_date][gte]", start_date),
        ("per_page", "10"),
        ("order", "newest"),
    ]
    for agency in agencies:
        params.append(("conditions[agencies][]", agency))
    for doc_type in _DOC_TYPES:
        params.append(("conditions[type][]", doc_type))
    for field in ["title", "type", "document_number", "publication_date", "abstract", "html_url", "agencies"]:
        params.append(("fields[]", field))

    try:
        resp = await request_with_retry(_BASE, params=params, headers=_HEADERS, timeout=_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except httpx.TimeoutException:
        return [{"error": "Federal Register API timeout"}]
    except httpx.HTTPStatusError as exc:
        return [{"error": f"Federal Register HTTP {exc.response.status_code}"}]
    except Exception as exc:
        return [{"error": str(exc)}]

    docs = data.get("results", [])
    results: list[RegulationDoc] = [
        RegulationDoc(
            title=d.get("title", ""),
            type=d.get("type", ""),
            document_number=d.get("document_number", ""),
            date=d.get("publication_date", ""),
            abstract=(d.get("abstract") or "")[:400],
            url=d.get("html_url", ""),
            agencies=[a.get("name", "") for a in (d.get("agencies") or [])],
        )
        for d in docs
    ]
    _cache.set(cache_key, results)
    return results


async def search_export_controls(query: str, days: int = 180) -> list[RegulationDoc | dict[str, Any]]:
    """Search BIS/OFAC for export control and sanctions regulatory updates."""
    return await search_regulations(
        query=query,
        days=days,
        agencies=[_AGENCIES["bis"], _AGENCIES["ofac"]],
    )
