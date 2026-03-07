"""Contract tests for the SEC EDGAR source adapter."""

import httpx
import pytest
import respx

SAMPLE_RESPONSE = {
    "hits": {
        "hits": [
            {
                "_source": {
                    "display_names": ["TSMC"],
                    "form": "10-K",
                    "file_date": "2024-02-15",
                    "period_ending": "2023-12-31",
                    "ciks": ["0001046179"],
                    "adsh": "0001046179-24-000010",
                }
            },
            {
                "_source": {
                    "display_names": ["Taiwan Semiconductor Manufacturing"],
                    "form": "10-Q",
                    "file_date": "2024-05-01",
                    "period_ending": "2024-03-31",
                    "ciks": ["0001046179"],
                    "adsh": "0001046179-24-000025",
                }
            },
        ]
    }
}

EMPTY_RESPONSE = {"hits": {"hits": []}}


@pytest.mark.asyncio
async def test_search_filings_returns_results():
    from semiconductor_mcp.sources import edgar

    edgar._cache.clear()
    with respx.mock:
        respx.get("https://efts.sec.gov/LATEST/search-index").mock(
            return_value=httpx.Response(200, json=SAMPLE_RESPONSE)
        )
        results = await edgar.search_filings("TSMC", "supply chain")

    assert len(results) == 2
    assert results[0]["company_name"] == "TSMC"
    assert results[0]["form_type"] == "10-K"
    assert results[0]["filed_at"] == "2024-02-15"
    assert results[0]["excerpt"] == ""  # EFTS doesn't return excerpts
    assert "file_url" in results[0]


@pytest.mark.asyncio
async def test_search_filings_no_results_returns_no_match_dict():
    from semiconductor_mcp.sources import edgar

    edgar._cache.clear()
    with respx.mock:
        respx.get("https://efts.sec.gov/LATEST/search-index").mock(
            return_value=httpx.Response(200, json=EMPTY_RESPONSE)
        )
        results = await edgar.search_filings("UnknownCorp", "supply chain")

    assert len(results) == 1
    assert results[0].get("result") == "No matches found"


@pytest.mark.asyncio
async def test_search_filings_handles_timeout():
    from semiconductor_mcp.sources import edgar

    edgar._cache.clear()
    with respx.mock:
        respx.get("https://efts.sec.gov/LATEST/search-index").mock(
            side_effect=httpx.TimeoutException("timeout")
        )
        results = await edgar.search_filings("Corp", "risk")

    assert len(results) == 1
    assert "error" in results[0]


@pytest.mark.asyncio
async def test_search_filings_caches_results():
    from semiconductor_mcp.sources import edgar

    edgar._cache.clear()
    with respx.mock:
        route = respx.get("https://efts.sec.gov/LATEST/search-index").mock(
            return_value=httpx.Response(200, json=SAMPLE_RESPONSE)
        )
        await edgar.search_filings("TSMC", "supply chain")
        await edgar.search_filings("TSMC", "supply chain")

    assert route.call_count == 1
