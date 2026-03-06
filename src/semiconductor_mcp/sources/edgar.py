"""SEC EDGAR full-text search (EFTS) — free, no API key required.

Equipment and materials companies are required to disclose supply chain risks,
single-source dependencies, and geographic concentration in SEC filings.
This client searches 10-K and 10-Q filings for relevant disclosures.
"""

from typing import Any

import httpx

_EFTS_BASE = "https://efts.sec.gov/LATEST/search-index"
_TIMEOUT = 20
# SEC EDGAR requires a descriptive User-Agent or returns 403
_HEADERS = {"User-Agent": "semiconductor-mcp-research/1.0 research@semiconductor-mcp.app"}


def _filing_url(cik: str, adsh: str) -> str:
    """Build EDGAR filing index URL from CIK and accession number."""
    cik_int = str(int(cik.lstrip("0") or "0"))
    adsh_clean = adsh.replace("-", "")
    return f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{adsh_clean}/"


async def search_filings(
    company: str,
    topic: str,
    forms: str = "10-K,10-Q",
    start_date: str = "2022-01-01",
    max_results: int = 5,
) -> list[dict[str, Any]]:
    """Search EDGAR full-text for supply chain disclosures in SEC filings.

    Returns up to max_results filing records matching the company + topic.
    """
    params = {
        "q": f'"{company}" "{topic}"',
        "forms": forms,
        "dateRange": "custom",
        "startdt": start_date,
    }
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(_EFTS_BASE, params=params, headers=_HEADERS)
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
        display_names = src.get("display_names", [])
        company_name = display_names[0] if display_names else company
        ciks = src.get("ciks", [""])
        adsh = src.get("adsh", "")
        results.append({
            "company_name": company_name,
            "form_type": src.get("form", src.get("file_type", "")),
            "filed_at": src.get("file_date", ""),
            "period": src.get("period_ending", ""),
            "file_url": _filing_url(ciks[0], adsh) if ciks and adsh else "",
            "excerpt": "",  # EFTS index endpoint does not return text excerpts
        })

    if not results:
        search_url = (
            f"https://efts.sec.gov/LATEST/search-index?"
            f"q=%22{company.replace(' ', '+')}%22+%22{topic.replace(' ', '+')}%22"
            f"&forms={forms}&dateRange=custom&startdt={start_date}"
        )
        return [{
            "company": company,
            "topic": topic,
            "result": "No matches found",
            "search_url": search_url,
        }]

    return results
