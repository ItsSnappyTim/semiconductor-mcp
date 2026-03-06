import asyncio
import hmac
import json
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from .config import (
    COMTRADE_API_KEY, ENABLE_EVAL, ITA_API_KEY,
    MCP_AUTH_TOKEN, PORT, WHITEPAPER_DIR, validate_config,
)
from .db import init_db, insert_whitepaper, list_all, search_fts
from .knowledge_base import search as _kb_search
from .pdf_utils import extract_pdf
from .sources import arxiv, newsapi, semantic_scholar
from .sources import bis_screening as _bis_screening
from .sources import comtrade as _comtrade
from .sources import edgar as _edgar
from .sources import gdelt as _gdelt
from .sources import opensanctions as _opensanctions

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
        if request.url.path != "/health":
            auth = request.headers.get("Authorization", "")
            expected = f"Bearer {MCP_AUTH_TOKEN}"
            if not hmac.compare_digest(auth, expected):
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
    max_results = max(1, min(max_results, 20))
    try:
        arxiv_results, ss_results = await asyncio.gather(
            arxiv.search(query, max_results),
            semantic_scholar.search(query, max_results),
        )
    except Exception as exc:
        return json.dumps({"error": f"Search failed: {exc}"})

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
    max_results = max(1, min(max_results, 20))
    try:
        results = await newsapi.search(query, max_results)
    except Exception as exc:
        return json.dumps({"error": f"News search failed: {exc}"})
    return json.dumps(results, ensure_ascii=False, indent=2)


@mcp.tool()
async def add_whitepaper(file_path: str) -> str:
    """Index a PDF whitepaper into the local FTS database.

    The file must already exist on the server (e.g. copied to the Railway
    volume at /data/whitepapers/). Provide the absolute server-side path.
    Re-indexing an existing filename updates the record.
    """
    # H-3: Confine to whitepapers directory to prevent path traversal
    try:
        path = Path(file_path).resolve()
        allowed = WHITEPAPER_DIR.resolve()
        path.relative_to(allowed)  # raises ValueError if outside allowed dir
    except ValueError:
        return json.dumps({"error": "File must be inside the whitepapers directory"})

    if not path.exists():
        return json.dumps({"error": "File not found"})
    if path.suffix.lower() != ".pdf":
        return json.dumps({"error": "Only PDF files are supported"})

    # M-5: Reject oversized PDFs (50 MB limit)
    if path.stat().st_size > 50 * 1024 * 1024:
        return json.dumps({"error": "File exceeds 50 MB size limit"})

    try:
        title, page_count, full_text = extract_pdf(path)
    except Exception as exc:
        return json.dumps({"error": f"Failed to extract PDF: {exc}"})

    # M-5: Truncate excessively long extracted text (2 M chars)
    if len(full_text) > 2_000_000:
        full_text = full_text[:2_000_000]

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
    max_results = max(1, min(max_results, 20))
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
# Supply chain intelligence tools
# ---------------------------------------------------------------------------

@mcp.tool()
async def lookup_fab_component(query: str) -> str:
    """Search the semiconductor fab process knowledge base.

    Accepts component names, material names, process step names, chemical
    symbols, or equipment names (e.g. "EUV", "gallium", "CMP", "HF",
    "lithography", "cobalt", "ALD", "neon").

    Returns:
      - Matching components with: availability classification, key global
        suppliers with market share, export control status and ECCN,
        grey market risk level and detail, process steps where used,
        geographic supply concentration, and critical mineral flag.
      - Matching process steps with their required component list.

    Availability classes: commodity | specialized | dual_source |
    single_source | export_controlled
    Grey market risk: low | medium | high | critical
    """
    results = _kb_search(query)

    # Enrich top high-risk components with live OpenSanctions supplier check
    enriched_components = []
    for comp in results.get("components", []):
        enriched = dict(comp)
        if comp.get("grey_market_risk") in ("high", "critical"):
            suppliers = comp.get("key_suppliers", [])
            if suppliers:
                top_supplier = suppliers[0].get("name", "")
                if top_supplier:
                    try:
                        screen = await _opensanctions.screen_entity(top_supplier)
                        enriched["supplier_sanctions_check"] = {
                            "screened_entity": top_supplier,
                            "risk": screen.get("risk"),
                            "matches": len(screen.get("matches", [])),
                        }
                    except Exception:
                        pass
        enriched_components.append(enriched)

    results["components"] = enriched_components
    return json.dumps(results, ensure_ascii=False, indent=2)


@mcp.tool()
async def get_supply_chain_status(component: str) -> str:
    """Get live supply chain status for a semiconductor component or material.

    Combines:
    - Knowledge base risk data (availability, suppliers, geographic concentration)
    - UN Comtrade annual trade flow data (if COMTRADE_API_KEY is configured)
    - GDELT news signals from the past 90 days (always available)

    Use to assess current availability, geographic concentration, and
    recent disruption events for a specific component.
    """
    kb = _kb_search(component)
    top_comp = kb["components"][0] if kb["components"] else None

    # Determine HS codes to query
    hs_codes = top_comp.get("hs_codes", []) if top_comp else []

    async def _no_trade() -> dict:
        return {"note": "No HS code available for this component"}

    # Run trade flow + GDELT concurrently
    trade_coro = (
        _comtrade.get_trade_flow(hs_codes[0], COMTRADE_API_KEY)
        if hs_codes
        else _no_trade()
    )
    gdelt_coro = _gdelt.search_supply_chain_news(component, days=90)

    trade_data, news_signals = await asyncio.gather(
        trade_coro, gdelt_coro, return_exceptions=True
    )

    if isinstance(trade_data, Exception):
        trade_data = {"error": str(trade_data)}
    if isinstance(news_signals, Exception):
        news_signals = []

    result = {
        "component": component,
        "knowledge_base": {
            "name": top_comp.get("name") if top_comp else None,
            "availability": top_comp.get("availability") if top_comp else None,
            "geographic_concentration": top_comp.get("geographic_concentration") if top_comp else None,
            "supply_risks": top_comp.get("supply_risks", []) if top_comp else [],
            "key_suppliers": top_comp.get("key_suppliers", []) if top_comp else [],
            "critical_mineral": top_comp.get("critical_mineral") if top_comp else None,
        },
        "trade_flow": trade_data,
        "news_signals": news_signals[:10],
        "news_signal_count": len(news_signals) if isinstance(news_signals, list) else 0,
    }
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
async def screen_entity(entity_name: str, country: str = "") -> str:
    """Screen a company or individual against global sanctions and export control lists.

    Checks two sources concurrently:
    1. OpenSanctions (always available, free): 100+ lists including OFAC SDN,
       EU Consolidated, UN Security Council, UK Sanctions, and national lists.
    2. ITA Consolidated Screening List (requires ITA_API_KEY): BIS Entity List,
       BIS Denied Persons List, BIS Unverified List, OFAC SDN/non-SDN, and
       State Department AECA Debarred list.

    Risk levels:
      CLEAR   — no matches on any list
      FLAGGED — matched on a watch/unverified list; proceed with caution
      BLOCKED — matched on a prohibited list (Entity List, SDN, etc.)
      UNKNOWN — API error; manual check recommended

    Use before engaging any unfamiliar supplier, especially for controlled
    semiconductor equipment, materials, or technology.
    """
    opensanctions_future = _opensanctions.screen_entity(entity_name)
    bis_future = _bis_screening.screen_entity(entity_name, ITA_API_KEY)

    os_result, bis_result = await asyncio.gather(
        opensanctions_future, bis_future, return_exceptions=True
    )

    if isinstance(os_result, Exception):
        os_result = {"risk": "UNKNOWN", "error": str(os_result), "total": 0}
    if isinstance(bis_result, Exception):
        bis_result = {"risk": "UNKNOWN", "error": str(bis_result), "total": 0}

    # Aggregate risk: take the worst
    risk_order = {"BLOCKED": 3, "FLAGGED": 2, "CLEAR": 1, "UNKNOWN": 0}
    os_risk = os_result.get("risk", "UNKNOWN")
    bis_risk = bis_result.get("risk", "UNKNOWN")
    aggregate_risk = max(os_risk, bis_risk, key=lambda r: risk_order.get(r, 0))

    result = {
        "entity": entity_name,
        "country": country or None,
        "aggregate_risk": aggregate_risk,
        "opensanctions": os_result,
        "ita_consolidated": bis_result,
        "recommendation": {
            "BLOCKED": "Do NOT proceed. Entity is on a prohibited list.",
            "FLAGGED": "Proceed with extreme caution. Conduct enhanced due diligence and obtain legal counsel before transacting.",
            "CLEAR": "No matches found. Standard due diligence still recommended.",
            "UNKNOWN": "API check failed. Perform manual checks at opensanctions.org and trade.gov before proceeding.",
        }.get(aggregate_risk, "Unable to determine risk."),
    }
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
async def get_grey_market_signals(query: str) -> str:
    """Search for grey market, smuggling, and sanctions evasion signals.

    Searches GDELT for recent news (past 180 days) about:
    smuggling, grey market, sanctions evasion, export control violations,
    counterfeit goods, and diversion activity related to the query term.

    Also runs a targeted NewsAPI search for enforcement and compliance angles.

    Use to assess whether a component or company is associated with known
    grey market activity, criminal networks, or sanctions circumvention.
    """
    grey_future = _gdelt.search_grey_market_signals(query, days=180)
    news_future = newsapi.search(
        f"{query} semiconductor export control enforcement sanctions", max_results=5
    )

    gdelt_results, news_results = await asyncio.gather(
        grey_future, news_future, return_exceptions=True
    )

    if isinstance(gdelt_results, Exception):
        gdelt_results = [{"error": str(gdelt_results)}]
    if isinstance(news_results, Exception):
        news_results = []

    # Assess signal strength
    signal_count = len(gdelt_results) if isinstance(gdelt_results, list) else 0
    signal_strength = (
        "HIGH" if signal_count >= 8
        else "MEDIUM" if signal_count >= 3
        else "LOW" if signal_count >= 1
        else "NONE"
    )

    result = {
        "query": query,
        "signal_strength": signal_strength,
        "gdelt_articles": gdelt_results,
        "news_articles": news_results,
        "interpretation": {
            "HIGH": "Significant recent news activity around grey market/enforcement for this topic.",
            "MEDIUM": "Some recent signals; warrants monitoring and due diligence.",
            "LOW": "Limited signals; may reflect recent events or emerging concern.",
            "NONE": "No recent grey market signals found in news sources.",
        }.get(signal_strength, ""),
    }
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
async def search_company_filings(company: str, topic: str = "supply chain") -> str:
    """Search SEC EDGAR 10-K and 10-Q filings for supply chain risk disclosures.

    Major semiconductor equipment and materials companies (ASML, Applied Materials,
    Lam Research, KLA, Tokyo Electron, Shin-Etsu, Air Products, Entegris, etc.)
    are legally required to disclose single-source dependencies, geographic
    concentration risks, export control impacts, and supply chain disruptions
    in their SEC filings.

    Examples:
      search_company_filings("ASML", "single source")
      search_company_filings("Lam Research", "China export control")
      search_company_filings("Entegris", "supply chain risk")
      search_company_filings("Air Products", "neon")

    Returns filing excerpts with company name, form type, filing date, and URL.
    """
    try:
        results = await _edgar.search_filings(company, topic)
    except Exception as exc:
        return json.dumps({"error": f"EDGAR search failed: {exc}"})
    return json.dumps(results, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Optional: RAGAS-inspired evaluation tool
# ---------------------------------------------------------------------------

if ENABLE_EVAL:
    from .evaluator import (
        draft_answer as _draft_answer,
        evaluate_response as _evaluate_response,
        extract_entities as _extract_entities,
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

        IMPORTANT: After presenting the answer to the user, you MUST always display:

        1. Sources consulted — list each source from the sources array as:
             • [title] (year if academic, date if news) — url

        2. Confidence scores from the evaluation field:
             • Composite: <composite_score>
             • Faithfulness: <faithfulness.score>  (claims supported by sources?)
             • Answer relevancy: <answer_relevancy.score>  (answers the question?)
             • Context utilization: <context_utilization.score>  (grounded in sources?)

        Always show both sections — they tell the user where the information came
        from and how much to trust it.
        """
        from .sources import arxiv, semantic_scholar, newsapi

        threshold = max(0.0, min(threshold, 1.0))
        max_attempts = max(1, min(max_attempts, 5))

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

    @mcp.tool()
    async def research_and_verify_supply_chain(
        question: str,
        threshold: float = 0.9,
        max_attempts: int = 3,
    ) -> str:
        """Research a semiconductor supply chain question and return a verified answer.

        Unlike research_and_verify (which searches academic papers and news),
        this tool draws context exclusively from supply chain intelligence sources:
          - Semiconductor fab knowledge base (components, suppliers, export controls)
          - UN Comtrade annual trade flow data (when HS codes are available)
          - GDELT supply chain news signals (past 90 days)
          - GDELT grey market / smuggling signals (past 180 days)
          - NewsAPI semiconductor enforcement and compliance news
          - SEC EDGAR 10-K/10-Q supply chain risk disclosures (for named companies)
          - OpenSanctions entity screening (for named companies)

        Runs the same verify loop as research_and_verify:
          1. Extract search keywords and any named entities from the question
          2. Gather context from all supply chain sources concurrently
          3. Draft a context-grounded answer
          4. Evaluate faithfulness, answer relevancy, and context utilization
          5. If composite score < threshold, refine query and retry
          6. Return when score >= threshold or attempts exhausted

        Use this for questions about: component availability, supplier concentration,
        export controls, grey market risk, sanctions exposure, or trade flow analysis.

        IMPORTANT: After presenting the answer to the user, always display:

        1. Sources consulted — list each source as:
             • [title] (type) — url

        2. Confidence scores from the evaluation field:
             • Composite: <composite_score>
             • Faithfulness: <faithfulness.score>
             • Answer relevancy: <answer_relevancy.score>
             • Context utilization: <context_utilization.score>
        """
        threshold = max(0.0, min(threshold, 1.0))
        max_attempts = max(1, min(max_attempts, 5))

        best: dict[str, Any] = {}
        best_score: float = -1.0

        async with _httpx.AsyncClient(timeout=60) as client:
            # Extract search keywords and named entities concurrently
            query, entities = await asyncio.gather(
                _question_to_query(client, question),
                _extract_entities(client, question),
            )

            # Knowledge base context is stable — compute once before the retry loop
            kb_result = _kb_search(query)
            top_comp = kb_result["components"][0] if kb_result.get("components") else None
            hs_codes = top_comp.get("hs_codes", []) if top_comp else []

            kb_contexts: list[str] = []
            kb_sources: list[dict[str, Any]] = []
            for comp in kb_result.get("components", [])[:3]:
                suppliers = ", ".join(
                    f"{s['name']} ({s['country']})"
                    for s in comp.get("key_suppliers", [])[:3]
                )
                text = (
                    f"Component: {comp['name']}. "
                    f"Availability: {comp.get('availability', 'unknown')}. "
                    f"Geographic concentration: {comp.get('geographic_concentration', 'unknown')}. "
                    f"Supply risks: {'; '.join(comp.get('supply_risks', []))}. "
                    f"Key suppliers: {suppliers}. "
                    f"Export controls: {comp.get('export_controls', {}).get('detail', 'none')}. "
                    f"Grey market risk: {comp.get('grey_market_risk', 'unknown')} — "
                    f"{comp.get('grey_market_detail', '')}."
                )
                kb_contexts.append(text)
                kb_sources.append({"type": "knowledge_base", "title": comp["name"], "url": ""})
            for step in kb_result.get("process_steps", [])[:2]:
                text = (
                    f"Process step: {step['name']}. "
                    f"{step.get('description', '')} "
                    f"Required components: {', '.join(step.get('component_ids', []))}."
                )
                kb_contexts.append(text)
                kb_sources.append({"type": "knowledge_base", "title": step["name"], "url": ""})

            # Comtrade is also stable (annual data) — fetch once if we have an HS code
            trade_context: list[str] = []
            trade_sources: list[dict[str, Any]] = []
            if hs_codes and COMTRADE_API_KEY:
                try:
                    trade_data = await _comtrade.get_trade_flow(hs_codes[0], COMTRADE_API_KEY)
                    if isinstance(trade_data, dict) and trade_data.get("top_exporters"):
                        exporters_str = ", ".join(
                            f"{e['country']} ({e['share_pct']}%)"
                            for e in trade_data["top_exporters"][:5]
                        )
                        trade_context.append(
                            f"UN Comtrade trade flow for HS {trade_data['hs_code']} "
                            f"({trade_data.get('year', 'N/A')}): "
                            f"top exporters are {exporters_str}. "
                            f"Total exports: USD {trade_data.get('total_exports_usd', 0):,}."
                        )
                        trade_sources.append({
                            "type": "comtrade",
                            "title": f"Comtrade HS {trade_data['hs_code']}",
                            "url": "https://comtradeplus.un.org/",
                        })
                except Exception:
                    pass

            for attempt in range(1, max_attempts + 1):
                contexts = kb_contexts + trade_context
                sources = kb_sources + trade_sources

                # Gather dynamic sources concurrently
                gdelt_sc_coro = _gdelt.search_supply_chain_news(query, days=90)
                gdelt_gm_coro = _gdelt.search_grey_market_signals(query, days=180)
                news_coro = newsapi.search(
                    f"{query} semiconductor supply chain", max_results=5
                )
                dynamic_results = await asyncio.gather(
                    gdelt_sc_coro, gdelt_gm_coro, news_coro,
                    return_exceptions=True,
                )

                gdelt_sc = dynamic_results[0] if not isinstance(dynamic_results[0], Exception) else []
                gdelt_gm = dynamic_results[1] if not isinstance(dynamic_results[1], Exception) else []
                news_res = dynamic_results[2] if not isinstance(dynamic_results[2], Exception) else []

                for article in (gdelt_sc or [])[:6]:
                    if article.get("title"):
                        contexts.append(
                            f"Supply chain news: {article['title']}. "
                            f"Source: {article.get('domain', '')}. "
                            f"Date: {str(article.get('seendate', ''))[:10]}."
                        )
                        sources.append({
                            "type": "gdelt",
                            "title": article["title"],
                            "url": article.get("url", ""),
                        })

                for article in (gdelt_gm or [])[:4]:
                    if article.get("title"):
                        contexts.append(
                            f"Grey market/enforcement signal: {article['title']}. "
                            f"Source: {article.get('domain', '')}. "
                            f"Date: {str(article.get('seendate', ''))[:10]}."
                        )
                        sources.append({
                            "type": "gdelt_grey_market",
                            "title": article["title"],
                            "url": article.get("url", ""),
                        })

                for r in (news_res or [])[:4]:
                    if r.get("description"):
                        contexts.append(f"{r['title']}: {r['description']}")
                        sources.append({
                            "type": "news",
                            "title": r["title"],
                            "url": r.get("url", ""),
                            "published_at": r.get("published_at", ""),
                        })

                # Entity-specific: EDGAR + sanctions (gather all at once)
                if entities:
                    entity_coros: list = []
                    for entity in entities[:2]:
                        entity_coros.append(_edgar.search_filings(entity, query[:50]))
                        entity_coros.append(_opensanctions.screen_entity(entity))
                    entity_raw = await asyncio.gather(*entity_coros, return_exceptions=True)

                    for i, entity in enumerate(entities[:2]):
                        edgar_res = entity_raw[i * 2]
                        sanc_res = entity_raw[i * 2 + 1]

                        if not isinstance(edgar_res, Exception) and isinstance(edgar_res, list):
                            for filing in edgar_res[:2]:
                                excerpt = filing.get("excerpt", "")
                                if excerpt:
                                    contexts.append(
                                        f"{filing.get('company_name', entity)} "
                                        f"{filing.get('form_type', 'filing')} "
                                        f"({str(filing.get('filed_at', ''))[:10]}): "
                                        f"{excerpt[:500]}"
                                    )
                                    sources.append({
                                        "type": "edgar",
                                        "title": f"{entity} {filing.get('form_type', 'SEC Filing')}",
                                        "url": filing.get("file_url", ""),
                                    })

                        if not isinstance(sanc_res, Exception) and isinstance(sanc_res, dict):
                            if sanc_res.get("total", 0) > 0:
                                lists = list({
                                    m.get("dataset", "")
                                    for m in sanc_res.get("matches", [])[:5]
                                    if m.get("dataset")
                                })
                                contexts.append(
                                    f"Sanctions check for {entity}: "
                                    f"risk={sanc_res.get('risk', 'UNKNOWN')}, "
                                    f"{sanc_res['total']} match(es) on lists including: "
                                    f"{', '.join(lists[:5])}."
                                )
                                sources.append({
                                    "type": "opensanctions",
                                    "title": f"{entity} sanctions check",
                                    "url": f"https://www.opensanctions.org/search/?q={entity}",
                                })

                if not contexts:
                    if not best:
                        best = {"error": f"No supply chain context retrieved for: {query!r}"}
                    break

                answer = await _draft_answer(client, question, contexts)
                eval_result = await _eval_with_client(client, question, contexts, answer)
                composite = eval_result.get("composite_score") or 0.0

                if composite > best_score:
                    best_score = composite
                    best = {
                        "answer": answer,
                        "sources": sources,
                        "evaluation": eval_result,
                        "query_used": query,
                        "entities_extracted": entities,
                        "attempt": attempt,
                        "threshold_met": composite >= threshold,
                    }

                if composite >= threshold:
                    break

                if attempt < max_attempts:
                    low_metric = min(
                        ("faithfulness", eval_result["metrics"]["faithfulness"].get("score") or 0),
                        ("answer_relevancy", eval_result["metrics"]["answer_relevancy"].get("score") or 0),
                        ("context_utilization", eval_result["metrics"]["context_utilization"].get("score") or 0),
                        key=lambda x: x[1],
                    )
                    issue = (
                        f"{low_metric[0]} score was {low_metric[1]:.2f} — "
                        "need more specific supply chain data"
                    )
                    query = await _refine_query(client, question, query, issue)

        if not best:
            best = {"error": "All attempts failed to retrieve supply chain context"}

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
