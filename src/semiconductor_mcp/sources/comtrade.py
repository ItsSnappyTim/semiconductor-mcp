"""UN Comtrade API client — optional, requires free COMTRADE_API_KEY.

Free key available at comtradeapi.un.org (Public - v1 tier).

Notes on free tier behaviour:
- World aggregate (reporterCode=0) returns no data; must use specific country codes.
- Descriptor fields (reporterDesc, cmdDesc, flowDesc) are null; we map codes to names.
- HS codes must be 6 digits with no period (e.g. "280530" not "2805.30").
"""

from typing import Any

import httpx

from ..cache import TTLCache
from ..http_client import request_with_retry
from ..schemas import TradeFlowResult

_BASE = "https://comtradeapi.un.org/data/v1/get/C/A/HS"
_TIMEOUT = 30.0
_RETRY_DELAYS = [5.0, 15.0]  # Comtrade free tier is strict on rate limits

# Major semiconductor supply chain countries (ISO numeric codes)
_REPORTER_CODES = (
    "156,840,392,276,410,158,528,56,250,826,643,36,124,076,356,764,702,704,616,528"
)

_COUNTRY_NAMES: dict[int, str] = {
    156: "China", 840: "USA", 392: "Japan", 276: "Germany", 410: "South Korea",
    158: "Taiwan", 528: "Netherlands", 56: "Belgium", 250: "France", 826: "UK",
    643: "Russia", 36: "Australia", 124: "Canada", 76: "Brazil", 356: "India",
    764: "Thailand", 702: "Singapore", 704: "Vietnam", 616: "Poland",
    752: "Sweden", 756: "Switzerland", 442: "Luxembourg", 372: "Ireland",
}

# Annual trade data doesn't change — cache for 24 hours
_cache: TTLCache = TTLCache(ttl_seconds=86400, name="comtrade")


def _normalise_hs(code: str) -> str:
    return code.replace(".", "").replace(" ", "")


async def get_trade_flow(hs_code: str, api_key: str, year: int = 2022) -> TradeFlowResult | dict[str, Any]:
    """Retrieve annual export trade flow data for an HS commodity code."""
    if not api_key:
        return {
            "hs_code": hs_code,
            "year": year,
            "data": [],
            "note": (
                "COMTRADE_API_KEY not configured. Register free at "
                "comtradeapi.un.org to enable trade flow data."
            ),
        }

    cache_key = f"{hs_code}:{year}"
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached

    cmd_code = _normalise_hs(hs_code)
    params = {
        "reporterCode": _REPORTER_CODES,
        "period": str(year),
        "partnerCode": "0",
        "cmdCode": cmd_code,
        "flowCode": "X",
        "maxRecords": "500",
        "format": "JSON",
    }
    headers = {"Ocp-Apim-Subscription-Key": api_key}

    try:
        resp = await request_with_retry(
            _BASE,
            params=params,
            headers=headers,
            timeout=_TIMEOUT,
            retry_delays=_RETRY_DELAYS,
        )
        if resp.status_code == 429:
            return {"hs_code": hs_code, "data": [], "error": "Comtrade rate limited (429)"}
        resp.raise_for_status()
        data = resp.json()
    except httpx.TimeoutException:
        return {"hs_code": hs_code, "data": [], "error": "Comtrade API timeout"}
    except httpx.HTTPStatusError as exc:
        return {"hs_code": hs_code, "data": [], "error": f"Comtrade API HTTP {exc.response.status_code}"}
    except Exception as exc:
        return {"hs_code": hs_code, "data": [], "error": str(exc)}

    records = data.get("data", [])
    if not records:
        return {
            "hs_code": hs_code,
            "year": year,
            "data": [],
            "note": f"No data returned for HS {hs_code} in {year}. Try an adjacent year.",
        }

    exporters: dict[int, float] = {}
    for r in records:
        code = r.get("reporterCode")
        value = float(r.get("primaryValue") or 0)
        if code is not None:
            exporters[int(code)] = exporters.get(int(code), 0) + value

    total = sum(exporters.values())
    top_exporters = sorted(exporters.items(), key=lambda x: x[1], reverse=True)[:10]

    result = TradeFlowResult(
        hs_code=hs_code,
        year=year,
        total_exports_usd=round(total),
        top_exporters=[
            {
                "country": _COUNTRY_NAMES.get(code, f"Code {code}"),
                "reporter_code": code,
                "value_usd": round(val),
                "share_pct": round(val / total * 100, 1) if total else 0,
            }
            for code, val in top_exporters
        ],
        record_count=len(records),
        note=f"Export data for {len(_REPORTER_CODES.split(','))} major semiconductor supply chain countries.",
    )
    _cache.set(cache_key, result)
    return result
