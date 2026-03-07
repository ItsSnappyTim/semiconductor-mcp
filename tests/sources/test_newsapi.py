"""Contract tests for the NewsAPI source adapter."""

import httpx
import pytest
import respx

SAMPLE_RESPONSE = {
    "status": "ok",
    "articles": [
        {
            "source": {"name": "Reuters"},
            "title": "TSMC boosts Arizona fab investment",
            "description": "TSMC announces additional $5B for Arizona fab expansion.",
            "url": "https://reuters.com/tsmc-arizona",
            "publishedAt": "2024-03-01T10:00:00Z",
        }
    ],
}

EMPTY_RESPONSE = {"status": "ok", "articles": []}


@pytest.mark.asyncio
async def test_search_returns_articles():
    from semiconductor_mcp.sources import newsapi

    with respx.mock:
        respx.get("https://newsapi.org/v2/everything").mock(
            return_value=httpx.Response(200, json=SAMPLE_RESPONSE)
        )
        results = await newsapi.search("TSMC fab")

    assert len(results) == 1
    assert results[0]["source"] == "Reuters"
    assert results[0]["title"] == "TSMC boosts Arizona fab investment"
    assert results[0]["published_at"] == "2024-03-01T10:00:00Z"


@pytest.mark.asyncio
async def test_search_returns_empty_on_no_articles():
    from semiconductor_mcp.sources import newsapi

    with respx.mock:
        respx.get("https://newsapi.org/v2/everything").mock(
            return_value=httpx.Response(200, json=EMPTY_RESPONSE)
        )
        results = await newsapi.search("some query")

    assert results == []


@pytest.mark.asyncio
async def test_search_returns_empty_on_http_error():
    from semiconductor_mcp.sources import newsapi

    with respx.mock:
        respx.get("https://newsapi.org/v2/everything").mock(
            return_value=httpx.Response(401, json={"message": "Unauthorized"})
        )
        # HTTPStatusError raised by raise_for_status → returns []
        results = await newsapi.search("test")

    assert results == []
