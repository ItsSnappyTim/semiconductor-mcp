import xml.etree.ElementTree as ET
from typing import Any

import httpx

_NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
}

_BASE = "https://export.arxiv.org/api/query"


async def search(query: str, max_results: int = 5) -> list[dict[str, Any]]:
    # Require all terms to co-occur in title OR in abstract (avoids noise from all-fields)
    terms = query.strip().split()
    if len(terms) == 1:
        search_query = f"all:{terms[0]}"
    else:
        ti_clause = " AND ".join(f"ti:{t}" for t in terms)
        abs_clause = " AND ".join(f"abs:{t}" for t in terms)
        search_query = f"({ti_clause}) OR ({abs_clause})"
    params = {
        "search_query": search_query,
        "max_results": max_results,
        "sortBy": "relevance",
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(_BASE, params=params)
        resp.raise_for_status()

    root = ET.fromstring(resp.text)
    results = []
    for entry in root.findall("atom:entry", _NS):
        title_el = entry.find("atom:title", _NS)
        summary_el = entry.find("atom:summary", _NS)
        published_el = entry.find("atom:published", _NS)
        id_el = entry.find("atom:id", _NS)

        doi = None
        doi_el = entry.find("arxiv:doi", _NS)
        if doi_el is not None and doi_el.text:
            doi = doi_el.text.strip()

        authors = [
            a.find("atom:name", _NS).text  # type: ignore[union-attr]
            for a in entry.findall("atom:author", _NS)
            if a.find("atom:name", _NS) is not None
        ]

        results.append(
            {
                "source": "arxiv",
                "title": (title_el.text or "").strip() if title_el is not None else "",
                "abstract": (summary_el.text or "").strip() if summary_el is not None else "",
                "year": (published_el.text or "")[:4] if published_el is not None else "",
                "authors": authors,
                "url": (id_el.text or "").strip() if id_el is not None else "",
                "doi": doi,
                "citation_count": None,
            }
        )
    return results
