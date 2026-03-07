"""Contract tests for the BIS/ITA screening source adapter."""

import httpx
import pytest
import respx

CLEAR_RESPONSE = {"total": 0, "results": []}

BLOCKED_RESPONSE = {
    "total": 1,
    "results": [
        {
            "name": "Shady Corp",
            "source": "Entity List",
            "country": "CN",
            "addresses": [],
            "federal_register_notice": "85 FR 12345",
            "end_date": "",
        }
    ],
}

FLAGGED_RESPONSE = {
    "total": 1,
    "results": [
        {
            "name": "Risky Corp",
            "source": "Unverified List",
            "country": "RU",
            "addresses": [],
            "federal_register_notice": "",
            "end_date": "",
        }
    ],
}


@pytest.mark.asyncio
async def test_screen_entity_no_api_key():
    from semiconductor_mcp.sources import bis_screening

    result = await bis_screening.screen_entity("Anyone", api_key="")
    assert result["risk"] == "UNKNOWN"
    assert "note" in result


@pytest.mark.asyncio
async def test_screen_entity_clear():
    from semiconductor_mcp.sources import bis_screening

    bis_screening._cache.clear()
    with respx.mock:
        respx.get("https://data.trade.gov/consolidated_screening_list/v1/search").mock(
            return_value=httpx.Response(200, json=CLEAR_RESPONSE)
        )
        result = await bis_screening.screen_entity("Acme Corp", api_key="test-key")

    assert result["risk"] == "CLEAR"
    assert result["total"] == 0


@pytest.mark.asyncio
async def test_screen_entity_blocked():
    from semiconductor_mcp.sources import bis_screening

    bis_screening._cache.clear()
    with respx.mock:
        respx.get("https://data.trade.gov/consolidated_screening_list/v1/search").mock(
            return_value=httpx.Response(200, json=BLOCKED_RESPONSE)
        )
        result = await bis_screening.screen_entity("Shady Corp", api_key="test-key")

    assert result["risk"] == "BLOCKED"


@pytest.mark.asyncio
async def test_screen_entity_flagged():
    from semiconductor_mcp.sources import bis_screening

    bis_screening._cache.clear()
    with respx.mock:
        respx.get("https://data.trade.gov/consolidated_screening_list/v1/search").mock(
            return_value=httpx.Response(200, json=FLAGGED_RESPONSE)
        )
        result = await bis_screening.screen_entity("Risky Corp", api_key="test-key")

    assert result["risk"] == "FLAGGED"


@pytest.mark.asyncio
async def test_screen_entity_handles_timeout():
    from semiconductor_mcp.sources import bis_screening

    bis_screening._cache.clear()
    with respx.mock:
        respx.get("https://data.trade.gov/consolidated_screening_list/v1/search").mock(
            side_effect=httpx.TimeoutException("timeout")
        )
        result = await bis_screening.screen_entity("Corp", api_key="test-key")

    assert result["risk"] == "UNKNOWN"
    assert "error" in result
