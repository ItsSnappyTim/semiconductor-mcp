"""Commodity price data via Yahoo Finance — free, no API key required.

Provides spot/futures price data for metals used in semiconductor manufacturing.
Data comes from CME/COMEX/NYMEX futures via Yahoo Finance's public chart API.

Available metals (Yahoo Finance futures symbols):
  Gold      → GC=F  (USD/troy oz)  — wire bonding, contacts
  Silver    → SI=F  (USD/troy oz)  — conductive pastes, contacts
  Copper    → HG=F  (USD/lb → converted to USD/kg)  — Cu interconnects, ECD
  Palladium → PA=F  (USD/troy oz)  — ENIG plating, IC packaging, catalysts
  Platinum  → PL=F  (USD/troy oz)  — specialty applications
  Aluminum  → ALI=F (USD/mt)       — older Al interconnects, leadframes

NOT available via free public APIs:
  Cobalt, Gallium, Germanium, Nickel, Ruthenium, Tantalum, Hafnium, Indium, Tin
  (LME/COMEX specialty metals require subscription; USGS publishes annual averages)
"""

from datetime import UTC, datetime
from typing import Any

import httpx

from ..cache import TTLCache
from ..http_client import request_with_retry
from ..schemas import CommodityPrice

_BASE = "https://query1.finance.yahoo.com/v8/finance/chart"
_TIMEOUT = 15.0
_HEADERS = {"User-Agent": "semiconductor-mcp-research/1.0"}

_SYMBOL_MAP: dict[str, tuple[str, str, str | None]] = {
    "gold":      ("GC=F", "USD/troy oz", None),
    "silver":    ("SI=F", "USD/troy oz", None),
    "copper":    ("HG=F", "USD/lb",      "multiply by 2204.62 for USD/mt"),
    "palladium": ("PA=F", "USD/troy oz", None),
    "platinum":  ("PL=F", "USD/troy oz", None),
    "aluminum":  ("ALI=F", "USD/mt",    None),
    "aluminium": ("ALI=F", "USD/mt",    None),
    "au": ("GC=F", "USD/troy oz", None),
    "ag": ("SI=F", "USD/troy oz", None),
    "cu": ("HG=F", "USD/lb",      "multiply by 2204.62 for USD/mt"),
    "pd": ("PA=F", "USD/troy oz", None),
    "pt": ("PL=F", "USD/troy oz", None),
    "al": ("ALI=F", "USD/mt",    None),
}

_UNAVAILABLE = {
    "cobalt", "co", "gallium", "ga", "germanium", "ge",
    "nickel", "ni", "ruthenium", "ru", "tantalum", "ta",
    "hafnium", "hf", "indium", "in", "tin", "sn",
    "tungsten", "w", "rhenium", "re",
}

_USGS_URL = (
    "https://www.usgs.gov/centers/national-minerals-information-center/"
    "commodity-statistics-and-information"
)
_LME_URL = "https://www.lme.com/Metals"

# Commodity prices are fairly stable at hourly granularity
_cache: TTLCache = TTLCache(ttl_seconds=3600, name="world_bank")  # 1 hour


async def get_commodity_price(material: str, months: int = 13) -> CommodityPrice | dict[str, Any]:
    """Fetch recent commodity price data for a metal used in semiconductor manufacturing."""
    key = material.lower().strip()

    if key in _UNAVAILABLE:
        return {
            "material": material,
            "available": False,
            "note": (
                f"'{material}' price data is not available via free public APIs. "
                "Specialty metals like cobalt, gallium, germanium, nickel, tin, and ruthenium "
                "are traded OTC or on the LME without free public price feeds. "
                "Annual averages: USGS Mineral Commodity Summaries (free). "
                "Real-time/historical: LME (subscription)."
            ),
            "usgs_url": _USGS_URL,
            "lme_url": _LME_URL,
        }

    mapping = _SYMBOL_MAP.get(key)
    if mapping is None:
        supported = sorted({k for k in _SYMBOL_MAP if len(k) > 2})
        return {
            "material": material,
            "available": False,
            "note": (
                f"No price data found for '{material}'. "
                f"Supported metals: {', '.join(supported)}."
            ),
        }

    cache_key = f"{key}:{months}"
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached

    symbol, unit, conversion_note = mapping
    yf_range = f"{min(max(months, 1), 24)}mo"

    try:
        resp = await request_with_retry(
            f"{_BASE}/{symbol}",
            params={"interval": "1mo", "range": yf_range},
            headers=_HEADERS,
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
    except httpx.TimeoutException:
        return {"material": material, "available": False, "error": "Yahoo Finance API timeout"}
    except httpx.HTTPStatusError as exc:
        return {"material": material, "available": False, "error": f"Yahoo Finance HTTP {exc.response.status_code}"}
    except Exception as exc:
        return {"material": material, "available": False, "error": str(exc)}

    result_list = (data.get("chart") or {}).get("result") or []
    if not result_list:
        err = (data.get("chart") or {}).get("error") or {}
        return {"material": material, "available": False, "error": str(err) or "No data returned"}

    chart = result_list[0]
    timestamps = chart.get("timestamp", [])
    closes = (chart.get("indicators") or {}).get("quote", [{}])[0].get("close", [])

    prices = []
    for ts, price in zip(timestamps, closes):
        if price is None:
            continue
        dt = datetime.fromtimestamp(ts, tz=UTC).strftime("%Y-%m")
        prices.append({"date": dt, "value": round(price, 4)})

    prices.sort(key=lambda x: x["date"])

    latest = prices[-1] if prices else None
    previous = prices[-2] if len(prices) >= 2 else None

    trend = "stable"
    pct_change: float | None = None
    if latest and previous and previous["value"]:
        pct_change = round(
            (latest["value"] - previous["value"]) / previous["value"] * 100, 2
        )
        if pct_change > 2:
            trend = "rising"
        elif pct_change < -2:
            trend = "falling"

    result = CommodityPrice(
        material=material,
        symbol=symbol,
        unit=unit,
        available=True,
        latest_price=latest["value"] if latest else None,
        latest_date=latest["date"] if latest else None,
        previous_price=previous["value"] if previous else None,
        previous_date=previous["date"] if previous else None,
        pct_change_month=pct_change,
        trend=trend,
        history=prices,
        source_url=f"https://finance.yahoo.com/quote/{symbol}",
    )
    if conversion_note:
        result["conversion_note"] = conversion_note  # type: ignore[typeddict-unknown-key]

    _cache.set(cache_key, result)
    return result
