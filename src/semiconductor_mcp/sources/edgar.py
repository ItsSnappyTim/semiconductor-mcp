"""SEC EDGAR full-text search (EFTS) — free, no API key required.

Equipment and materials companies are required to disclose supply chain risks,
single-source dependencies, and geographic concentration in SEC filings.
This client searches 10-K and 10-Q filings for relevant disclosures.
"""

from typing import Any

import httpx

_EFTS_BASE = "https://efts.sec.gov/LATEST/search-index"
_FILING_BASE = "https://www.sec.gov/Archives"
_TIMEOUT = 20


async def search_filings(
    company: str,
    topic: str,
    forms: str = "10-K,10-Q",
    start_date: str = "2022-01-01",
    max_results: int = 5,
) -> list[dict[str, Any]]:
    """Search EDGAR full-text for supply chain disclosures in SEC filings.

    Returns up to max_results filing excerpts matching the company + topic.
    """
    # EDGAR EFTS uses the _source endpoint for full-text search
    params = {
        "q": f'"{company}" "{topic}"',
        "forms": forms,
        "dateRange": "custom",
        "startdt": start_date,
        "hits.hits.total.value": 1,
        "_source": "period_of_report,file_date,form_type,display_names,file_num,period_of_report",
    }
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(_EFTS_BASE, params=params)
            resp.raise_for_status()
        data = resp.json()
    except httpx.TimeoutException:
        return [{"error": "SEC EDGAR API timeout"}]
    except httpx.HTTPStatusError as exc:
        return [{"error": f"SEC EDGAR HTTP {exc.response.status_code}"}]
    except Exception as exc:
        return [{"error": str(exc)}]

    hits = data.get("hits", {}).get("hits", [])
    results = []
    for hit in hits[:max_results]:
        src = hit.get("_source", {})
        entity_names = src.get("display_names", [])
        company_name = entity_names[0].get("name", "") if entity_names else ""
        results.append({
            "company": company_name,
            "form_type": src.get("form_type", ""),
            "filed_at": src.get("file_date", ""),
            "period": src.get("period_of_report", ""),
            "filing_url": f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&filenum={src.get('file_num', '')}&type={src.get('form_type', '')}&dateb=&owner=include&count=40",
            "excerpt": hit.get("highlight", {}).get("file_date", [""])[0] if hit.get("highlight") else "",
        })

    if not results and not hits:
        # Fallback: return a search URL the user can follow
        search_url = (
            f"https://efts.sec.gov/LATEST/search-index?"
            f"q=%22{company.replace(' ', '+')}%22+%22{topic.replace(' ', '+')}%22"
            f"&forms={forms}&dateRange=custom&startdt={start_date}"
        )
        return [{
            "company": company,
            "topic": topic,
            "result": "No direct API matches; follow URL to search EDGAR",
            "search_url": search_url,
        }]

    return results
