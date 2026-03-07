"""Shared pytest fixtures and startup configuration.

Environment variables must be set before any semiconductor_mcp modules are
imported (config.py reads them at import time). Setting them here at module
level ensures they are in place before pytest begins collecting tests.
"""

import os

import pytest

# Required by config.validate_config() — must be set before any module import
os.environ.setdefault("NEWSAPI_KEY", "test-newsapi-key")
os.environ.setdefault("MCP_AUTH_TOKEN", "test-mcp-token")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-anthropic-key")
os.environ.setdefault("ENABLE_EVAL", "1")


@pytest.fixture(autouse=True)
def reset_http_client():
    """Discard the shared HTTP client before each test so respx.mock patches
    a fresh client created within the test's respx context.
    """
    from semiconductor_mcp.http_client import reset_client

    reset_client()
    yield
    reset_client()


@pytest.fixture
def fresh_db(tmp_path, monkeypatch):
    """Provide an isolated SQLite database for each test.

    Patches DB_PATH and WHITEPAPER_DIR in both config and db modules so that
    all database operations within the test hit the temp path.
    """
    import semiconductor_mcp.config as cfg
    import semiconductor_mcp.db as db_mod

    test_db = tmp_path / "test.db"
    test_wp = tmp_path / "whitepapers"
    test_wp.mkdir()

    monkeypatch.setattr(cfg, "DB_PATH", test_db)
    monkeypatch.setattr(cfg, "WHITEPAPER_DIR", test_wp)
    monkeypatch.setattr(db_mod, "DB_PATH", test_db)

    from semiconductor_mcp.db import init_db

    init_db()
    return tmp_path
