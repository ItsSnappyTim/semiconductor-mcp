import asyncio
import json
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from .config import MCP_AUTH_TOKEN, PORT, WHITEPAPER_DIR, validate_config
from .db import init_db, insert_whitepaper, list_all, search_fts
from .pdf_utils import extract_pdf
from .sources import arxiv, newsapi, semantic_scholar

# Validate required config at startup
validate_config()

# Ensure whitepaper directory exists
WHITEPAPER_DIR.mkdir(parents=True, exist_ok=True)

# Initialize SQLite FTS database
init_db()

# DNS rebinding protection is disabled because Bearer token auth is the security layer.
# The default allowed_hosts=["localhost", "127.0.0.1"] would block Railway's public hostname.
mcp = FastMCP(
    "semiconductor-expert",
    transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
)


# ---------------------------------------------------------------------------
# Auth middleware
# ---------------------------------------------------------------------------

class BearerAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Any) -> Response:
        if MCP_AUTH_TOKEN and request.url.path != "/health":
            auth = request.headers.get("Authorization", "")
            if auth != f"Bearer {MCP_AUTH_TOKEN}":
                return Response("Unauthorized", status_code=401)
        return await call_next(request)


# ---------------------------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------------------------

@mcp.custom_route("/health", methods=["GET"])
async def health(_: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool()
async def search_academic(query: str, max_results: int = 5) -> str:
    """Search arXiv and Semantic Scholar for academic papers on a topic.

    Returns deduplicated results ranked by source. Use for fact-checking
    technical claims about semiconductor processes, materials, and equipment.
    """
    arxiv_results, ss_results = await asyncio.gather(
        arxiv.search(query, max_results),
        semantic_scholar.search(query, max_results),
    )

    # Deduplicate by DOI (prefer Semantic Scholar entry which has citation count)
    seen_dois: set[str] = set()
    combined: list[dict[str, Any]] = []

    for result in ss_results + arxiv_results:
        doi = result.get("doi")
        if doi:
            if doi in seen_dois:
                continue
            seen_dois.add(doi)
        combined.append(result)

    return json.dumps(combined[:max_results * 2], ensure_ascii=False, indent=2)


@mcp.tool()
async def search_news(query: str, max_results: int = 5) -> str:
    """Search recent semiconductor industry news via NewsAPI.

    Use for tracking current events: fab announcements, equipment orders,
    technology roadmap updates, company earnings, and supply chain news.
    """
    results = await newsapi.search(query, max_results)
    return json.dumps(results, ensure_ascii=False, indent=2)


@mcp.tool()
async def add_whitepaper(file_path: str) -> str:
    """Index a PDF whitepaper into the local FTS database.

    The file must already exist on the server (e.g. copied to the Railway
    volume at /data/whitepapers/). Provide the absolute server-side path.
    Re-indexing an existing filename updates the record.
    """
    path = Path(file_path)
    if not path.exists():
        return json.dumps({"error": f"File not found: {file_path}"})
    if path.suffix.lower() != ".pdf":
        return json.dumps({"error": "Only PDF files are supported"})

    try:
        title, page_count, full_text = extract_pdf(path)
    except Exception as exc:
        return json.dumps({"error": f"Failed to extract PDF: {exc}"})

    row_id = insert_whitepaper(
        filename=path.name,
        title=title,
        page_count=page_count,
        file_path=str(path),
        full_text=full_text,
    )
    return json.dumps(
        {
            "status": "indexed",
            "id": row_id,
            "filename": path.name,
            "title": title,
            "page_count": page_count,
        }
    )


@mcp.tool()
async def search_whitepapers(query: str, max_results: int = 5) -> str:
    """Full-text search across all indexed whitepapers using SQLite FTS5.

    Returns matching documents with highlighted excerpt snippets showing
    where the query terms appear in the text.
    """
    try:
        results = search_fts(query, max_results)
    except Exception as exc:
        return json.dumps({"error": f"Search failed: {exc}"})
    return json.dumps(results, ensure_ascii=False, indent=2)


@mcp.tool()
async def list_whitepapers() -> str:
    """List all whitepapers currently indexed in the database.

    Returns filename, title, date added, and page count for each document.
    """
    results = list_all()
    return json.dumps(results, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    app = mcp.streamable_http_app()
    app.add_middleware(BearerAuthMiddleware)

    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)


if __name__ == "__main__":
    main()
