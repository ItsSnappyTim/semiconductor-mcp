"""Contract tests for the world_bank (commodity prices) source adapter."""

import httpx
import pytest
import respx

SAMPLE_YAHOO_RESPONSE = {
    "chart": {
        "result": [
            {
                "meta": {"exchangeName": "COMEX"},
                "timestamp": [1704067200, 1706745600],
                "indicators": {
                    "quote": [{"close": [2050.5, 2075.3]}]
                },
            }
        ],
        "error": None,
    }
}


@pytest.mark.asyncio
async def test_get_commodity_price_gold():
    from semiconductor_mcp.sources import world_bank

    world_bank._cache.clear()
    with respx.mock:
        respx.get("https://query1.finance.yahoo.com/v8/finance/chart/GC=F").mock(
            return_value=httpx.Response(200, json=SAMPLE_YAHOO_RESPONSE)
        )
        result = await world_bank.get_commodity_price("gold")

    assert result["available"] is True
    assert result["material"] == "gold"
    assert result["symbol"] == "GC=F"
    assert result["unit"] == "USD/troy oz"
    assert result["latest_price"] == 2075.3
    assert result["trend"] in ("rising", "stable", "falling")


@pytest.mark.asyncio
async def test_get_commodity_price_unavailable_metal():
    from semiconductor_mcp.sources import world_bank

    result = await world_bank.get_commodity_price("cobalt")
    assert result["available"] is False
    assert "note" in result


@pytest.mark.asyncio
async def test_get_commodity_price_unknown_metal():
    from semiconductor_mcp.sources import world_bank

    result = await world_bank.get_commodity_price("unobtanium")
    assert result["available"] is False


@pytest.mark.asyncio
async def test_get_commodity_price_caches():
    from semiconductor_mcp.sources import world_bank

    world_bank._cache.clear()
    with respx.mock:
        route = respx.get("https://query1.finance.yahoo.com/v8/finance/chart/GC=F").mock(
            return_value=httpx.Response(200, json=SAMPLE_YAHOO_RESPONSE)
        )
        await world_bank.get_commodity_price("gold")
        await world_bank.get_commodity_price("gold")

    assert route.call_count == 1


@pytest.mark.asyncio
async def test_get_commodity_price_handles_timeout():
    from semiconductor_mcp.sources import world_bank

    world_bank._cache.clear()
    with respx.mock:
        respx.get("https://query1.finance.yahoo.com/v8/finance/chart/PA=F").mock(
            side_effect=httpx.TimeoutException("timeout")
        )
        result = await world_bank.get_commodity_price("palladium")

    assert result["available"] is False
    assert "error" in result
