"""Contract tests for the arXiv source adapter."""

import httpx
import pytest
import respx

SAMPLE_XML = """\
<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:arxiv="http://arxiv.org/schemas/atom">
  <entry>
    <id>https://arxiv.org/abs/2401.00001</id>
    <title>EUV Lithography Source Power Scaling</title>
    <summary>We report advances in EUV source power for high-volume manufacturing.</summary>
    <published>2024-01-15T00:00:00Z</published>
    <author><name>Alice Smith</name></author>
    <author><name>Bob Jones</name></author>
    <arxiv:doi>10.1234/euv2024</arxiv:doi>
  </entry>
</feed>"""

EMPTY_XML = """\
<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"></feed>"""


@pytest.mark.asyncio
async def test_search_returns_parsed_results():
    from semiconductor_mcp.sources import arxiv

    arxiv._cache.clear()
    with respx.mock:
        respx.get("https://export.arxiv.org/api/query").mock(
            return_value=httpx.Response(200, text=SAMPLE_XML)
        )
        results = await arxiv.search("euv lithography")

    assert len(results) == 1
    assert results[0]["source"] == "arxiv"
    assert results[0]["title"] == "EUV Lithography Source Power Scaling"
    assert results[0]["year"] == "2024"
    assert results[0]["doi"] == "10.1234/euv2024"
    assert "Alice Smith" in results[0]["authors"]


@pytest.mark.asyncio
async def test_search_returns_empty_on_no_results():
    from semiconductor_mcp.sources import arxiv

    arxiv._cache.clear()
    with respx.mock:
        respx.get("https://export.arxiv.org/api/query").mock(
            return_value=httpx.Response(200, text=EMPTY_XML)
        )
        results = await arxiv.search("nonexistentquery12345")

    assert results == []


@pytest.mark.asyncio
async def test_search_returns_empty_on_timeout():
    from semiconductor_mcp.sources import arxiv

    arxiv._cache.clear()
    with respx.mock:
        respx.get("https://export.arxiv.org/api/query").mock(
            side_effect=httpx.TimeoutException("timeout")
        )
        results = await arxiv.search("something")

    assert results == []


@pytest.mark.asyncio
async def test_search_uses_cache_on_second_call():
    from semiconductor_mcp.sources import arxiv

    arxiv._cache.clear()
    with respx.mock:
        route = respx.get("https://export.arxiv.org/api/query").mock(
            return_value=httpx.Response(200, text=SAMPLE_XML)
        )
        await arxiv.search("euv lithography", max_results=3)
        await arxiv.search("euv lithography", max_results=3)

    # Should only have made one real HTTP call
    assert route.call_count == 1


@pytest.mark.asyncio
async def test_search_retries_on_429():
    from semiconductor_mcp.sources import arxiv

    arxiv._cache.clear()
    responses = [
        httpx.Response(429),
        httpx.Response(200, text=SAMPLE_XML),
    ]
    with respx.mock:
        respx.get("https://export.arxiv.org/api/query").mock(side_effect=responses)
        results = await arxiv.search("euv", max_results=1)

    assert len(results) == 1
