"""PubChem PUG REST API client — free, no API key required.

Provides chemical property data and GHS safety classifications for process
chemicals used in semiconductor fabrication (etchants, precursors, developers,
solvents, specialty gases).
"""

import asyncio
import urllib.parse
from typing import Any, cast

from ..cache import TTLCache
from ..http_client import get_client
from ..schemas import ChemicalData, GHSData

_BASE_PUG = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
_BASE_PUG_VIEW = "https://pubchem.ncbi.nlm.nih.gov/rest/pug_view"
_TIMEOUT = 20.0
_HEADERS = {"User-Agent": "semiconductor-mcp-research/1.0"}

_PROPERTIES = ",".join([
    "MolecularFormula",
    "MolecularWeight",
    "IUPACName",
    "CanonicalSMILES",
    "InChIKey",
    "Charge",
    "HBondDonorCount",
    "HBondAcceptorCount",
])

# Chemical properties are stable — cache for 24 hours
_cache: TTLCache = TTLCache(ttl_seconds=86400, name="pubchem")


async def _get_cid(name: str) -> int | None:
    """Resolve a chemical name to a PubChem CID."""
    encoded = urllib.parse.quote(name, safe="")
    client = get_client()
    try:
        resp = await client.get(
            f"{_BASE_PUG}/compound/name/{encoded}/cids/JSON",
            params={"name_type": "complete"},
            headers=_HEADERS,
            timeout=_TIMEOUT,
        )
        if resp.status_code == 404:
            resp = await client.get(
                f"{_BASE_PUG}/compound/name/{encoded}/cids/JSON",
                headers=_HEADERS,
                timeout=_TIMEOUT,
            )
        if resp.status_code != 200:
            return None
        data = resp.json()
        cids = data.get("IdentifierList", {}).get("CID", [])
        return cids[0] if cids else None
    except Exception:
        return None


async def _get_properties(cid: int) -> dict[str, Any]:
    client = get_client()
    try:
        resp = await client.get(
            f"{_BASE_PUG}/compound/cid/{cid}/property/{_PROPERTIES}/JSON",
            headers=_HEADERS,
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        props_list = resp.json().get("PropertyTable", {}).get("Properties", [])
        return props_list[0] if props_list else {}
    except Exception:
        return {}


def _find_section(sections: list, keyword: str) -> dict | None:
    kw = keyword.lower()
    for s in sections:
        if kw in s.get("TOCHeading", "").lower():
            return s
    return None


def _extract_strings(info_items: list) -> list[str]:
    out: list[str] = []
    for item in info_items:
        for sv in item.get("Value", {}).get("StringWithMarkup", []):
            s = sv.get("String", "").strip()
            if s:
                out.append(s)
    return out


async def _get_ghs(cid: int) -> dict[str, Any]:
    """Fetch GHS classification from PUG View."""
    client = get_client()
    try:
        resp = await client.get(
            f"{_BASE_PUG_VIEW}/data/compound/{cid}/JSON",
            params={"heading": "GHS Classification"},
            headers=_HEADERS,
            timeout=_TIMEOUT,
        )
        if resp.status_code != 200:
            return {}
        data = resp.json()
        record = data.get("Record", {})

        top_sections = record.get("Section", [])
        safety = _find_section(top_sections, "safety")
        hazid = _find_section(safety.get("Section", []) if safety else [], "hazard")
        ghs = _find_section(hazid.get("Section", []) if hazid else [], "ghs")

        if ghs is None:
            ghs = _find_section(top_sections, "ghs")
        if ghs is None:
            return {}

        result: dict[str, Any] = {"signal_word": "", "hazard_statements": [], "pictograms": []}

        for item in ghs.get("Information", []):
            name = item.get("Name", "").lower()
            strings = _extract_strings([item])
            if not strings:
                continue
            if "signal" in name:
                result["signal_word"] = strings[0]
            elif "hazard statement" in name:
                result["hazard_statements"] = strings[:10]
            elif "pictogram" in name:
                result["pictograms"] = [s for s in strings if s.strip()]

        return result
    except Exception:
        return {}


async def get_chemical_data(name: str) -> ChemicalData | dict[str, Any]:
    """Fetch chemical properties and GHS safety data for a given chemical name."""
    cache_key = name.strip().lower()
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached

    cid = await _get_cid(name)
    if cid is None:
        return {
            "error": f"Chemical '{name}' not found in PubChem",
            "query": name,
            "pubchem_url": f"https://pubchem.ncbi.nlm.nih.gov/#query={name}",
        }

    props, ghs = await asyncio.gather(_get_properties(cid), _get_ghs(cid))

    result = ChemicalData(
        query=name,
        cid=cid,
        pubchem_url=f"https://pubchem.ncbi.nlm.nih.gov/compound/{cid}",
        molecular_formula=props.get("MolecularFormula", ""),
        molecular_weight=props.get("MolecularWeight", ""),
        iupac_name=props.get("IUPACName", ""),
        canonical_smiles=props.get("CanonicalSMILES", ""),
        ghs=cast(GHSData, ghs),
    )
    _cache.set(cache_key, result)
    return result
