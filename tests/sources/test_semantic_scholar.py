"""Contract tests for the Semantic Scholar source adapter."""

import httpx
import pytest
import respx

SAMPLE_RESPONSE = {
    "data": [
        {
            "title": "Gate-all-around transistors for 2nm node",
            "abstract": "We present GAAFET transistor fabrication at 2nm node.",
            "year": 2024,
            "authors": [{"name": "Jane Doe"}, {"name": "John Smith"}],
            "url": "https://semanticscholar.org/paper/abc123",
            "externalIds": {"DOI": "10.1109/gaafet.2024"},
            "citationCount": 42,
        }
    ]
}


@pytest.mark.asyncio
async def test_search_returns_parsed_results():
    from semiconductor_mcp.sources import semantic_scholar

    semantic_scholar._cache.clear()
    with respx.mock:
        respx.get("https://api.semanticscholar.org/graph/v1/paper/search").mock(
            return_value=httpx.Response(200, json=SAMPLE_RESPONSE)
        )
        results = await semantic_scholar.search("gaafet transistor 2nm")

    assert len(results) == 1
    assert results[0]["source"] == "semantic_scholar"
    assert results[0]["title"] == "Gate-all-around transistors for 2nm node"
    assert results[0]["year"] == "2024"
    assert results[0]["doi"] == "10.1109/gaafet.2024"
    assert results[0]["citation_count"] == 42


@pytest.mark.asyncio
async def test_search_returns_empty_on_timeout():
    from semiconductor_mcp.sources import semantic_scholar

    semantic_scholar._cache.clear()
    with respx.mock:
        respx.get("https://api.semanticscholar.org/graph/v1/paper/search").mock(
            side_effect=httpx.TimeoutException("timeout")
        )
        results = await semantic_scholar.search("test")

    assert results == []


@pytest.mark.asyncio
async def test_search_caches_results():
    from semiconductor_mcp.sources import semantic_scholar

    semantic_scholar._cache.clear()
    with respx.mock:
        route = respx.get("https://api.semanticscholar.org/graph/v1/paper/search").mock(
            return_value=httpx.Response(200, json=SAMPLE_RESPONSE)
        )
        await semantic_scholar.search("gaafet transistor 2nm", max_results=5)
        await semantic_scholar.search("gaafet transistor 2nm", max_results=5)

    assert route.call_count == 1
