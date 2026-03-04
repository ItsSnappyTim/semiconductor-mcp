import asyncio
import json
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from .config import ENABLE_EVAL, MCP_AUTH_TOKEN, PORT, WHITEPAPER_DIR, validate_config
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
# Optional: RAGAS-inspired evaluation tool
# ---------------------------------------------------------------------------

if ENABLE_EVAL:
    from .evaluator import (
        draft_answer as _draft_answer,
        evaluate_response as _evaluate_response,
        question_to_query as _question_to_query,
        refine_query as _refine_query,
        _eval_with_client,
    )
    import httpx as _httpx

    @mcp.tool()
    async def evaluate_response(question: str, contexts: list[str], answer: str) -> str:
        """Evaluate a generated answer using RAGAS-inspired metrics.

        Use this after generating an answer with search_academic or search_news
        to score the quality of the response.

        - question: the original user question
        - contexts: list of retrieved text passages used to generate the answer
          (e.g. paper abstracts, news descriptions from previous tool calls)
        - answer: the answer text to evaluate

        Returns JSON with three scores (0.0–1.0):
          faithfulness        — are the answer's claims supported by the contexts?
          answer_relevancy    — does the answer actually address the question?
          context_utilization — did the answer draw from contexts vs general knowledge?
        Plus a composite_score (mean of the three) and per-claim verdict details.
        """
        return await _evaluate_response(question, contexts, answer)

    @mcp.tool()
    async def research_and_verify(
        question: str,
        threshold: float = 0.9,
        max_attempts: int = 3,
    ) -> str:
        """Research a semiconductor question and return a verified, high-quality answer.

        Unlike search_academic or search_news, this tool runs a full loop:
          1. Search arXiv, Semantic Scholar, and NewsAPI concurrently
          2. Draft a context-grounded answer using retrieved sources
          3. Evaluate faithfulness, answer relevancy, and context utilization
          4. If composite score < threshold, refine the query and retry
          5. Return only when score >= threshold or attempts are exhausted

        Use this when you need a guaranteed high-confidence answer, not just
        raw search results.

        - question: the semiconductor question to research
        - threshold: minimum composite score to accept (default 0.9)
        - max_attempts: maximum search-draft-evaluate cycles (default 3)

        IMPORTANT: After presenting the answer to the user, you MUST always
        display the confidence ratings from the evaluation field, formatted as:

          Confidence scores:
          • Composite: <composite_score>
          • Faithfulness: <faithfulness.score>  (are claims supported by sources?)
          • Answer relevancy: <answer_relevancy.score>  (does answer address the question?)
          • Context utilization: <context_utilization.score>  (grounded in retrieved sources?)

        Always show these scores — they tell the user how much to trust the answer.
        """
        from .sources import arxiv, semantic_scholar, newsapi

        best: dict[str, Any] = {}
        best_score: float = -1.0

        async with _httpx.AsyncClient(timeout=45) as client:
            # Convert natural language question to search-friendly keywords
            query = await _question_to_query(client, question)

            for attempt in range(1, max_attempts + 1):

                # 1. Search all sources concurrently
                arxiv_results, ss_results, news_results = await asyncio.gather(
                    arxiv.search(query, max_results=5),
                    semantic_scholar.search(query, max_results=5),
                    newsapi.search(query, max_results=5),
                )

                # 2. Deduplicate academic results by DOI, build context list
                seen_dois: set[str] = set()
                academic: list[dict[str, Any]] = []
                for r in ss_results + arxiv_results:
                    doi = r.get("doi")
                    if doi:
                        if doi in seen_dois:
                            continue
                        seen_dois.add(doi)
                    academic.append(r)

                contexts = []
                sources = []
                for r in academic[:6]:
                    if r.get("abstract"):
                        contexts.append(f"{r['title']}: {r['abstract']}")
                        sources.append({"type": "academic", "title": r["title"], "url": r.get("url", ""), "year": r.get("year", "")})
                for r in news_results[:4]:
                    if r.get("description"):
                        contexts.append(f"{r['title']}: {r['description']}")
                        sources.append({"type": "news", "title": r["title"], "url": r.get("url", ""), "published_at": r.get("published_at", "")})

                if not contexts:
                    if not best:
                        best = {"error": f"No results found for query: {query!r}"}
                    break

                # 3. Draft answer grounded in retrieved contexts
                answer = await _draft_answer(client, question, contexts)

                # 4. Evaluate
                eval_result = await _eval_with_client(client, question, contexts, answer)
                composite = eval_result.get("composite_score") or 0.0

                if composite > best_score:
                    best_score = composite
                    best = {
                        "answer": answer,
                        "sources": sources,
                        "evaluation": eval_result,
                        "query_used": query,
                        "attempt": attempt,
                        "threshold_met": composite >= threshold,
                    }

                if composite >= threshold:
                    break

                # 5. Refine query for next attempt
                if attempt < max_attempts:
                    low_metric = min(
                        ("faithfulness", eval_result["metrics"]["faithfulness"].get("score") or 0),
                        ("answer_relevancy", eval_result["metrics"]["answer_relevancy"].get("score") or 0),
                        ("context_utilization", eval_result["metrics"]["context_utilization"].get("score") or 0),
                        key=lambda x: x[1],
                    )
                    issue = f"{low_metric[0]} score was {low_metric[1]:.2f} — need more specific/relevant sources"
                    query = await _refine_query(client, question, query, issue)

        if not best:
            best = {"error": "All attempts failed to retrieve results"}

        return json.dumps(best, ensure_ascii=False, indent=2)


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
