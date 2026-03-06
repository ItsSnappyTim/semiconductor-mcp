"""UN Comtrade API client — optional, requires free COMTRADE_API_KEY.

New Comtrade API (comtradeapi.un.org) requires a subscription key.
Free tier available with registration at https://comtradeapi.un.org/

Without a key, returns an informational response with the HS code so the
user can look up data manually at comtradeapi.un.org.
"""

from typing import Any

import httpx

_BASE = "https://comtradeapi.un.org/data/v1/get/C/A/HS"
_TIMEOUT = 30


async def get_trade_flow(hs_code: str, api_key: str, year: int = 2023) -> dict[str, Any]:
    """Retrieve annual trade flow data for an HS commodity code.

    Returns top exporting and importing countries with volumes (USD thousands).
    Requires COMTRADE_API_KEY.
    """
    if not api_key:
        return {
            "hs_code": hs_code,
            "year": year,
            "data": [],
            "note": (
                f"COMTRADE_API_KEY not configured. Register free at "
                f"https://comtradeapi.un.org/ to enable trade flow data. "
                f"Manual lookup: https://comtradeplus.un.org/TradeFlow?"
                f"Frequency=A&Flows=X,M&CommodityCodes={hs_code}&partners=0&reporters=all"
                f"&period={year}&AggregateBy=none&BreakdownMode=plus"
            ),
        }

    params = {
        "reporterCode": "0",   # 0 = world aggregated
        "period": str(year),
        "partnerCode": "0",    # 0 = all partners
        "cmdCode": hs_code,
        "flowCode": "X,M",     # exports and imports
        "maxRecords": "500",
        "format": "JSON",
        "breakdownMode": "plus",
        "countOnly": "false",
    }
    headers = {"Ocp-Apim-Subscription-Key": api_key}

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(_BASE, params=params, headers=headers)
            resp.raise_for_status()
        data = resp.json()
    except httpx.TimeoutException:
        return {"hs_code": hs_code, "data": [], "error": "Comtrade API timeout"}
    except httpx.HTTPStatusError as exc:
        return {"hs_code": hs_code, "data": [], "error": f"Comtrade API HTTP {exc.response.status_code}"}
    except Exception as exc:
        return {"hs_code": hs_code, "data": [], "error": str(exc)}

    records = data.get("data", [])

    # Summarize: top exporters and importers
    exporters: dict[str, float] = {}
    importers: dict[str, float] = {}
    for r in records:
        reporter = r.get("reporterDesc", r.get("reporterCode", ""))
        flow = r.get("flowDesc", r.get("flowCode", ""))
        value = float(r.get("primaryValue", 0) or 0)
        if "export" in flow.lower():
            exporters[reporter] = exporters.get(reporter, 0) + value
        elif "import" in flow.lower():
            importers[reporter] = importers.get(reporter, 0) + value

    top_exporters = sorted(exporters.items(), key=lambda x: x[1], reverse=True)[:10]
    top_importers = sorted(importers.items(), key=lambda x: x[1], reverse=True)[:10]
    total_export = sum(exporters.values())

    return {
        "hs_code": hs_code,
        "year": year,
        "total_exports_usd_thousands": round(total_export),
        "top_exporters": [
            {
                "country": country,
                "value_usd_thousands": round(val),
                "share_pct": round(val / total_export * 100, 1) if total_export else 0,
            }
            for country, val in top_exporters
        ],
        "top_importers": [
            {"country": country, "value_usd_thousands": round(val)}
            for country, val in top_importers
        ],
        "record_count": len(records),
    }
