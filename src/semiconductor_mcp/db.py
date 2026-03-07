import sqlite3
from datetime import UTC, datetime
from typing import Any

from .config import DB_PATH


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS whitepapers (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                filename  TEXT    NOT NULL UNIQUE,
                title     TEXT    NOT NULL,
                added_at  TEXT    NOT NULL,
                page_count INTEGER NOT NULL,
                file_path TEXT    NOT NULL,
                full_text TEXT    NOT NULL
            );

            CREATE VIRTUAL TABLE IF NOT EXISTS whitepapers_fts
                USING fts5(title, full_text, content='whitepapers', content_rowid='id');

            CREATE TRIGGER IF NOT EXISTS whitepapers_ai
                AFTER INSERT ON whitepapers BEGIN
                    INSERT INTO whitepapers_fts(rowid, title, full_text)
                    VALUES (new.id, new.title, new.full_text);
                END;

            CREATE TRIGGER IF NOT EXISTS whitepapers_au
                AFTER UPDATE ON whitepapers BEGIN
                    INSERT INTO whitepapers_fts(whitepapers_fts, rowid, title, full_text)
                    VALUES ('delete', old.id, old.title, old.full_text);
                    INSERT INTO whitepapers_fts(rowid, title, full_text)
                    VALUES (new.id, new.title, new.full_text);
                END;

            CREATE TRIGGER IF NOT EXISTS whitepapers_ad
                AFTER DELETE ON whitepapers BEGIN
                    INSERT INTO whitepapers_fts(whitepapers_fts, rowid, title, full_text)
                    VALUES ('delete', old.id, old.title, old.full_text);
                END;
        """)


def insert_whitepaper(
    filename: str, title: str, page_count: int, file_path: str, full_text: str
) -> int:
    added_at = datetime.now(UTC).isoformat()
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO whitepapers (filename, title, added_at, page_count, file_path, full_text)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(filename) DO UPDATE SET
                title      = excluded.title,
                added_at   = excluded.added_at,
                page_count = excluded.page_count,
                file_path  = excluded.file_path,
                full_text  = excluded.full_text
            RETURNING id
            """,
            (filename, title, added_at, page_count, file_path, full_text),
        )
        return cur.fetchone()[0]


def _escape_fts5(query: str) -> str:
    """Escape FTS5 special characters to prevent syntax errors or query injection."""
    # Wrap each whitespace-separated token in double quotes so FTS5 treats
    # them as literal phrases rather than operators.
    tokens = query.strip().split()
    return " ".join(f'"{t.replace(chr(34), "")}"' for t in tokens if t)


def search_fts(query: str, max_results: int = 5) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT w.id, w.filename, w.title, w.added_at, w.page_count,
                   snippet(whitepapers_fts, 1, '[', ']', '...', 20) AS excerpt
            FROM whitepapers_fts
            JOIN whitepapers w ON w.id = whitepapers_fts.rowid
            WHERE whitepapers_fts MATCH ?
            ORDER BY rank
            LIMIT ?
            """,
            (_escape_fts5(query), max_results),
        ).fetchall()
    return [dict(row) for row in rows]


def list_all() -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, filename, title, added_at, page_count FROM whitepapers ORDER BY added_at DESC"
        ).fetchall()
    return [dict(row) for row in rows]
