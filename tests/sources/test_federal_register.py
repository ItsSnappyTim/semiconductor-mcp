"""Contract tests for the Federal Register source adapter."""

import httpx
import pytest
import respx

SAMPLE_RESPONSE = {
    "results": [
        {
            "title": "Addition of Entities to the Entity List",
            "type": "NOTICE",
            "document_number": "2024-12345",
            "publication_date": "2024-03-01",
            "abstract": "The Bureau of Industry and Security adds entities to the Entity List.",
            "html_url": "https://www.federalregister.gov/documents/2024/03/01/2024-12345",
            "agencies": [{"name": "Bureau of Industry and Security"}],
        }
    ]
}

EMPTY_RESPONSE = {"results": []}


@pytest.mark.asyncio
async def test_search_export_controls_returns_docs():
    from semiconductor_mcp.sources import federal_register

    federal_register._cache.clear()
    with respx.mock:
        respx.get("https://www.federalregister.gov/api/v1/documents.json").mock(
            return_value=httpx.Response(200, json=SAMPLE_RESPONSE)
        )
        results = await federal_register.search_export_controls("semiconductor entity list")

    assert len(results) == 1
    assert results[0]["title"] == "Addition of Entities to the Entity List"
    assert results[0]["type"] == "NOTICE"
    assert "Bureau of Industry and Security" in results[0]["agencies"]


@pytest.mark.asyncio
async def test_search_returns_empty_list_on_no_results():
    from semiconductor_mcp.sources import federal_register

    federal_register._cache.clear()
    with respx.mock:
        respx.get("https://www.federalregister.gov/api/v1/documents.json").mock(
            return_value=httpx.Response(200, json=EMPTY_RESPONSE)
        )
        results = await federal_register.search_export_controls("nonexistent query")

    assert results == []


@pytest.mark.asyncio
async def test_search_handles_timeout():
    from semiconductor_mcp.sources import federal_register

    federal_register._cache.clear()
    with respx.mock:
        respx.get("https://www.federalregister.gov/api/v1/documents.json").mock(
            side_effect=httpx.TimeoutException("timeout")
        )
        results = await federal_register.search_export_controls("test")

    assert len(results) == 1
    assert "error" in results[0]


@pytest.mark.asyncio
async def test_caches_results():
    from semiconductor_mcp.sources import federal_register

    federal_register._cache.clear()
    with respx.mock:
        route = respx.get("https://www.federalregister.gov/api/v1/documents.json").mock(
            return_value=httpx.Response(200, json=SAMPLE_RESPONSE)
        )
        await federal_register.search_export_controls("entity list", days=180)
        await federal_register.search_export_controls("entity list", days=180)

    assert route.call_count == 1
