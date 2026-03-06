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
    COMTRADE_API_KEY, ENABLE_EVAL, ITA_API_KEY, OPENSANCTIONS_API_KEY,
    MCP_AUTH_TOKEN, PORT, WHITEPAPER_DIR, validate_config,
)
from .db import init_db, insert_whitepaper, list_all, search_fts
from .knowledge_base import search as _kb_search
from .pdf_utils import extract_pdf
from .sources import arxiv, newsapi, semantic_scholar
from .sources import bis_screening as _bis_screening
from .sources import comtrade as _comtrade
from .sources import edgar as _edgar
from .sources import federal_register as _federal_register
from .sources import gdelt as _gdelt
from .sources import opensanctions as _opensanctions
from .sources import pubchem as _pubchem
from .sources import world_bank as _world_bank

# Validate required config at startup
validate_config()


def _truncate(value: str, max_len: int) -> str:
    """Silently truncate a string input to prevent excessively long API queries."""
    return value[:max_len] if len(value) > max_len else value

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
        title, page_count, full_text = await asyncio.wait_for(
            asyncio.to_thread(extract_pdf, path),
            timeout=60.0,
        )
    except asyncio.TimeoutError:
        return json.dumps({"error": "PDF extraction timed out (>60s)"})
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
    query = _truncate(query, 500)
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
# Compliance screening
# ---------------------------------------------------------------------------

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
    entity_name = _truncate(entity_name, 200)
    country = _truncate(country, 100)
    opensanctions_future = _opensanctions.screen_entity(entity_name, OPENSANCTIONS_API_KEY)
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
        this tool draws context from all available supply chain intelligence sources:
          - Semiconductor fab knowledge base (components, suppliers, export controls)
          - UN Comtrade annual trade flow data (when HS codes are available)
          - GDELT supply chain news signals (past 90 days)
          - GDELT grey market / smuggling signals (past 180 days)
          - Federal Register BIS/OFAC regulatory documents (past 12 months)
          - PubChem chemical properties and GHS safety data (for process chemicals)
          - Commodity price data for metals (copper, gold, palladium, etc.)
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

            # Fetch GDELT once before the retry loop — news doesn't change
            # between attempts, and re-fetching would burn rate limit quota.
            # The lock in gdelt.py serialises these two sequential calls.
            gdelt_sc = await _gdelt.search_supply_chain_news(query, days=90)
            if not isinstance(gdelt_sc, list):
                gdelt_sc = []
            gdelt_gm = await _gdelt.search_grey_market_signals(query, days=180)
            if not isinstance(gdelt_gm, list):
                gdelt_gm = []

            gdelt_contexts: list[str] = []
            gdelt_sources: list[dict[str, Any]] = []
            for article in gdelt_sc[:6]:
                if article.get("title"):
                    gdelt_contexts.append(
                        f"Supply chain news: {article['title']}. "
                        f"Source: {article.get('domain', '')}. "
                        f"Date: {str(article.get('date', ''))[:10]}."
                    )
                    gdelt_sources.append({
                        "type": "gdelt",
                        "title": article["title"],
                        "url": article.get("url", ""),
                    })
            for article in gdelt_gm[:4]:
                if article.get("title"):
                    gdelt_contexts.append(
                        f"Grey market/enforcement signal: {article['title']}. "
                        f"Source: {article.get('domain', '')}. "
                        f"Date: {str(article.get('date', ''))[:10]}."
                    )
                    gdelt_sources.append({
                        "type": "gdelt_grey_market",
                        "title": article["title"],
                        "url": article.get("url", ""),
                    })

            # ---------------------------------------------------------------
            # Federal Register, PubChem, and commodity prices are all stable
            # (regulations and prices don't change between retry attempts).
            # Fetch all three concurrently once, then join to context.
            # ---------------------------------------------------------------

            # --- Federal Register: BIS/OFAC regulatory docs (past 12 months) ---
            async def _fetch_fedreg() -> list[dict[str, Any]]:
                try:
                    docs = await _federal_register.search_export_controls(query, days=365)
                    return docs if isinstance(docs, list) else []
                except Exception:
                    return []

            # --- PubChem: chemical safety for any chemical KB components found ---
            _CHEM_CATEGORIES = {"wet_chemistry", "cvd_precursor"}
            _CHEM_KEYWORDS = {"acid", "gas", "oxide", "fluoride", "chloride", "silane",
                               "precursor", "developer", "solvent", "etchant"}

            chem_names: list[str] = []
            for comp in kb_result.get("components", [])[:5]:
                cat = comp.get("category", "")
                name_lower = comp.get("name", "").lower()
                if cat in _CHEM_CATEGORIES or any(kw in name_lower for kw in _CHEM_KEYWORDS):
                    chem_names.append(comp["name"])
            # Fall back to the raw query itself (handles direct chemical queries)
            if not chem_names:
                chem_names = [query]

            async def _fetch_pubchem() -> list[dict[str, Any]]:
                results = []
                for name in chem_names[:2]:  # max 2 lookups
                    try:
                        data = await _pubchem.get_chemical_data(name)
                        if not data.get("error"):
                            results.append(data)
                    except Exception:
                        pass
                return results

            # --- Commodity prices: metals mentioned in query or KB components ---
            _METAL_KEYWORDS: dict[str, str] = {
                "copper": "copper", "gold": "gold", "silver": "silver",
                "palladium": "palladium", "platinum": "platinum",
                "aluminum": "aluminum", "aluminium": "aluminum",
                "cobalt": "cobalt", "tungsten": "tungsten", "tin": "tin",
                "gallium": "gallium", "germanium": "germanium",
                "ruthenium": "ruthenium", "nickel": "nickel",
            }
            metals_to_fetch: list[str] = []
            seen_metals: set[str] = set()
            query_lower = query.lower()
            for kw, metal in _METAL_KEYWORDS.items():
                if kw in query_lower and metal not in seen_metals:
                    metals_to_fetch.append(metal)
                    seen_metals.add(metal)
            for comp in kb_result.get("components", [])[:3]:
                comp_text = (comp.get("name", "") + " " + " ".join(comp.get("aliases", []))).lower()
                for kw, metal in _METAL_KEYWORDS.items():
                    if kw in comp_text and metal not in seen_metals:
                        metals_to_fetch.append(metal)
                        seen_metals.add(metal)

            async def _fetch_commodity_prices() -> list[dict[str, Any]]:
                results = []
                for metal in metals_to_fetch[:3]:  # max 3 price lookups
                    try:
                        data = await _world_bank.get_commodity_price(metal)
                        results.append(data)
                    except Exception:
                        pass
                return results

            # Run all three concurrently — different APIs, no shared rate limits
            fedreg_raw, pubchem_raw, commodity_raw = await asyncio.gather(
                _fetch_fedreg(),
                _fetch_pubchem(),
                _fetch_commodity_prices(),
                return_exceptions=True,
            )
            if isinstance(fedreg_raw, Exception):
                fedreg_raw = []
            if isinstance(pubchem_raw, Exception):
                pubchem_raw = []
            if isinstance(commodity_raw, Exception):
                commodity_raw = []

            # Build Federal Register context
            fedreg_context: list[str] = []
            fedreg_sources: list[dict[str, Any]] = []
            for doc in (fedreg_raw or [])[:4]:
                if doc.get("title") and not doc.get("error"):
                    fedreg_context.append(
                        f"U.S. regulatory document ({doc.get('date', '')[:10]}): "
                        f"{doc['title']}. "
                        f"Agency: {', '.join(doc.get('agencies', []))}. "
                        f"{doc.get('abstract', '')[:300]}"
                    )
                    fedreg_sources.append({
                        "type": "federal_register",
                        "title": doc["title"],
                        "url": doc.get("url", ""),
                    })

            # Build PubChem context
            chem_context: list[str] = []
            chem_sources: list[dict[str, Any]] = []
            for chem in (pubchem_raw or []):
                ghs = chem.get("ghs", {})
                hazards = "; ".join(ghs.get("hazard_statements", [])[:3])
                name_display = chem.get("iupac_name") or chem.get("query", "")
                chem_context.append(
                    f"Chemical data for {name_display} "
                    f"(formula: {chem.get('molecular_formula', '?')}, "
                    f"MW: {chem.get('molecular_weight', '?')}). "
                    f"GHS signal: {ghs.get('signal_word', 'unknown')}. "
                    f"Hazards: {hazards or 'none listed'}."
                )
                chem_sources.append({
                    "type": "pubchem",
                    "title": f"{chem.get('query', '')} chemical safety",
                    "url": chem.get("pubchem_url", ""),
                })

            # Build commodity price context
            commodity_context: list[str] = []
            commodity_sources: list[dict[str, Any]] = []
            for price in (commodity_raw or []):
                metal = price.get("material", "")
                if price.get("available"):
                    pct = price.get("pct_change_month")
                    pct_str = f" ({pct:+.1f}% month-over-month)" if pct is not None else ""
                    commodity_context.append(
                        f"Commodity price for {metal}: "
                        f"{price['latest_price']} {price['unit']} "
                        f"as of {price.get('latest_date', 'recent')}. "
                        f"Trend: {price.get('trend', 'unknown')}{pct_str}."
                    )
                else:
                    commodity_context.append(
                        f"Commodity price for {metal}: not available via free API. "
                        f"{price.get('note', 'Check USGS or LME for current pricing.')}"
                    )
                commodity_sources.append({
                    "type": "commodity_prices",
                    "title": f"{metal} price data",
                    "url": price.get("source_url", price.get("lme_url", "")),
                })

            # Cache NewsAPI results by query string — only re-fetch when query changes.
            # NewsAPI quota is limited; hitting it 3× with the same query wastes calls.
            news_cache: dict[str, list] = {}

            for attempt in range(1, max_attempts + 1):
                contexts = (
                    kb_contexts + trade_context + gdelt_contexts
                    + fedreg_context + chem_context + commodity_context
                )
                sources = (
                    kb_sources + trade_sources + gdelt_sources
                    + fedreg_sources + chem_sources + commodity_sources
                )

                news_key = f"{query} semiconductor supply chain"
                if news_key not in news_cache:
                    try:
                        news_cache[news_key] = await newsapi.search(news_key, max_results=5)
                    except Exception:
                        news_cache[news_key] = []
                news_res = news_cache[news_key]

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
                        entity_coros.append(_opensanctions.screen_entity(entity, OPENSANCTIONS_API_KEY))
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
