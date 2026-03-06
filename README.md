# semiconductor-mcp

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server that gives AI assistants deep, real-time intelligence about the semiconductor supply chain — component availability, export controls, sanctions screening, trade flows, grey market risk, and more.

Designed to run as a persistent HTTP service (deployed on Railway) and connect to any MCP-compatible client (e.g. Claude Desktop, Cursor).

---

## What it does

The server exposes **7 tools** to MCP clients:

| Tool | Description |
|------|-------------|
| `add_whitepaper` | Index a PDF into the local full-text search database |
| `search_whitepapers` | FTS5 search across indexed PDFs with highlighted snippets |
| `list_whitepapers` | List all indexed whitepapers |
| `screen_entity` | Screen a company or individual against global sanctions & export control lists |
| `evaluate_response` | RAGAS-inspired quality scoring for a generated answer *(requires `ENABLE_EVAL`)* |
| `research_and_verify` | Research a semiconductor question with academic + news sources and auto-verify answer quality *(requires `ENABLE_EVAL`)* |
| `research_and_verify_supply_chain` | Full supply chain intelligence: KB + trade data + GDELT news + regulations + chemical safety + commodity prices + SEC filings + sanctions *(requires `ENABLE_EVAL`)* |

### Data sources

`research_and_verify_supply_chain` aggregates context from:

- **Internal knowledge base** — curated component/supplier/process-step data with HS codes, export control flags, and grey market risk ratings
- **UN Comtrade** — annual bilateral trade flow data by HS code *(optional API key)*
- **GDELT** — real-time global news for supply chain signals and grey market/smuggling enforcement stories
- **Federal Register** — BIS and OFAC regulatory documents from the past 12 months
- **PubChem** — chemical safety (GHS hazard data) for process chemicals and CVD precursors
- **World Bank** — commodity spot prices for metals (copper, gold, palladium, etc.)
- **NewsAPI** — semiconductor industry news *(required API key)*
- **SEC EDGAR** — 10-K/10-Q supply chain risk disclosures for named companies
- **OpenSanctions** — entity screening across 100+ sanctions and watch lists *(optional API key)*
- **ITA Consolidated Screening List** — BIS Entity List, Denied Persons, OFAC SDN *(optional API key)*
- **arXiv / Semantic Scholar** — academic papers (used by `research_and_verify`)

---

## Running locally

**Prerequisites:** Python 3.11+, [uv](https://docs.astral.sh/uv/)

```bash
git clone https://github.com/ItsSnappyTim/semiconductor-mcp.git
cd semiconductor-mcp

# Install dependencies
uv sync

# Create a .env file (see Environment variables below)
cp .env.example .env   # or create manually

# Start the server
uv run semiconductor-mcp
```

The server listens on `http://localhost:8000` by default.

### Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `MCP_AUTH_TOKEN` | **Yes** | Bearer token clients must send in `Authorization` header |
| `NEWSAPI_KEY` | **Yes** | [NewsAPI](https://newsapi.org/) key for news search |
| `ANTHROPIC_API_KEY` | If `ENABLE_EVAL=1` | Claude API key for answer drafting and evaluation |
| `ENABLE_EVAL` | No | Set to `1` to enable the three research/evaluation tools |
| `COMTRADE_API_KEY` | No | [UN Comtrade](https://comtradeapi.un.org/) key for trade flow data |
| `ITA_API_KEY` | No | [ITA developer portal](https://developer.trade.gov/) key for the Consolidated Screening List |
| `OPENSANCTIONS_API_KEY` | No | [OpenSanctions](https://www.opensanctions.org/api/) key |
| `WHITEPAPER_DIR` | No | Absolute path for whitepaper storage (default: `data/whitepapers/`) |
| `DB_PATH` | No | Absolute path for the SQLite database (default: `data/whitepapers.db`) |
| `PORT` | No | HTTP port (default: `8000`) |

---

## Connecting a client

Add the server to your MCP client config. Example for **Claude Desktop** (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "semiconductor": {
      "url": "http://localhost:8000/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_MCP_AUTH_TOKEN"
      }
    }
  }
}
```

Replace `localhost:8000` with your Railway public URL if deployed remotely.

---

## Deploying to Railway

The repo includes a `railway.toml` with the correct start command and health check path.

1. Create a new Railway project and connect this repo
2. Add all required environment variables in the Railway dashboard
3. For whitepaper persistence, attach a Railway Volume mounted at `/data`

---

## Project structure

```
src/semiconductor_mcp/
├── server.py          # MCP tool definitions and server entry point
├── config.py          # Environment variable loading
├── db.py              # SQLite FTS5 database for whitepapers
├── knowledge_base.py  # Curated semiconductor component/supplier data
├── pdf_utils.py       # PDF text extraction (thread-isolated)
├── evaluator.py       # RAGAS-inspired answer quality scoring (Claude-backed)
└── sources/
    ├── arxiv.py
    ├── bis_screening.py
    ├── comtrade.py
    ├── edgar.py
    ├── federal_register.py
    ├── gdelt.py
    ├── newsapi.py
    ├── opensanctions.py
    ├── pubchem.py
    ├── semantic_scholar.py
    └── world_bank.py
```

---

## Security notes

- All endpoints (except `/health`) require a `Bearer` token via constant-time comparison
- Whitepaper uploads are path-traversal protected and size-limited (50 MB)
- PDF extraction runs in a separate thread with a 60-second timeout
- GDELT requests are rate-limited with a semaphore (max 2 concurrent) and exponential backoff
- DNS rebinding protection is disabled intentionally to allow Railway's public hostname; Bearer auth is the security boundary
