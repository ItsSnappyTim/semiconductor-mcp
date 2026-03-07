"""Unit tests for db.py — FTS triggers, upsert, id reliability."""

import sqlite3

from semiconductor_mcp.db import (
    _escape_fts5,
    insert_whitepaper,
    list_all,
    search_fts,
)


def _insert(fresh_db, filename="test.pdf", title="Test Paper", text="silicon wafer process"):
    return insert_whitepaper(
        filename=filename,
        title=title,
        page_count=5,
        file_path=str(fresh_db / "whitepapers" / filename),
        full_text=text,
    )


class TestInsertAndSearch:
    def test_insert_returns_id(self, fresh_db):
        row_id = _insert(fresh_db)
        assert isinstance(row_id, int)
        assert row_id > 0

    def test_inserted_paper_appears_in_fts(self, fresh_db):
        _insert(fresh_db, text="extreme ultraviolet lithography scanner")
        results = search_fts("ultraviolet lithography")
        assert len(results) == 1
        assert "Test Paper" in results[0]["title"]

    def test_insert_returns_consistent_id(self, fresh_db):
        """RETURNING id should give the same id on both insert and upsert paths."""
        id1 = _insert(fresh_db, filename="a.pdf")
        id2 = _insert(fresh_db, filename="a.pdf", text="updated text")
        assert id1 == id2

    def test_list_all_returns_all_papers(self, fresh_db):
        _insert(fresh_db, filename="a.pdf")
        _insert(fresh_db, filename="b.pdf")
        all_papers = list_all()
        filenames = [p["filename"] for p in all_papers]
        assert "a.pdf" in filenames
        assert "b.pdf" in filenames


class TestFTSSyncTriggers:
    def test_upsert_updates_fts_not_duplicates(self, fresh_db, monkeypatch):
        """Upserting should not leave stale FTS rows from the old text."""

        _insert(fresh_db, text="chemical mechanical polishing slurry")
        # Re-index with completely different text
        _insert(fresh_db, text="atomic layer deposition precursor")

        # Old text should NOT be findable
        old_results = search_fts("chemical mechanical polishing")
        assert len(old_results) == 0, "Stale FTS entry found after upsert"

        # New text SHOULD be findable
        new_results = search_fts("atomic layer deposition")
        assert len(new_results) == 1

    def test_fts_entry_removed_after_row_delete(self, fresh_db):
        """DELETE trigger should remove the FTS entry."""
        import semiconductor_mcp.db as db_mod

        _insert(fresh_db, filename="del.pdf", text="gallium nitride epitaxy")

        # Verify findable before delete
        assert len(search_fts("gallium nitride")) == 1

        # Delete the row directly via SQL
        conn = sqlite3.connect(str(db_mod.DB_PATH))
        conn.execute("DELETE FROM whitepapers WHERE filename = ?", ("del.pdf",))
        conn.commit()
        conn.close()

        # Should no longer be findable
        assert len(search_fts("gallium nitride")) == 0


class TestFTSSearch:
    def test_search_returns_excerpt(self, fresh_db):
        _insert(fresh_db, text="copper electrochemical deposition interconnect")
        results = search_fts("copper electrochemical")
        assert len(results) == 1
        assert "excerpt" in results[0]

    def test_search_ranked_by_relevance(self, fresh_db):
        _insert(fresh_db, filename="a.pdf", title="CMP Paper", text="silicon cmp polishing wafer")
        _insert(fresh_db, filename="b.pdf", title="EUV Paper", text="euv lithography scanner wavelength")
        results = search_fts("euv lithography")
        # EUV paper should rank first
        assert results[0]["title"] == "EUV Paper"

    def test_search_no_results(self, fresh_db):
        _insert(fresh_db, text="silicon wafer")
        results = search_fts("quantum computing")
        assert results == []

    def test_search_handles_fts5_special_chars(self, fresh_db):
        """FTS5 operators in query should not raise."""
        _insert(fresh_db, text="some content")
        # These would normally crash FTS5 if not escaped
        for q in ["AND OR NOT", "test*", '"phrase query"', "hyph-en"]:
            results = search_fts(q)
            assert isinstance(results, list)

    def test_max_results_respected(self, fresh_db):
        for i in range(5):
            _insert(fresh_db, filename=f"p{i}.pdf", text=f"semiconductor process step {i}")
        results = search_fts("semiconductor process", max_results=2)
        assert len(results) <= 2


class TestFTSEscape:
    def test_escapes_double_quotes(self):
        # Embedded quotes are stripped from tokens; each token is wrapped in quotes
        escaped = _escape_fts5('say "hello"')
        # "say" "hello" — embedded quote stripped from "hello", both tokens quoted
        assert escaped == '"say" "hello"'
        for token in escaped.split():
            assert token.startswith('"') and token.endswith('"')

    def test_empty_query(self):
        assert _escape_fts5("") == ""

    def test_single_token(self):
        result = _escape_fts5("semiconductor")
        assert "semiconductor" in result
