"""Tool-level tests for the 4 non-eval MCP tools.

These tests call the tool functions directly (they are regular async functions
decorated with @mcp.tool() which returns them unchanged). Sources are mocked
via unittest.mock to keep tests fast and deterministic.
"""

import json
from unittest.mock import AsyncMock, patch

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_sanctions_result(risk: str, total: int = 0):
    return {"risk": risk, "total": total, "matches": [], "source_url": "https://example.com"}


# ---------------------------------------------------------------------------
# screen_entity
# ---------------------------------------------------------------------------

class TestScreenEntity:
    @pytest.mark.asyncio
    async def test_aggregate_risk_takes_worst(self):
        from semiconductor_mcp.server import screen_entity

        with (
            patch("semiconductor_mcp.server._opensanctions.screen_entity", new_callable=AsyncMock) as mock_os,
            patch("semiconductor_mcp.server._bis_screening.screen_entity", new_callable=AsyncMock) as mock_bis,
        ):
            mock_os.return_value = _make_sanctions_result("CLEAR")
            mock_bis.return_value = {"risk": "BLOCKED", "total": 1, "results": [{"source_list": "Entity List"}]}

            result = json.loads(await screen_entity("Shady Corp", "CN"))

        assert result["aggregate_risk"] == "BLOCKED"

    @pytest.mark.asyncio
    async def test_clear_when_both_clear(self):
        from semiconductor_mcp.server import screen_entity

        with (
            patch("semiconductor_mcp.server._opensanctions.screen_entity", new_callable=AsyncMock) as mock_os,
            patch("semiconductor_mcp.server._bis_screening.screen_entity", new_callable=AsyncMock) as mock_bis,
        ):
            mock_os.return_value = _make_sanctions_result("CLEAR")
            mock_bis.return_value = {"risk": "CLEAR", "total": 0, "results": []}

            result = json.loads(await screen_entity("Acme Corp"))

        assert result["aggregate_risk"] == "CLEAR"
        assert "recommendation" in result

    @pytest.mark.asyncio
    async def test_handles_source_exception(self):
        from semiconductor_mcp.server import screen_entity

        with (
            patch("semiconductor_mcp.server._opensanctions.screen_entity", new_callable=AsyncMock) as mock_os,
            patch("semiconductor_mcp.server._bis_screening.screen_entity", new_callable=AsyncMock) as mock_bis,
        ):
            mock_os.side_effect = Exception("network error")
            mock_bis.return_value = {"risk": "CLEAR", "total": 0, "results": []}

            result = json.loads(await screen_entity("Corp"))

        assert result["aggregate_risk"] in ("UNKNOWN", "CLEAR")


# ---------------------------------------------------------------------------
# add_whitepaper
# ---------------------------------------------------------------------------

class TestAddWhitepaper:
    @pytest.mark.asyncio
    async def test_path_traversal_rejected(self, fresh_db):
        from semiconductor_mcp.server import add_whitepaper

        result = json.loads(await add_whitepaper("../../../etc/passwd"))
        assert "error" in result
        assert "whitepapers directory" in result["error"]

    @pytest.mark.asyncio
    async def test_nonexistent_file_rejected(self, fresh_db, tmp_path, monkeypatch):
        import semiconductor_mcp.config as cfg
        monkeypatch.setattr(cfg, "WHITEPAPER_DIR", tmp_path / "whitepapers")
        (tmp_path / "whitepapers").mkdir(exist_ok=True)

        from semiconductor_mcp.server import add_whitepaper

        result = json.loads(await add_whitepaper(str(tmp_path / "whitepapers" / "missing.pdf")))
        assert "error" in result

    @pytest.mark.asyncio
    async def test_non_pdf_rejected(self, fresh_db, tmp_path, monkeypatch):
        import semiconductor_mcp.server as srv
        wp_dir = tmp_path / "whitepapers"
        wp_dir.mkdir(exist_ok=True)
        # Patch the server module's own reference to WHITEPAPER_DIR
        monkeypatch.setattr(srv, "WHITEPAPER_DIR", wp_dir)

        txt_file = wp_dir / "notes.txt"
        txt_file.write_text("some text")

        result = json.loads(await srv.add_whitepaper(str(txt_file)))
        assert "error" in result
        assert "PDF" in result["error"]


# ---------------------------------------------------------------------------
# search_whitepapers / list_whitepapers
# ---------------------------------------------------------------------------

class TestSearchWhitepapers:
    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_papers(self, fresh_db):
        from semiconductor_mcp.server import search_whitepapers

        result = json.loads(await search_whitepapers("silicon wafer"))
        assert result == []

    @pytest.mark.asyncio
    async def test_list_whitepapers_returns_empty_when_none(self, fresh_db):
        from semiconductor_mcp.server import list_whitepapers

        result = json.loads(await list_whitepapers())
        assert result == []

    @pytest.mark.asyncio
    async def test_search_handles_fts_error_gracefully(self, fresh_db):
        """Malformed queries should return error JSON, not raise."""
        from semiconductor_mcp.server import search_whitepapers

        # This would crash unescaped FTS5 — our escaping should handle it
        result_raw = await search_whitepapers("AND OR NOT")
        result = json.loads(result_raw)
        assert isinstance(result, list)
