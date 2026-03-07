"""Contract tests for the GDELT source adapter."""

import httpx
import pytest
import respx

SAMPLE_RESPONSE = {
    "articles": [
        {
            "title": "ASML restricts EUV machine exports to China",
            "url": "https://example.com/news/1",
            "domain": "example.com",
            "seendate": "20240301120000",
            "language": "English",
        },
        {
            "title": "Semiconductor supply chain diversification efforts",
            "url": "https://example.com/news/2",
            "domain": "example.com",
            "seendate": "20240228090000",
            "language": "English",
        },
    ]
}

EMPTY_RESPONSE = {"articles": []}


@pytest.mark.asyncio
async def test_search_supply_chain_news_returns_articles():
    from semiconductor_mcp.sources import gdelt

    gdelt._cache.clear()
    with respx.mock:
        respx.get("https://api.gdeltproject.org/api/v2/doc/doc").mock(
            return_value=httpx.Response(200, json=SAMPLE_RESPONSE)
        )
        results = await gdelt.search_supply_chain_news("ASML")

    assert len(results) == 2
    assert results[0]["title"] == "ASML restricts EUV machine exports to China"
    assert results[0]["domain"] == "example.com"
    assert "url" in results[0]


@pytest.mark.asyncio
async def test_uses_https_url():
    """GDELT URL must use HTTPS (P2 fix from review)."""
    from semiconductor_mcp.sources import gdelt

    assert gdelt._BASE.startswith("https://"), "GDELT base URL must use HTTPS"


@pytest.mark.asyncio
async def test_search_handles_timeout():
    from semiconductor_mcp.sources import gdelt

    gdelt._cache.clear()
    with respx.mock:
        respx.get("https://api.gdeltproject.org/api/v2/doc/doc").mock(
            side_effect=httpx.TimeoutException("timeout")
        )
        results = await gdelt.search_supply_chain_news("ASML")

    assert len(results) == 1
    assert "error" in results[0]


@pytest.mark.asyncio
async def test_search_grey_market_returns_articles():
    from semiconductor_mcp.sources import gdelt

    gdelt._cache.clear()
    with respx.mock:
        respx.get("https://api.gdeltproject.org/api/v2/doc/doc").mock(
            return_value=httpx.Response(200, json=SAMPLE_RESPONSE)
        )
        results = await gdelt.search_grey_market_signals("semiconductor")

    assert isinstance(results, list)


@pytest.mark.asyncio
async def test_cache_prevents_duplicate_requests():
    from semiconductor_mcp.sources import gdelt

    gdelt._cache.clear()
    with respx.mock:
        route = respx.get("https://api.gdeltproject.org/api/v2/doc/doc").mock(
            return_value=httpx.Response(200, json=SAMPLE_RESPONSE)
        )
        await gdelt.search_supply_chain_news("ASML", days=90)
        await gdelt.search_supply_chain_news("ASML", days=90)

    assert route.call_count == 1
