"""Contract tests for the OpenSanctions source adapter."""

import httpx
import pytest
import respx

CLEAR_RESPONSE = {"results": [], "total": {"value": 0}}

FLAGGED_RESPONSE = {
    "results": [
        {
            "id": "Q12345",
            "caption": "Huawei Technologies",
            "schema": "Company",
            "datasets": ["us_ofac_sdn"],
            "properties": {
                "country": ["cn"],
                "name": ["Huawei", "华为"],
            },
        }
    ],
    "total": {"value": 1},
}


@pytest.mark.asyncio
async def test_screen_entity_clear():
    from semiconductor_mcp.sources import opensanctions

    opensanctions._cache.clear()
    with respx.mock:
        respx.get("https://api.opensanctions.org/search/default").mock(
            return_value=httpx.Response(200, json=CLEAR_RESPONSE)
        )
        result = await opensanctions.screen_entity("Acme Corp", api_key="test-key")

    assert result["risk"] == "CLEAR"
    assert result["total"] == 0
    assert result["matches"] == []


@pytest.mark.asyncio
async def test_screen_entity_flagged():
    from semiconductor_mcp.sources import opensanctions

    opensanctions._cache.clear()
    with respx.mock:
        respx.get("https://api.opensanctions.org/search/default").mock(
            return_value=httpx.Response(200, json=FLAGGED_RESPONSE)
        )
        result = await opensanctions.screen_entity("Huawei", api_key="test-key")

    assert result["risk"] == "FLAGGED"
    assert result["total"] == 1
    assert len(result["matches"]) == 1
    assert "us_ofac_sdn" in result["matches"][0]["datasets"]


@pytest.mark.asyncio
async def test_screen_entity_no_api_key_returns_unknown():
    from semiconductor_mcp.sources import opensanctions

    result = await opensanctions.screen_entity("Anyone", api_key="")
    assert result["risk"] == "UNKNOWN"
    assert "note" in result


@pytest.mark.asyncio
async def test_screen_entity_caches_result():
    from semiconductor_mcp.sources import opensanctions

    opensanctions._cache.clear()
    with respx.mock:
        route = respx.get("https://api.opensanctions.org/search/default").mock(
            return_value=httpx.Response(200, json=CLEAR_RESPONSE)
        )
        await opensanctions.screen_entity("Acme Corp", api_key="test-key")
        await opensanctions.screen_entity("Acme Corp", api_key="test-key")

    assert route.call_count == 1


@pytest.mark.asyncio
async def test_screen_entity_handles_timeout():
    from semiconductor_mcp.sources import opensanctions

    opensanctions._cache.clear()
    with respx.mock:
        respx.get("https://api.opensanctions.org/search/default").mock(
            side_effect=httpx.TimeoutException("timeout")
        )
        result = await opensanctions.screen_entity("Corp", api_key="test-key")

    assert result["risk"] == "UNKNOWN"
    assert "error" in result
