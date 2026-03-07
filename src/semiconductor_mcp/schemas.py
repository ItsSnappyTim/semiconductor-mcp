"""TypedDict schemas for source adapter return types.

These serve as documentation and enable mypy type-checking across the
source adapter → server.py boundary. When a source adapter changes the shape
of what it returns, mypy will flag mismatches here before they cause silent
runtime failures in context-building code.

Source adapters should annotate their return types with these schemas.
"""

from typing import Any, TypedDict

# ---------------------------------------------------------------------------
# Academic sources (arXiv, Semantic Scholar)
# ---------------------------------------------------------------------------

class PaperResult(TypedDict):
    source: str             # "arxiv" | "semantic_scholar"
    title: str
    abstract: str
    year: str
    authors: list[str]
    url: str
    doi: str | None
    citation_count: int | None


# ---------------------------------------------------------------------------
# News (NewsAPI, GDELT)
# ---------------------------------------------------------------------------

class NewsResult(TypedDict):
    source: str
    title: str
    description: str
    url: str
    published_at: str


class GdeltArticle(TypedDict):
    title: str
    url: str
    domain: str
    date: str               # YYYYMMDDHHMMSS


# ---------------------------------------------------------------------------
# Compliance (OpenSanctions, BIS/ITA)
# ---------------------------------------------------------------------------

class SanctionsMatch(TypedDict):
    id: str
    caption: str
    schema: str
    datasets: list[str]
    countries: list[str]
    aliases: list[str]


class SanctionsResult(TypedDict):
    query: str
    total: int
    risk: str               # "CLEAR" | "FLAGGED" | "BLOCKED" | "UNKNOWN"
    matches: list[SanctionsMatch]
    source_url: str


class ITAMatch(TypedDict):
    name: str
    source_list: str
    country: str
    addresses: list[Any]
    federal_register_notice: str
    end_date: str


class ITAResult(TypedDict):
    query: str
    total: int
    results: list[ITAMatch]
    risk: str               # "CLEAR" | "FLAGGED" | "BLOCKED" | "UNKNOWN"
    note: str


# ---------------------------------------------------------------------------
# Supply chain data
# ---------------------------------------------------------------------------

class FilingResult(TypedDict):
    company_name: str
    form_type: str
    filed_at: str
    period: str
    file_url: str
    excerpt: str            # Empty string when EFTS doesn't return text


class RegulationDoc(TypedDict):
    title: str
    type: str
    document_number: str
    date: str
    abstract: str
    url: str
    agencies: list[str]


class TradeExporter(TypedDict):
    country: str
    reporter_code: int
    value_usd: float
    share_pct: float


class TradeFlowResult(TypedDict):
    hs_code: str
    year: int
    total_exports_usd: float
    top_exporters: list[TradeExporter]
    record_count: int
    note: str


# ---------------------------------------------------------------------------
# Chemical data (PubChem)
# ---------------------------------------------------------------------------

class GHSData(TypedDict):
    signal_word: str
    hazard_statements: list[str]
    pictograms: list[str]


class ChemicalData(TypedDict):
    query: str
    cid: int
    pubchem_url: str
    molecular_formula: str
    molecular_weight: str
    iupac_name: str
    canonical_smiles: str
    ghs: GHSData


# ---------------------------------------------------------------------------
# Commodity prices (Yahoo Finance / World Bank)
# ---------------------------------------------------------------------------

class PricePoint(TypedDict):
    date: str               # YYYY-MM
    value: float


class CommodityPrice(TypedDict):
    material: str
    symbol: str
    unit: str
    available: bool
    latest_price: float | None
    latest_date: str | None
    previous_price: float | None
    previous_date: str | None
    pct_change_month: float | None
    trend: str
    history: list[PricePoint]
    source_url: str
