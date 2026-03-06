"""Curated semiconductor fabrication knowledge base.

Two top-level dicts:
  PROCESS_STEPS  — fab process steps (ID → metadata)
  COMPONENTS     — components/materials/equipment (ID → metadata)

Public API:
  search(query: str) -> dict   — returns top matching components + process steps
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Process steps
# ---------------------------------------------------------------------------

PROCESS_STEPS: dict[str, dict] = {
    "wafer_prep": {
        "name": "Wafer Preparation",
        "category": "front_end",
        "description": (
            "Silicon crystal growth (Czochralski process), ingot slicing, "
            "lapping, grinding, and chemical-mechanical polishing to produce "
            "prime-grade 300mm silicon wafers."
        ),
        "node_applicability": ["all nodes"],
        "component_ids": [
            "silicon_wafer_300mm", "argon_gas_bulk", "hf_acid_electronic",
            "cmp_slurry", "cmp_polishing_pad", "cmp_system",
        ],
    },
    "thermal_oxidation": {
        "name": "Thermal Oxidation",
        "category": "front_end",
        "description": (
            "Dry or wet oxidation in a furnace to grow SiO2 layers used as "
            "gate dielectrics (legacy nodes), field isolation, or hardmask."
        ),
        "node_applicability": ["mature nodes (>28nm)"],
        "component_ids": ["argon_gas_bulk", "cvd_system"],
    },
    "lithography_duv": {
        "name": "DUV Lithography (ArF Immersion, 193nm)",
        "category": "patterning",
        "description": (
            "ArF immersion lithography at 193nm, the workhorse patterning "
            "technology for 7nm–28nm nodes and mature nodes. Requires "
            "neon-fluorine laser gas blend, photoresist, and reticles."
        ),
        "node_applicability": ["7nm–28nm and older", "mature nodes"],
        "component_ids": [
            "duv_scanner_arf", "duv_photoresist_arf", "photomask_euv",
            "neon_gas", "krypton_gas", "argon_gas_bulk",
        ],
    },
    "lithography_euv": {
        "name": "EUV Lithography (13.5nm)",
        "category": "patterning",
        "description": (
            "Extreme ultraviolet lithography at 13.5nm for leading-edge nodes "
            "≤7nm. Requires tin plasma light source, reflective optics from "
            "Carl Zeiss SMT, EUV-specific photoresist, and pellicles."
        ),
        "node_applicability": ["<7nm", "5nm", "3nm", "2nm", "1.4nm"],
        "component_ids": [
            "euv_system", "euv_photoresist", "euv_pellicle", "photomask_euv",
            "euv_optics", "tin_euv_target",
        ],
    },
    "etch_dry": {
        "name": "Dry Etch (Plasma / RIE / ALE)",
        "category": "removal",
        "description": (
            "Plasma-based material removal including reactive ion etch (RIE), "
            "inductively coupled plasma (ICP) etch, and atomic layer etch (ALE). "
            "Used for gate patterning, contact/via etch, and high-aspect-ratio "
            "structures in 3D NAND."
        ),
        "node_applicability": ["all nodes"],
        "component_ids": [
            "etch_system_advanced", "specialty_etch_gases", "argon_gas_bulk",
        ],
    },
    "etch_wet": {
        "name": "Wet Etch & Chemical Cleaning",
        "category": "removal",
        "description": (
            "Isotropic chemical etching and surface cleaning using HF (oxide "
            "removal), SC-1 (NH4OH/H2O2/H2O), SC-2 (HCl/H2O2/H2O), and "
            "SPM (H2SO4/H2O2). Critical for particle and metal contamination "
            "control throughout the process."
        ),
        "node_applicability": ["all nodes"],
        "component_ids": ["hf_acid_electronic", "argon_gas_bulk"],
    },
    "cvd_deposition": {
        "name": "Chemical Vapor Deposition (CVD / PECVD / SACVD)",
        "category": "deposition",
        "description": (
            "Gas-phase deposition of dielectric films (SiO2, SiN, SiCOH low-k) "
            "and conductive films. PECVD uses plasma to enable lower temperature "
            "deposition. Used throughout the process for ILD, hardmask, and "
            "spacer films."
        ),
        "node_applicability": ["all nodes"],
        "component_ids": [
            "cvd_system", "ald_precursors_metal", "specialty_etch_gases",
            "argon_gas_bulk",
        ],
    },
    "ald": {
        "name": "Atomic Layer Deposition (ALD)",
        "category": "deposition",
        "description": (
            "Self-limiting sequential precursor exposures for angstrom-level "
            "thickness control. Essential for high-k gate dielectrics (HfO2), "
            "metal gate work-function metals (TiN, TiAl), diffusion barriers "
            "(TaN), and conformal coatings in high-aspect-ratio structures."
        ),
        "node_applicability": ["<28nm"],
        "component_ids": [
            "ald_system", "ald_precursors_metal", "hafnium", "tantalum",
            "argon_gas_bulk",
        ],
    },
    "pvd_sputtering": {
        "name": "Physical Vapor Deposition (PVD / Sputtering)",
        "category": "deposition",
        "description": (
            "Target sputtering to deposit metal films: Ta/TaN diffusion barrier, "
            "Cu seed layer, Ti/TiN liner, Al interconnect (legacy), and "
            "cobalt/ruthenium liner layers at leading edge."
        ),
        "node_applicability": ["all nodes"],
        "component_ids": [
            "pvd_system", "tantalum", "cobalt", "ruthenium", "argon_gas_bulk",
        ],
    },
    "ion_implant": {
        "name": "Ion Implantation",
        "category": "doping",
        "description": (
            "Accelerating dopant ions (B, P, As, In, Sb) into silicon to "
            "form source/drain, well, halo, and extension regions. Covers a "
            "wide energy/dose range from ultra-shallow junction to deep well."
        ),
        "node_applicability": ["all nodes"],
        "component_ids": ["ion_implant_system", "argon_gas_bulk"],
    },
    "rtp_anneal": {
        "name": "Rapid Thermal Processing (RTP / RTA / Laser Anneal)",
        "category": "thermal",
        "description": (
            "Millisecond to second thermal processing to activate implanted "
            "dopants, crystallize films, form silicide contacts, and anneal "
            "defects. Flash and laser anneal used at leading edge to minimize "
            "thermal budget."
        ),
        "node_applicability": ["all nodes"],
        "component_ids": ["argon_gas_bulk"],
    },
    "cmp": {
        "name": "Chemical Mechanical Planarization (CMP)",
        "category": "planarization",
        "description": (
            "Mechanical polishing with chemical slurry to planarize wafer "
            "surfaces. Used after STI (oxide CMP), tungsten contact fill, "
            "copper damascene (Cu + barrier CMP), and after each metal layer "
            "in BEOL. Critical for achieving planarity requirements at "
            "leading-edge nodes."
        ),
        "node_applicability": ["all nodes"],
        "component_ids": [
            "cmp_system", "cmp_slurry", "cmp_polishing_pad",
            "hf_acid_electronic",
        ],
    },
    "metallization_cu": {
        "name": "Copper Interconnect (Damascene / Electroplating)",
        "category": "interconnect",
        "description": (
            "Copper dual-damascene process: barrier deposition (TaN/Ta or Ru), "
            "Cu seed layer (PVD), electrochemical deposition (ECD) to fill "
            "trenches/vias, followed by CMP. Dominates BEOL from 130nm onwards. "
            "Ruthenium emerging as barrier/liner replacement at <2nm."
        ),
        "node_applicability": ["<130nm"],
        "component_ids": [
            "pvd_system", "copper_sulfate_ecd", "tantalum", "cobalt",
            "ruthenium", "cmp_system", "cmp_slurry",
        ],
    },
    "metallization_w": {
        "name": "Tungsten Contact / Via Fill (CVD)",
        "category": "interconnect",
        "description": (
            "CVD tungsten deposition using WF6 (tungsten hexafluoride) as "
            "precursor to fill contact and via openings. Ti/TiN liner deposited "
            "first by PVD. Tungsten used for contact plugs and local "
            "interconnects due to its thermal stability."
        ),
        "node_applicability": ["all nodes"],
        "component_ids": ["cvd_system", "wf6_tungsten_hex", "tungsten", "pvd_system"],
    },
    "inspection_metrology": {
        "name": "Metrology and Inspection",
        "category": "quality",
        "description": (
            "In-line measurement and defect detection: CD-SEM for critical "
            "dimension measurement, OCD/scatterometry for film stacks, "
            "e-beam and optical inspection for defect detection, overlay "
            "metrology for lithography alignment. Essential at every major "
            "process step for yield control."
        ),
        "node_applicability": ["all nodes"],
        "component_ids": ["metrology_system"],
    },
}


# ---------------------------------------------------------------------------
# Components
# ---------------------------------------------------------------------------

COMPONENTS: dict[str, dict] = {

    # -----------------------------------------------------------------------
    # Capital Equipment
    # -----------------------------------------------------------------------

    "euv_system": {
        "name": "EUV Lithography System",
        "aliases": ["EUV scanner", "ASML NXE", "ASML EXE", "High-NA EUV", "extreme ultraviolet"],
        "category": "capital_equipment",
        "description": (
            "EUV lithography systems expose wafers at 13.5nm wavelength. "
            "ASML's NXE series (0.33 NA) is the production workhorse; "
            "the EXE:5000 (0.55 NA High-NA) began delivery in 2023 for "
            "sub-2nm nodes. Each system weighs ~180 tonnes and contains "
            "~100,000 components."
        ),
        "used_in_steps": ["lithography_euv"],
        "availability": "single_source",
        "key_suppliers": [
            {"name": "ASML", "country": "Netherlands", "market_share": "100%",
             "notes": "Sole global supplier; no alternative exists or is in development"},
        ],
        "supply_risks": [
            "Monopoly — any ASML disruption halts all EUV-based chip production globally",
            "Lead time 12–18 months per system at ~$200M (NXE) to ~$380M (High-NA)",
            "EUV optics (Carl Zeiss SMT) and light sources (Cymer/Gigaphoton) are themselves single/dual-source",
            "Export to China blocked since ASML declined to renew license in 2019; fully restricted 2023",
        ],
        "export_controls": {
            "status": "strict",
            "detail": (
                "Dutch Strategic Goods Export Regulation (Strategische Goederen). "
                "US EAR foreign direct product rule applies (US-origin technology in optics/source). "
                "Export to China, Russia, and other restricted destinations prohibited."
            ),
            "eccn": "3B001.a",
        },
        "grey_market_risk": "critical",
        "grey_market_detail": (
            "Documented attempts by Chinese entities to acquire EUV systems through "
            "front companies in Singapore, Malaysia, and South Korea. BIS and Dutch "
            "authorities have brought enforcement actions. System size and customs "
            "visibility make actual diversion nearly impossible, but procurement "
            "networks remain active."
        ),
        "critical_mineral": False,
        "geographic_concentration": "Netherlands (sole production site: Veldhoven)",
        "hs_codes": ["8486.20"],
    },

    "duv_scanner_arf": {
        "name": "ArF Immersion DUV Lithography Scanner",
        "aliases": ["ArF scanner", "ArFi", "193nm immersion", "DUV scanner", "Nikon scanner", "Canon scanner"],
        "category": "capital_equipment",
        "description": (
            "193nm ArF immersion scanners use water as an immersion medium to "
            "achieve effective wavelengths below 193nm. Workhorse for 7nm–28nm "
            "nodes and all mature node production. Multiple exposure/patterning "
            "techniques (SAQP, SADP) extend reach to smaller features."
        ),
        "used_in_steps": ["lithography_duv"],
        "availability": "specialized",
        "key_suppliers": [
            {"name": "ASML", "country": "Netherlands", "market_share": "~80%",
             "notes": "TWINSCAN NXT series; dominant at leading edge DUV"},
            {"name": "Nikon", "country": "Japan", "market_share": "~15%",
             "notes": "NSR series; strong in memory and mature logic"},
            {"name": "Canon", "country": "Japan", "market_share": "~5%",
             "notes": "FPA series; primarily mature nodes"},
        ],
        "supply_risks": [
            "ASML dominance means Nikon/Canon capacity may be insufficient if ASML disrupted",
            "All three suppliers in allied countries (Netherlands, Japan) — geopolitical alignment stable",
            "Lead time 6–12 months",
            "Neon laser gas supply disruption (Ukraine 2022) stressed ArF scanner availability",
        ],
        "export_controls": {
            "status": "partial",
            "detail": (
                "Less restricted than EUV, but advanced ArF immersion tools (capable of <28nm) "
                "are subject to US EAR and Dutch/Japanese export controls for some destinations."
            ),
            "eccn": "3B001.a",
        },
        "grey_market_risk": "medium",
        "grey_market_detail": (
            "Older DUV scanners actively traded on secondary market and through "
            "brokers. China has accumulated significant DUV scanner installed base "
            "prior to restrictions. Remarked or mislabeled DUV equipment has "
            "been documented in enforcement cases."
        ),
        "critical_mineral": False,
        "geographic_concentration": "Netherlands + Japan (all production)",
        "hs_codes": ["8486.20"],
    },

    "euv_optics": {
        "name": "EUV Optical Elements (Multilayer Mirrors)",
        "aliases": ["EUV mirrors", "EUV projection optics", "Zeiss optics", "Carl Zeiss SMT"],
        "category": "capital_equipment",
        "description": (
            "EUV optics use multilayer Mo/Si mirrors (not lenses — EUV is absorbed "
            "by all materials) ground to sub-nanometer surface roughness. Carl Zeiss "
            "SMT is the sole supplier of EUV projection optics for all ASML systems. "
            "ASML holds a 24.9% stake in Zeiss SMT."
        ),
        "used_in_steps": ["lithography_euv"],
        "availability": "single_source",
        "key_suppliers": [
            {"name": "Carl Zeiss SMT", "country": "Germany", "market_share": "100%",
             "notes": "Sole supplier of EUV projection optics globally; ~1,000 employees dedicated to EUV"},
        ],
        "supply_risks": [
            "Single source — Zeiss SMT disruption stops all EUV system production",
            "Zeiss SMT is itself dependent on specialty glass from Schott AG (also German)",
            "Polishing process takes months per mirror set; no surge capacity possible",
            "US/Netherlands export controls apply (Zeiss uses US-origin technology)",
        ],
        "export_controls": {
            "status": "strict",
            "detail": "Controlled as part of EUV system (ECCN 3B001.a); cannot be separately exported to restricted parties.",
            "eccn": "3B001.a",
        },
        "grey_market_risk": "low",
        "grey_market_detail": (
            "Optics are custom-built for specific ASML systems and cannot function "
            "standalone; grey market risk is low, but the single-source dependency "
            "creates catastrophic supply risk."
        ),
        "critical_mineral": False,
        "geographic_concentration": "Germany (Oberkochen) — single facility",
        "hs_codes": ["9001.90"],
    },

    "etch_system_advanced": {
        "name": "Advanced Plasma Etch System",
        "aliases": ["RIE", "plasma etch", "ALE", "HAR etch", "Lam etch", "TEL etch", "AMAT etch"],
        "category": "capital_equipment",
        "description": (
            "Plasma etch systems for conductor and dielectric etch, including "
            "high-aspect-ratio (HAR) etch for 3D NAND wordline and contact "
            "structures, and atomic layer etch (ALE) for FinFET/GAA precision. "
            "Multiple tool types required per fab (dielectric, conductor, strip)."
        ),
        "used_in_steps": ["etch_dry"],
        "availability": "specialized",
        "key_suppliers": [
            {"name": "Lam Research", "country": "USA", "market_share": "~40%",
             "notes": "Dominant in HAR etch for 3D NAND and dielectric etch"},
            {"name": "Tokyo Electron (TEL)", "country": "Japan", "market_share": "~30%",
             "notes": "Strong in conductor etch and strip"},
            {"name": "Applied Materials", "country": "USA", "market_share": "~25%",
             "notes": "Competitive across etch categories"},
        ],
        "supply_risks": [
            "US and Japanese suppliers subject to combined export controls (Oct 2023)",
            "HAR etch for 3D NAND: Lam Research dominant, creating concentration risk",
            "Leading-edge ALE tools require significant process development per application",
        ],
        "export_controls": {
            "status": "strict",
            "detail": (
                "Advanced etch tools capable of ≥45 etch steps or high-aspect-ratio "
                "etching are controlled under US EAR (Commerce Control List) and "
                "Japanese export regulations as of October 2023. Export to China "
                "for advanced nodes effectively blocked."
            ),
            "eccn": "3B001.b",
        },
        "grey_market_risk": "high",
        "grey_market_detail": (
            "Post-2023 export controls have driven significant grey market activity. "
            "Chinese entities have attempted to acquire advanced etch tools through "
            "intermediaries in Southeast Asia. BIS has issued denial orders for "
            "several front companies."
        ),
        "critical_mineral": False,
        "geographic_concentration": "USA + Japan (all leading-edge suppliers)",
        "hs_codes": ["8486.20", "8486.90"],
    },

    "ald_system": {
        "name": "Atomic Layer Deposition (ALD) System",
        "aliases": ["ALD tool", "ASM ALD", "thermal ALD", "plasma ALD"],
        "category": "capital_equipment",
        "description": (
            "ALD systems deposit films one atomic layer at a time via alternating "
            "precursor pulses. Critical for high-k dielectrics (HfO2), metal gate "
            "films (TiN, TiAl, WN), barrier layers (TaN), and conformal coatings "
            "in GAA nanosheet device structures."
        ),
        "used_in_steps": ["ald"],
        "availability": "specialized",
        "key_suppliers": [
            {"name": "ASM International", "country": "Netherlands", "market_share": "~50%",
             "notes": "Leader in thermal ALD; Pulsar and Eagle product lines"},
            {"name": "Applied Materials", "country": "USA", "market_share": "~25%",
             "notes": "Strong in plasma-enhanced ALD"},
            {"name": "Lam Research", "country": "USA", "market_share": "~15%",
             "notes": "ALD for select film applications"},
            {"name": "Tokyo Electron", "country": "Japan", "market_share": "~10%",
             "notes": "Growing ALD portfolio for logic and memory"},
        ],
        "supply_risks": [
            "Subject to US/Japan/Netherlands export controls for advanced applications",
            "Precursor supply (specialty organometallic chemicals) is a separate bottleneck",
        ],
        "export_controls": {
            "status": "strict",
            "detail": "Advanced ALD tools for leading-edge logic controlled under US EAR and Japanese regulations (2023).",
            "eccn": "3B001.b",
        },
        "grey_market_risk": "medium",
        "grey_market_detail": "Similar diversion patterns to etch tools; less documented but actively monitored.",
        "critical_mineral": False,
        "geographic_concentration": "Netherlands + USA + Japan",
        "hs_codes": ["8486.20"],
    },

    "cvd_system": {
        "name": "CVD / PECVD Deposition System",
        "aliases": ["CVD tool", "PECVD", "LPCVD", "SACVD", "Applied Materials CVD", "Lam CVD", "TEL CVD"],
        "category": "capital_equipment",
        "description": (
            "CVD systems deposit dielectric films (SiO2, SiN, SiCOH low-k) and "
            "conductive films from gas-phase precursors. PECVD (plasma-enhanced) "
            "enables lower deposition temperatures. Used throughout the process "
            "from isolation films to ILD."
        ),
        "used_in_steps": ["cvd_deposition", "metallization_w", "thermal_oxidation"],
        "availability": "specialized",
        "key_suppliers": [
            {"name": "Applied Materials", "country": "USA", "market_share": "~35%"},
            {"name": "Lam Research", "country": "USA", "market_share": "~30%"},
            {"name": "Tokyo Electron", "country": "Japan", "market_share": "~20%"},
            {"name": "Kokusai Electric (Hitachi Kokusai)", "country": "Japan", "market_share": "~10%",
             "notes": "Strong in batch furnace CVD for memory"},
        ],
        "supply_risks": [
            "Subject to US/Japan export controls for advanced applications",
            "Leading-edge low-k CVD requires tight process control; few qualified tools",
        ],
        "export_controls": {
            "status": "partial",
            "detail": "Advanced CVD for leading-edge nodes controlled; mature-node CVD more broadly available.",
            "eccn": "3B001.b",
        },
        "grey_market_risk": "medium",
        "grey_market_detail": "Used CVD tools actively traded on secondary market; less controlled than litho or etch.",
        "critical_mineral": False,
        "geographic_concentration": "USA + Japan",
        "hs_codes": ["8486.20"],
    },

    "pvd_system": {
        "name": "PVD / Sputter Deposition System",
        "aliases": ["PVD tool", "sputter", "magnetron sputtering", "Applied Materials PVD", "Endura"],
        "category": "capital_equipment",
        "description": (
            "Physical vapor deposition systems sputter material from a solid target "
            "onto the wafer. Used for metal films: Ta/TaN barrier, Cu seed, Ti/TiN "
            "liner, Al interconnect, and CoWP/Ru capping layers. Applied Materials "
            "Endura platform is the industry standard."
        ),
        "used_in_steps": ["pvd_sputtering", "metallization_cu", "metallization_w"],
        "availability": "specialized",
        "key_suppliers": [
            {"name": "Applied Materials", "country": "USA", "market_share": "~60%",
             "notes": "Endura platform dominates copper barrier/seed PVD"},
            {"name": "Canon Anelva", "country": "Japan", "market_share": "~20%"},
            {"name": "Ulvac", "country": "Japan", "market_share": "~15%"},
        ],
        "supply_risks": [
            "Applied Materials near-monopoly on leading-edge Cu barrier/seed PVD",
            "Subject to export controls for advanced applications",
        ],
        "export_controls": {
            "status": "partial",
            "detail": "Advanced PVD tools for leading-edge nodes subject to US EAR controls.",
            "eccn": "3B001.b",
        },
        "grey_market_risk": "low",
        "grey_market_detail": "Broad installed base; less targeted for diversion than litho/etch tools.",
        "critical_mineral": False,
        "geographic_concentration": "USA + Japan",
        "hs_codes": ["8486.20"],
    },

    "ion_implant_system": {
        "name": "Ion Implant System",
        "aliases": ["implanter", "ion implanter", "Axcelis", "Applied Materials Varian"],
        "category": "capital_equipment",
        "description": (
            "Ion implanters accelerate dopant ions into silicon to form p-n junctions. "
            "Three classes by energy: high current (source/drain), medium current "
            "(well/retrograde), and high energy (deep well). Ultra-shallow junction "
            "implants at leading edge require precise dose and energy control."
        ),
        "used_in_steps": ["ion_implant"],
        "availability": "specialized",
        "key_suppliers": [
            {"name": "Applied Materials (Varian)", "country": "USA", "market_share": "~55%",
             "notes": "Acquired Varian Semiconductor 2011; dominant across all implant categories"},
            {"name": "Axcelis Technologies", "country": "USA", "market_share": "~35%",
             "notes": "Purion product line; strong in high current and high energy"},
            {"name": "Sumitomo Heavy Industries", "country": "Japan", "market_share": "~10%"},
        ],
        "supply_risks": [
            "US suppliers dominate; subject to US export controls",
            "High-dose implant tools for advanced nodes have limited supplier options",
        ],
        "export_controls": {
            "status": "strict",
            "detail": "Advanced ion implant tools controlled under US EAR for export to restricted destinations.",
            "eccn": "3B001.c",
        },
        "grey_market_risk": "medium",
        "grey_market_detail": "Documented cases of Chinese entities attempting to procure implanters through third-country intermediaries.",
        "critical_mineral": False,
        "geographic_concentration": "USA (dominant), Japan",
        "hs_codes": ["8486.20"],
    },

    "cmp_system": {
        "name": "CMP (Chemical Mechanical Planarization) System",
        "aliases": ["CMP tool", "polisher", "Applied Materials Reflexion", "Ebara CMP"],
        "category": "capital_equipment",
        "description": (
            "CMP systems combine chemical reaction and mechanical abrasion to "
            "planarize wafer surfaces. Required at STI, W-plug, Cu BEOL, and "
            "advanced packaging steps. Multiple polishing heads, slurry delivery, "
            "and in-situ endpoint detection are key differentiators."
        ),
        "used_in_steps": ["cmp", "metallization_cu", "wafer_prep"],
        "availability": "specialized",
        "key_suppliers": [
            {"name": "Applied Materials", "country": "USA", "market_share": "~45%",
             "notes": "Reflexion platform; dominant in logic"},
            {"name": "Ebara Corporation", "country": "Japan", "market_share": "~35%",
             "notes": "Strong in memory (DRAM, NAND)"},
            {"name": "Revasum (now Axus)", "country": "USA", "market_share": "~10%"},
        ],
        "supply_risks": [
            "Slurry and pad supply (consumables) are separate and critical bottlenecks",
            "Process window narrowing at leading edge requires co-optimization with slurry supplier",
        ],
        "export_controls": {
            "status": "partial",
            "detail": "Advanced CMP tools subject to US/Japanese export controls for some destinations.",
            "eccn": "3B001",
        },
        "grey_market_risk": "low",
        "grey_market_detail": "Broad availability; used CMP tools widely traded. Lower strategic value than litho tools.",
        "critical_mineral": False,
        "geographic_concentration": "USA + Japan",
        "hs_codes": ["8486.20"],
    },

    "metrology_system": {
        "name": "Metrology and Inspection System",
        "aliases": ["CD-SEM", "OCD", "overlay", "defect inspection", "KLA", "Onto Innovation", "AMAT metrology"],
        "category": "capital_equipment",
        "description": (
            "In-line measurement (CD-SEM, OCD scatterometry, overlay) and defect "
            "detection (e-beam inspection, optical inspection, review SEM) tools. "
            "Yield cannot be controlled without metrology; spending on inspection "
            "tools is ~10–15% of total equipment spend."
        ),
        "used_in_steps": ["inspection_metrology"],
        "availability": "specialized",
        "key_suppliers": [
            {"name": "KLA Corporation", "country": "USA", "market_share": "~50%",
             "notes": "Dominant in defect inspection and CD-SEM"},
            {"name": "Applied Materials", "country": "USA", "market_share": "~20%",
             "notes": "CD-SEM and e-beam inspection"},
            {"name": "Onto Innovation", "country": "USA", "market_share": "~15%",
             "notes": "OCD scatterometry and overlay"},
            {"name": "Hitachi High-Tech", "country": "Japan", "market_share": "~10%",
             "notes": "CD-SEM"},
        ],
        "supply_risks": [
            "US companies dominate; KLA near-monopoly in critical categories",
            "Subject to US export controls for advanced inspection tools",
        ],
        "export_controls": {
            "status": "strict",
            "detail": "Advanced e-beam inspection and leading-edge metrology tools controlled under US EAR.",
            "eccn": "3B001.e",
        },
        "grey_market_risk": "medium",
        "grey_market_detail": "Less targeted than litho tools but KLA inspection tools are on restricted lists for China exports.",
        "critical_mineral": False,
        "geographic_concentration": "USA (dominant), Japan",
        "hs_codes": ["8486.40", "9031.49"],
    },

    # -----------------------------------------------------------------------
    # Critical Materials and Gases
    # -----------------------------------------------------------------------

    "silicon_wafer_300mm": {
        "name": "300mm Silicon Wafer (Prime Grade)",
        "aliases": ["silicon wafer", "300mm wafer", "Si wafer", "CZ wafer", "FZ wafer"],
        "category": "material",
        "description": (
            "Czochralski-grown single-crystal silicon wafers, the substrate for "
            "virtually all logic and memory chips. 300mm is the leading-edge "
            "diameter. Ultra-high purity (9N+), tight specifications on oxygen "
            "content, flatness (SFQR <20nm), and particles."
        ),
        "used_in_steps": ["wafer_prep"],
        "availability": "specialized",
        "key_suppliers": [
            {"name": "Shin-Etsu Handotai (SEH)", "country": "Japan", "market_share": "~30%"},
            {"name": "SUMCO", "country": "Japan", "market_share": "~25%"},
            {"name": "Siltronic", "country": "Germany", "market_share": "~15%"},
            {"name": "SK Siltron", "country": "South Korea", "market_share": "~15%"},
            {"name": "GlobalWafers", "country": "Taiwan", "market_share": "~15%"},
        ],
        "supply_risks": [
            "Japan supplies ~55% of 300mm wafers — natural disaster or geopolitical risk concentrated",
            "Wafer qualification takes 1–2 years; fabs cannot quickly switch suppliers",
            "300mm capacity expansions take 3–5 years from investment to output",
            "Competing demand from automotive and power semiconductors for 200mm capacity",
        ],
        "export_controls": {
            "status": "none",
            "detail": "Standard silicon wafers are not export controlled (EAR99 for commodity grades).",
            "eccn": "EAR99",
        },
        "grey_market_risk": "low",
        "grey_market_detail": "Commodity item; grey market risk is low. Counterfeit wafers (spec misrepresentation) documented in lower-tier supply chains.",
        "critical_mineral": False,
        "geographic_concentration": "Japan ~55%, Germany ~15%, Taiwan ~15%, South Korea ~15%",
        "hs_codes": ["3818.00"],
    },

    "euv_photoresist": {
        "name": "EUV Photoresist",
        "aliases": ["EUV resist", "metal-oxide resist", "CAR resist EUV", "JSR resist", "Shin-Etsu resist"],
        "category": "material",
        "description": (
            "EUV-specific photoresist must absorb 13.5nm photons efficiently "
            "(unlike DUV resists). Two main types: chemically amplified resist (CAR) "
            "and metal-oxide resist (e.g., tin-oxide). Requires extreme purity, "
            "consistent photoacid generator (PAG) loading, and high etch resistance."
        ),
        "used_in_steps": ["lithography_euv"],
        "availability": "specialized",
        "key_suppliers": [
            {"name": "JSR Corporation", "country": "Japan", "market_share": "~40%",
             "notes": "Nationalized by Japanese government in 2023 as strategic asset"},
            {"name": "Shin-Etsu Chemical", "country": "Japan", "market_share": "~30%"},
            {"name": "Tokyo Ohka Kogyo (TOK)", "country": "Japan", "market_share": "~20%"},
            {"name": "Dow Electronic Materials / DuPont", "country": "USA", "market_share": "~10%",
             "notes": "Growing but not yet at leading-edge production scale"},
        ],
        "supply_risks": [
            "All leading EUV photoresist suppliers are Japanese — geographic concentration risk",
            "Japan export controls (Oct 2023) now require licenses for advanced photoresist exports",
            "JSR nationalization (2023) signals Japanese government treating this as strategic infrastructure",
            "Each new node requires extensive resist re-qualification (12–18 months)",
        ],
        "export_controls": {
            "status": "strict",
            "detail": (
                "Japan's October 2023 export controls cover advanced photoresist for EUV. "
                "Requires Japanese government license for export to restricted destinations."
            ),
            "eccn": "1C350 (chemical precursors aspect); 3C006 (resist aspect)",
        },
        "grey_market_risk": "medium",
        "grey_market_detail": (
            "Japan export controls have driven attempts to procure EUV resist through "
            "intermediary countries. Chemical nature makes customs inspection difficult. "
            "However, resist without a qualified EUV scanner is of limited use."
        ),
        "critical_mineral": False,
        "geographic_concentration": "Japan ~90% of supply",
        "hs_codes": ["3707.10"],
    },

    "duv_photoresist_arf": {
        "name": "DUV ArF Photoresist (193nm)",
        "aliases": ["ArF resist", "193nm resist", "DUV resist", "chemically amplified resist"],
        "category": "material",
        "description": (
            "Chemically amplified photoresist for 193nm ArF lithography. Used for "
            "mature and leading-edge nodes in multiple-patterning flows. Also "
            "includes anti-reflective coatings (ARC) and topcoats for immersion."
        ),
        "used_in_steps": ["lithography_duv"],
        "availability": "specialized",
        "key_suppliers": [
            {"name": "JSR Corporation", "country": "Japan", "market_share": "~35%"},
            {"name": "Tokyo Ohka Kogyo (TOK)", "country": "Japan", "market_share": "~25%"},
            {"name": "Shin-Etsu Chemical", "country": "Japan", "market_share": "~20%"},
            {"name": "DuPont", "country": "USA", "market_share": "~10%"},
            {"name": "Fujifilm", "country": "Japan", "market_share": "~10%"},
        ],
        "supply_risks": [
            "Japanese supplier concentration (same risk as EUV resist but somewhat broader)",
            "Subject to Japan export controls (2023)",
        ],
        "export_controls": {
            "status": "partial",
            "detail": "Advanced DUV photoresist covered by Japan's 2023 export control expansion.",
            "eccn": "3C006",
        },
        "grey_market_risk": "low",
        "grey_market_detail": "More broadly available than EUV resist; lower grey market pressure.",
        "critical_mineral": False,
        "geographic_concentration": "Japan ~90%",
        "hs_codes": ["3707.10"],
    },

    "euv_pellicle": {
        "name": "EUV Pellicle",
        "aliases": ["pellicle", "EUV mask pellicle", "ASML pellicle"],
        "category": "material",
        "description": (
            "A thin (50nm) membrane mounted over EUV photomasks to prevent "
            "particle contamination. EUV pellicles must transmit >90% of 13.5nm "
            "light while surviving intense plasma environment. Only recently "
            "commercially viable; still limited supply."
        ),
        "used_in_steps": ["lithography_euv"],
        "availability": "single_source",
        "key_suppliers": [
            {"name": "ASML", "country": "Netherlands", "market_share": "~60%",
             "notes": "Polysilicon-based pellicle; began volume supply ~2023"},
            {"name": "Mitsui Chemicals", "country": "Japan", "market_share": "~40%",
             "notes": "CNT (carbon nanotube) based pellicle"},
        ],
        "supply_risks": [
            "Very limited production capacity; fabs often run without pellicles (mask risk)",
            "Each pellicle degrades over time under EUV dose; high consumable cost",
            "Yield of pellicle manufacturing is low; difficult to scale",
        ],
        "export_controls": {
            "status": "partial",
            "detail": "Controlled as part of EUV infrastructure; subject to Dutch and Japanese export controls.",
            "eccn": "3C905.b",
        },
        "grey_market_risk": "low",
        "grey_market_detail": "Niche product; limited grey market due to extreme technical specificity.",
        "critical_mineral": False,
        "geographic_concentration": "Netherlands + Japan",
        "hs_codes": ["9001.90"],
    },

    "photomask_euv": {
        "name": "Photomask / Reticle (EUV and DUV)",
        "aliases": ["reticle", "photomask", "EUV mask", "photomask blank", "mask blank"],
        "category": "material",
        "description": (
            "Quartz (DUV) or LTEM (low thermal expansion material, EUV) substrates "
            "coated with chrome or multilayer Mo/Si reflective coating, patterned "
            "by e-beam writing. Each layer of each chip design requires a separate "
            "mask. EUV masks are reflective (not transmissive)."
        ),
        "used_in_steps": ["lithography_duv", "lithography_euv"],
        "availability": "specialized",
        "key_suppliers": [
            {"name": "Photronics", "country": "USA", "market_share": "~30%"},
            {"name": "Toppan Photomask", "country": "Japan", "market_share": "~25%"},
            {"name": "DNP (Dai Nippon Printing)", "country": "Japan", "market_share": "~20%"},
            {"name": "Hoya (blanks)", "country": "Japan", "market_share": "~40% of blanks",
             "notes": "Hoya dominates EUV mask blank supply"},
            {"name": "AGC (blanks)", "country": "Japan", "market_share": "~30% of blanks"},
            {"name": "Carl Zeiss (blank glass)", "country": "Germany", "market_share": "~30% of blanks"},
        ],
        "supply_risks": [
            "EUV mask blanks: Hoya and AGC control ~70% of supply from Japan",
            "Zeiss provides specialty glass substrate — another single-point concentration",
            "EUV mask patterning requires high-end e-beam writers (NuFlare, IMS)",
            "EUV mask repair/inspection tools are extremely limited",
        ],
        "export_controls": {
            "status": "partial",
            "detail": "Advanced EUV masks and blanks subject to export controls for restricted destinations.",
            "eccn": "3C905",
        },
        "grey_market_risk": "medium",
        "grey_market_detail": "Mask IP (design data) is more valuable than the physical mask; mask smuggling less common than IP theft.",
        "critical_mineral": False,
        "geographic_concentration": "Japan (blanks ~70%+); US + Japan (finished masks)",
        "hs_codes": ["3707.90", "9001.90"],
    },

    "neon_gas": {
        "name": "Neon Gas (Ultra-High Purity)",
        "aliases": ["Ne", "neon", "laser gas", "ArF laser gas blend"],
        "category": "gas",
        "description": (
            "Ultra-high-purity neon is the primary buffer gas in ArF excimer laser "
            "systems (193nm DUV scanners). The laser gas mixture is Ne/F2/Ar. "
            "Neon is produced as a byproduct of oxygen/nitrogen steel mill production "
            "and requires extensive purification to semiconductor grade (99.9999%)."
        ),
        "used_in_steps": ["lithography_duv"],
        "availability": "specialized",
        "key_suppliers": [
            {"name": "Ingas", "country": "Ukraine", "market_share": "~20% (pre-war ~35%)",
             "notes": "Mariupol plant damaged in 2022 conflict"},
            {"name": "Cryoin", "country": "Ukraine", "market_share": "~15% (pre-war ~25%)",
             "notes": "Odessa-based; operations disrupted"},
            {"name": "Air Products", "country": "USA", "market_share": "~20%",
             "notes": "Ramped production post-2022"},
            {"name": "Linde", "country": "Germany/USA", "market_share": "~15%"},
            {"name": "Air Liquide", "country": "France", "market_share": "~10%"},
            {"name": "Iceblick", "country": "Ukraine", "market_share": "~10%"},
        ],
        "supply_risks": [
            "Ukraine supplied ~50% of global ultra-high-purity neon pre-2022 invasion",
            "2022 crisis caused neon prices to spike 500%+; forced diversification",
            "Now diversifying to US, China, and other sources — concentration improving",
            "6–12 month buffer typically held by scanner manufacturers and gas suppliers",
        ],
        "export_controls": {
            "status": "none",
            "detail": "Neon gas itself is not export controlled (EAR99). Semiconductor-grade purification equipment may be.",
            "eccn": "EAR99",
        },
        "grey_market_risk": "low",
        "grey_market_detail": "Commodity gas with active global market post-Ukraine diversification; grey market risk low.",
        "critical_mineral": True,
        "geographic_concentration": "Ukraine historically dominant; now diversifying",
        "hs_codes": ["2804.29"],
    },

    "krypton_gas": {
        "name": "Krypton Gas (Ultra-High Purity)",
        "aliases": ["Kr", "krypton", "KrF laser gas"],
        "category": "gas",
        "description": (
            "Ultra-high-purity krypton used in KrF excimer lasers (248nm) for "
            "mature node DUV lithography. Also used in EUV scanner chamber flushing "
            "to prevent EUV beam absorption. Byproduct of air separation, similar "
            "supply chain to neon."
        ),
        "used_in_steps": ["lithography_duv", "lithography_euv"],
        "availability": "specialized",
        "key_suppliers": [
            {"name": "Air Products", "country": "USA", "market_share": "~25%"},
            {"name": "Linde", "country": "Germany/USA", "market_share": "~20%"},
            {"name": "Air Liquide", "country": "France", "market_share": "~20%"},
            {"name": "Various Ukrainian/Russian producers", "country": "Ukraine/Russia",
             "market_share": "~20% (pre-war)", "notes": "Supply disrupted by conflict"},
        ],
        "supply_risks": [
            "Byproduct of steel production — supply tied to industrial activity levels",
            "Ukraine/Russia historically significant producers",
            "Less concentrated than neon historically",
        ],
        "export_controls": {
            "status": "none",
            "detail": "Krypton gas is not export controlled (EAR99).",
            "eccn": "EAR99",
        },
        "grey_market_risk": "low",
        "grey_market_detail": "Commodity gas; grey market risk low.",
        "critical_mineral": True,
        "geographic_concentration": "Global production; historically Ukraine/Russia significant",
        "hs_codes": ["2804.29"],
    },

    "argon_gas_bulk": {
        "name": "Argon Gas (Bulk, Ultra-High Purity)",
        "aliases": ["Ar", "argon", "bulk argon", "process gas"],
        "category": "gas",
        "description": (
            "Bulk argon is the most widely used process gas in semiconductor fabs — "
            "used as carrier gas, sputter gas in PVD, plasma gas in etch, and purge "
            "gas throughout. Produced in massive quantities by air separation; "
            "delivered as liquid and vaporized on-site."
        ),
        "used_in_steps": [
            "wafer_prep", "lithography_duv", "etch_dry", "cvd_deposition",
            "ald", "pvd_sputtering", "ion_implant", "rtp_anneal", "cmp",
        ],
        "availability": "commodity",
        "key_suppliers": [
            {"name": "Air Products", "country": "USA", "market_share": "~25%"},
            {"name": "Linde", "country": "Germany/USA", "market_share": "~25%"},
            {"name": "Air Liquide", "country": "France", "market_share": "~20%"},
            {"name": "Nippon Sanso (Matheson)", "country": "Japan", "market_share": "~15%"},
            {"name": "Regional suppliers", "country": "Various", "market_share": "~15%"},
        ],
        "supply_risks": [
            "Commodity with multiple global suppliers; supply risk is low",
            "Local disruptions (plant outages, logistics) can cause short-term shortages",
            "On-site storage buffers typically cover 2–4 weeks of fab consumption",
        ],
        "export_controls": {
            "status": "none",
            "detail": "Argon gas is not export controlled (EAR99).",
            "eccn": "EAR99",
        },
        "grey_market_risk": "low",
        "grey_market_detail": "Commodity; no grey market risk.",
        "critical_mineral": False,
        "geographic_concentration": "Global; no concentration risk",
        "hs_codes": ["2804.21"],
    },

    "hf_acid_electronic": {
        "name": "Hydrofluoric Acid (Electronic Grade, Ultra-Pure)",
        "aliases": ["HF", "hydrofluoric acid", "HF acid", "buffered HF", "BHF", "dilute HF"],
        "category": "chemical",
        "description": (
            "Electronic-grade HF (50% aqueous and anhydrous) is used extensively "
            "for thermal oxide etch, native oxide removal (pre-gate clean), silicon "
            "surface passivation, and glass etching. Ultra-high purity (sub-ppt "
            "metal contamination) required. Highly corrosive and toxic — "
            "dual-use chemical under Chemical Weapons Convention (CWC)."
        ),
        "used_in_steps": ["etch_wet", "cmp", "wafer_prep"],
        "availability": "specialized",
        "key_suppliers": [
            {"name": "Stella Chemifa", "country": "Japan", "market_share": "~30%",
             "notes": "Leading supplier of ultra-high-purity electronic grade HF"},
            {"name": "Morita Chemical", "country": "Japan", "market_share": "~25%"},
            {"name": "Solvay", "country": "Belgium/USA", "market_share": "~20%"},
            {"name": "Honeywell", "country": "USA", "market_share": "~15%"},
        ],
        "supply_risks": [
            "Japanese suppliers dominate ultra-high-purity grade required for leading-edge fabs",
            "Dual-use CWC Schedule 3 chemical — subject to export reporting and controls",
            "HF production uses fluorspar (fluorite) as feedstock; China controls ~60% of global fluorspar",
            "2019 South Korea–Japan trade dispute caused temporary HF supply crisis for Korean fabs",
        ],
        "export_controls": {
            "status": "partial",
            "detail": (
                "Electronic-grade HF is a CWC Schedule 3 chemical. Requires export declarations "
                "and end-user certificates in most jurisdictions. US EAR: AT controls apply."
            ),
            "eccn": "1C350.d",
        },
        "grey_market_risk": "medium",
        "grey_market_detail": (
            "The 2019 Japan–Korea HF restrictions demonstrated how quickly supply disruptions "
            "drive informal procurement. HF's chemical nature makes it difficult to inspect; "
            "purity misrepresentation (selling standard grade as electronic grade) is a documented "
            "fraud in less-regulated supply chains."
        ),
        "critical_mineral": False,
        "geographic_concentration": "Japan ~55% of electronic grade",
        "hs_codes": ["2811.11"],
    },

    "cmp_slurry": {
        "name": "CMP Slurry (Oxide, Tungsten, Copper)",
        "aliases": ["polishing slurry", "CMP abrasive", "STI slurry", "W slurry", "Cu slurry", "ceria slurry"],
        "category": "chemical",
        "description": (
            "Colloidal suspensions of abrasive particles (ceria CeO2, silica SiO2, "
            "alumina Al2O3) in a chemical solution tailored to selectively remove "
            "specific films during CMP. Each application (STI oxide, W contact, "
            "Cu BEOL, low-k) requires a purpose-formulated slurry."
        ),
        "used_in_steps": ["cmp", "metallization_cu", "metallization_w"],
        "availability": "specialized",
        "key_suppliers": [
            {"name": "CMC Materials (formerly Cabot)", "country": "USA", "market_share": "~35%"},
            {"name": "Versum Materials (Merck KGaA)", "country": "Germany/USA", "market_share": "~20%"},
            {"name": "DuPont Electronic Materials", "country": "USA", "market_share": "~15%"},
            {"name": "Fujimi", "country": "Japan", "market_share": "~15%"},
            {"name": "Nitta Haas", "country": "Japan", "market_share": "~10%"},
        ],
        "supply_risks": [
            "Ceria (CeO2) feedstock: China controls ~60% of rare earth production",
            "Slurry formulations are highly proprietary; switching suppliers requires re-qualification",
            "Particle size consistency is critical — contamination causes yield loss",
        ],
        "export_controls": {
            "status": "none",
            "detail": "CMP slurries are generally EAR99 and not export controlled.",
            "eccn": "EAR99",
        },
        "grey_market_risk": "low",
        "grey_market_detail": "Consumable; multiple suppliers; low grey market risk. Counterfeit slurries (spec misrepresentation) documented in lower-tier fabs.",
        "critical_mineral": False,
        "geographic_concentration": "USA ~65%, Japan ~25%, Germany ~10%",
        "hs_codes": ["3824.99"],
    },

    "cmp_polishing_pad": {
        "name": "CMP Polishing Pad",
        "aliases": ["polishing pad", "CMP pad", "IC1000 pad", "Dow pad"],
        "category": "material",
        "description": (
            "Polyurethane foam pads used in CMP to mechanically abrade the wafer "
            "surface in the presence of slurry. Pad conditioning (using diamond-"
            "embedded discs) restores surface texture during and between wafer polishes. "
            "Pad-slurry-tool interaction must be co-optimized."
        ),
        "used_in_steps": ["cmp"],
        "availability": "specialized",
        "key_suppliers": [
            {"name": "DuPont (Dow Chemical legacy)", "country": "USA", "market_share": "~60%",
             "notes": "IC1000 pad is industry standard; very high market share"},
            {"name": "CMC Materials", "country": "USA", "market_share": "~20%"},
            {"name": "Fujibo Holdings", "country": "Japan", "market_share": "~15%"},
        ],
        "supply_risks": [
            "DuPont near-monopoly on the IC1000 standard pad — limited alternatives",
            "Pad qualification takes 6–12 months per application",
        ],
        "export_controls": {
            "status": "none",
            "detail": "Polishing pads are EAR99 and not export controlled.",
            "eccn": "EAR99",
        },
        "grey_market_risk": "low",
        "grey_market_detail": "Consumable with few alternatives; counterfeit pads (inferior quality) documented.",
        "critical_mineral": False,
        "geographic_concentration": "USA dominant (~80%)",
        "hs_codes": ["3926.90"],
    },

    # -----------------------------------------------------------------------
    # Critical Minerals and Specialty Materials
    # -----------------------------------------------------------------------

    "gallium": {
        "name": "Gallium (Refined, Semiconductor Grade)",
        "aliases": ["Ga", "gallium metal", "gallium arsenide substrate", "GaAs", "GaN", "gallium nitride"],
        "category": "critical_mineral",
        "description": (
            "Gallium is a byproduct of aluminum refining (bauxite processing). "
            "Used in III-V compound semiconductors: GaAs (RF chips, solar cells), "
            "GaN (power electronics, 5G RF, LEDs), and InGaP (HBT devices). "
            "China controls ~80% of global refined gallium production."
        ),
        "used_in_steps": ["cvd_deposition", "ald", "pvd_sputtering"],
        "availability": "specialized",
        "key_suppliers": [
            {"name": "China (multiple state-linked producers)", "country": "China",
             "market_share": "~80%", "notes": "Zijin Mining, Aluminum Corporation of China (Chalco)"},
            {"name": "Recylex / Nyrstar", "country": "Germany/Belgium", "market_share": "~8%"},
            {"name": "Dowa Holdings", "country": "Japan", "market_share": "~5%"},
            {"name": "US Geological Survey notes no primary US production", "country": "USA",
             "market_share": "0%", "notes": "US recycling only"},
        ],
        "supply_risks": [
            "China export restrictions effective August 1, 2023 (license required for gallium exports)",
            "Near-total dependence on China for primary supply",
            "Stockpiling behavior documented post-restriction announcement",
            "Alternative sources being developed (Russia, Germany, South Korea) but scale is limited",
        ],
        "export_controls": {
            "status": "strict",
            "detail": (
                "China's Ministry of Commerce imposed export license requirements on gallium "
                "metal and gallium compounds effective August 1, 2023. US/EU list it as "
                "a critical mineral; no US export control on gallium itself, but the "
                "import dependence on China is the critical risk."
            ),
            "eccn": "EAR99 (US export); China imposes import controls",
        },
        "grey_market_risk": "high",
        "grey_market_detail": (
            "Post-August 2023 Chinese export restrictions drove significant grey market activity. "
            "Reports of informal export channels through Hong Kong, Vietnam, and other "
            "intermediary countries. Price premiums of 30–50% documented on spot market "
            "for non-licensed supply. Criminal networks are actively exploiting supply anxiety."
        ),
        "critical_mineral": True,
        "geographic_concentration": "China ~80% of refined supply",
        "hs_codes": ["2805.30"],
    },

    "germanium": {
        "name": "Germanium (Refined, Semiconductor Grade)",
        "aliases": ["Ge", "germanium", "SiGe", "silicon germanium", "germanium substrate"],
        "category": "critical_mineral",
        "description": (
            "Germanium is recovered as a byproduct of zinc smelting and coal fly ash. "
            "Used in silicon-germanium (SiGe) strained channel layers in FinFET and "
            "GAA transistors, III-V substrates (GaAs epi), germanium photodetectors, "
            "and fiber optic glass (GeO2)."
        ),
        "used_in_steps": ["ald", "cvd_deposition", "epitaxy" if "epitaxy" else "cvd_deposition"],
        "availability": "specialized",
        "key_suppliers": [
            {"name": "China (multiple producers)", "country": "China",
             "market_share": "~60%", "notes": "Yunnan Chihong Zinc & Germanium dominant"},
            {"name": "Umicore", "country": "Belgium", "market_share": "~15%"},
            {"name": "Teck Resources", "country": "Canada", "market_share": "~8%"},
            {"name": "Indium Corporation", "country": "USA", "market_share": "~5%"},
        ],
        "supply_risks": [
            "China export restrictions effective August 1, 2023 (same regulation as gallium)",
            "Fiber optics and solar demand compete with semiconductor demand",
            "Limited non-Chinese refining capacity",
        ],
        "export_controls": {
            "status": "strict",
            "detail": (
                "China imposed export license requirements on germanium and germanium "
                "compounds effective August 1, 2023, alongside gallium restrictions."
            ),
            "eccn": "EAR99 (US export)",
        },
        "grey_market_risk": "high",
        "grey_market_detail": (
            "Same informal export patterns as gallium post-August 2023. Germanium "
            "compounds are harder to detect at customs than metal. Reports of "
            "misclassified exports to evade licensing requirements."
        ),
        "critical_mineral": True,
        "geographic_concentration": "China ~60%",
        "hs_codes": ["2804.50"],
    },

    "cobalt": {
        "name": "Cobalt (Refined)",
        "aliases": ["Co", "cobalt", "cobalt liner", "cobalt silicide", "CoSi2"],
        "category": "critical_mineral",
        "description": (
            "Cobalt is used in semiconductor manufacturing as a contact liner "
            "material (replacing Ti/TiN at leading-edge nodes), cobalt silicide "
            "(CoSi2) for low-resistance contacts, and as CoWP capping layer on "
            "copper interconnects. DRC supplies ~70% of global cobalt mine production."
        ),
        "used_in_steps": ["pvd_sputtering", "metallization_cu", "ald"],
        "availability": "specialized",
        "key_suppliers": [
            {"name": "DRC (multiple artisanal and industrial mines)", "country": "Democratic Republic of Congo",
             "market_share": "~70% of mining", "notes": "Glencore, China Molybdenum (CMOC) dominant operators"},
            {"name": "Umicore", "country": "Belgium", "market_share": "~15% of refining"},
            {"name": "Freeport Cobalt", "country": "Finland", "market_share": "~10% of refining"},
            {"name": "Jien Mining", "country": "China", "market_share": "growing refining share"},
        ],
        "supply_risks": [
            "DRC political instability, conflict, and governance risk",
            "Artisanal small-scale mining (~20% of DRC production) creates human rights and supply chain integrity issues",
            "Battery demand (EVs) competing with electronics — price and allocation pressure",
            "China controls an increasing share of DRC mine operations and global refining",
        ],
        "export_controls": {
            "status": "none",
            "detail": "Cobalt is not export controlled in the traditional sense, but conflict mineral due diligence (Dodd-Frank, EU Conflict Minerals Regulation) applies.",
            "eccn": "EAR99",
        },
        "grey_market_risk": "medium",
        "grey_market_detail": (
            "Artisanal cobalt mining creates parallel informal supply chains. "
            "Smuggling of unrefined cobalt from DRC through Rwanda and Uganda to "
            "avoid taxation and traceability requirements is well-documented by "
            "Global Witness and OECD. Material may enter legitimate supply chains "
            "through unscrupulous traders."
        ),
        "critical_mineral": True,
        "geographic_concentration": "DRC ~70% of mining; China growing refining share",
        "hs_codes": ["2605.00", "8105.20"],
    },

    "ruthenium": {
        "name": "Ruthenium (Refined)",
        "aliases": ["Ru", "ruthenium", "Ru liner", "Ru barrier"],
        "category": "critical_mineral",
        "description": (
            "Ruthenium (a platinum group metal, PGM) is emerging as a copper "
            "interconnect liner and potential replacement metal at sub-2nm nodes "
            "where copper's resistivity becomes unacceptable at narrow linewidths. "
            "Also used in MRAM magnetic tunnel junctions and DRAM capacitor electrodes."
        ),
        "used_in_steps": ["pvd_sputtering", "ald", "metallization_cu"],
        "availability": "specialized",
        "key_suppliers": [
            {"name": "Anglo American Platinum", "country": "South Africa", "market_share": "~40%"},
            {"name": "Impala Platinum (Implats)", "country": "South Africa", "market_share": "~25%"},
            {"name": "Norilsk Nickel", "country": "Russia", "market_share": "~15%",
             "notes": "Under Western sanctions since 2022 — supply access disrupted for sanctioned entities"},
            {"name": "Sibanye-Stillwater", "country": "South Africa/USA", "market_share": "~10%"},
        ],
        "supply_risks": [
            "South Africa supplies ~90% of global PGM including ruthenium",
            "Power outages (load shedding) in South Africa repeatedly disrupt PGM mining",
            "Russian supply (Norilsk Nickel) inaccessible to Western buyers under sanctions",
            "Semiconductor demand growing but ruthenium is a small PGM market — price volatile",
        ],
        "export_controls": {
            "status": "none",
            "detail": "Ruthenium is not export controlled (EAR99). Russian supply subject to sanctions.",
            "eccn": "EAR99",
        },
        "grey_market_risk": "medium",
        "grey_market_detail": (
            "Russian sanctions have created pressure on Norilsk Nickel ruthenium supply. "
            "Some evidence of sanctions circumvention through third-country traders for "
            "PGMs generally. South African production risk from electricity/labor instability "
            "drives speculative stockpiling."
        ),
        "critical_mineral": True,
        "geographic_concentration": "South Africa ~90% of PGM production",
        "hs_codes": ["7112.92", "2616.90"],
    },

    "indium": {
        "name": "Indium (Refined)",
        "aliases": ["In", "indium", "ITO", "InGaAs", "indium tin oxide", "InP"],
        "category": "critical_mineral",
        "description": (
            "Indium is produced as a byproduct of zinc smelting. Used in "
            "indium tin oxide (ITO) for transparent electrodes, InGaAs/InP "
            "III-V devices (HEMT, laser, photodetector), and advanced CMOS "
            "channels (InGaAs replacing Si in some III-V logic proposals)."
        ),
        "used_in_steps": ["pvd_sputtering", "cvd_deposition"],
        "availability": "specialized",
        "key_suppliers": [
            {"name": "China (multiple)", "country": "China", "market_share": "~55%"},
            {"name": "South Korea", "country": "South Korea", "market_share": "~15%"},
            {"name": "Japan", "country": "Japan", "market_share": "~10%"},
            {"name": "Canada", "country": "Canada", "market_share": "~8%"},
        ],
        "supply_risks": [
            "China controls majority of global indium refining",
            "Zinc mine output decline reduces indium byproduct availability",
            "ITO recycling recovering significant amounts, easing primary supply pressure",
        ],
        "export_controls": {
            "status": "none",
            "detail": "Indium is not export controlled in the US (EAR99). China has it on critical mineral watch lists.",
            "eccn": "EAR99",
        },
        "grey_market_risk": "low",
        "grey_market_detail": "Lower supply risk than gallium/germanium; grey market pressure is modest.",
        "critical_mineral": True,
        "geographic_concentration": "China ~55%, South Korea ~15%",
        "hs_codes": ["2620.99", "8112.92"],
    },

    "tantalum": {
        "name": "Tantalum (Refined)",
        "aliases": ["Ta", "tantalum", "TaN", "tantalum nitride", "Ta barrier", "conflict mineral"],
        "category": "critical_mineral",
        "description": (
            "Tantalum is used as a diffusion barrier (TaN/Ta bilayer) in copper "
            "interconnects to prevent Cu diffusion into silicon. Also used in "
            "tantalum capacitors (distinct from semiconductor tantalum). "
            "Primary ore is coltan (columbite-tantalite), predominantly from DRC and Rwanda."
        ),
        "used_in_steps": ["pvd_sputtering", "ald", "metallization_cu"],
        "availability": "specialized",
        "key_suppliers": [
            {"name": "DRC/Rwanda (artisanal + industrial)", "country": "Democratic Republic of Congo / Rwanda",
             "market_share": "~40% of mining"},
            {"name": "Australia (Global Advanced Metals)", "country": "Australia", "market_share": "~25%"},
            {"name": "Brazil", "country": "Brazil", "market_share": "~10%"},
            {"name": "H.C. Starck (Materion)", "country": "Germany/USA", "market_share": "~30% of refining"},
        ],
        "supply_risks": [
            "DRC conflict mineral — Dodd-Frank Section 1502 and EU Conflict Minerals Regulation apply",
            "Supply chain traceability from mine to fab is difficult and costly",
            "DRC conflict financing through mineral trade documented by UN Panel of Experts",
        ],
        "export_controls": {
            "status": "none",
            "detail": "Tantalum is not export controlled, but conflict mineral due diligence reporting is mandatory for US SEC registrants.",
            "eccn": "EAR99",
        },
        "grey_market_risk": "medium",
        "grey_market_detail": (
            "DRC tantalum frequently enters global supply chains with falsified provenance "
            "documentation. Armed groups finance operations through coltan taxation. "
            "The formal supply chain certification (iTSCi, RMI) covers a minority of "
            "actual production."
        ),
        "critical_mineral": True,
        "geographic_concentration": "DRC/Rwanda ~40% of mining; Australia ~25%",
        "hs_codes": ["2615.90", "8103.20"],
    },

    "tungsten": {
        "name": "Tungsten (Refined)",
        "aliases": ["W", "tungsten", "WF6", "tungsten hexafluoride", "W plug", "tungsten contact"],
        "category": "critical_mineral",
        "description": (
            "Tungsten has the highest melting point of all metals and exceptional "
            "thermal stability. Used in semiconductor fabs as tungsten CVD contact "
            "fill (via WF6 precursor), W PVD targets for TiW adhesion layers, and "
            "wolfram carbide for CMP conditioner discs."
        ),
        "used_in_steps": ["metallization_w", "cmp"],
        "availability": "specialized",
        "key_suppliers": [
            {"name": "China (multiple, state-linked)", "country": "China",
             "market_share": "~83% of mining", "notes": "Jiangxi Tungsten dominant"},
            {"name": "Vietnam", "country": "Vietnam", "market_share": "~5%"},
            {"name": "Russia", "country": "Russia", "market_share": "~3%"},
            {"name": "H.C. Starck (Materion)", "country": "Germany", "market_share": "significant refining share"},
        ],
        "supply_risks": [
            "China controls ~83% of global tungsten mining and significant refining",
            "China classified tungsten as a critical strategic mineral in 2023",
            "WF6 (gas precursor) supply chain is an additional step — limited producers",
        ],
        "export_controls": {
            "status": "partial",
            "detail": "Tungsten is not currently export controlled under US EAR, but China's 2023 strategic mineral designation raises future restriction risk. WF6 may have AT controls.",
            "eccn": "EAR99 (tungsten metal); WF6 may require review",
        },
        "grey_market_risk": "low",
        "grey_market_detail": "Less acute grey market pressure than gallium/germanium; broader Western supply base for refining.",
        "critical_mineral": True,
        "geographic_concentration": "China ~83% of mining",
        "hs_codes": ["2611.00", "8101.94"],
    },

    "hafnium": {
        "name": "Hafnium (Refined)",
        "aliases": ["Hf", "hafnium", "HfO2", "hafnium oxide", "high-k dielectric", "HfSiO4"],
        "category": "critical_mineral",
        "description": (
            "Hafnium is a byproduct of zirconium refining. HfO2 is the industry-"
            "standard high-k gate dielectric (replacing SiO2 from 45nm onwards) "
            "in all leading-edge CMOS devices, deposited by ALD. Also used in "
            "nuclear reactor control rods, creating competing demand."
        ),
        "used_in_steps": ["ald"],
        "availability": "specialized",
        "key_suppliers": [
            {"name": "Orano (Framatome)", "country": "France", "market_share": "~30%",
             "notes": "Major zirconium/hafnium refiner; nuclear industry focus"},
            {"name": "ATI (Allegheny Technologies)", "country": "USA", "market_share": "~20%"},
            {"name": "Chepetsky (TVEL Rosatom)", "country": "Russia", "market_share": "~20%",
             "notes": "Sanctions risk for Western buyers since 2022"},
            {"name": "China National Nuclear (CNNC)", "country": "China", "market_share": "~15%"},
        ],
        "supply_risks": [
            "Byproduct of zirconium — production rate tied to nuclear industry demand",
            "Russian supply (Rosatom subsidiary) inaccessible under Western sanctions",
            "Nuclear industry and semiconductor industry compete for limited supply",
            "Few primary hafnium refiners globally",
        ],
        "export_controls": {
            "status": "partial",
            "detail": "Hafnium is export controlled (ECCN 1C234) due to nuclear applications. Requires license for some destinations.",
            "eccn": "1C234",
        },
        "grey_market_risk": "medium",
        "grey_market_detail": (
            "Nuclear dual-use creates export control complexity. Russian supply sanctions "
            "have created price pressure. Limited documented semiconductor-specific grey "
            "market activity, but nuclear control complexity creates compliance risk."
        ),
        "critical_mineral": True,
        "geographic_concentration": "France ~30%, USA ~20%, Russia ~20% (sanctioned)",
        "hs_codes": ["2615.90", "8109.20"],
    },

    "tin_euv_target": {
        "name": "Tin (Sn) — EUV Plasma Target",
        "aliases": ["Sn", "tin", "tin droplet", "EUV source tin", "LPP tin"],
        "category": "material",
        "description": (
            "In EUV light sources, CO2 laser pulses vaporize microscopic tin "
            "droplets to create a plasma that emits 13.5nm EUV radiation. "
            "Requires ultra-high-purity tin delivered as micro-droplets at "
            "~50,000 droplets/second. Tin itself is not scarce, but the "
            "purification and delivery system are specialized."
        ),
        "used_in_steps": ["lithography_euv"],
        "availability": "specialized",
        "key_suppliers": [
            {"name": "ASML/Cymer (integrated supply)", "country": "Netherlands/USA",
             "market_share": "~100% of EUV-grade", "notes": "Tin supply integrated into EUV system service contract"},
            {"name": "China (primary tin mining)", "country": "China", "market_share": "~40% of global tin mining"},
            {"name": "Indonesia", "country": "Indonesia", "market_share": "~25% of global tin"},
            {"name": "Myanmar", "country": "Myanmar", "market_share": "~15%", "notes": "Military junta governance risk"},
        ],
        "supply_risks": [
            "EUV-grade tin supply is vertically integrated into ASML service — not an independent market",
            "Raw tin primary supply: China/Indonesia/Myanmar concentration",
            "Myanmar tin supply (Wa State, Man Maw mine) involves armed group territory",
        ],
        "export_controls": {
            "status": "none",
            "detail": "Tin itself is not export controlled. EUV system service (which includes tin supply) subject to ASML export license.",
            "eccn": "EAR99",
        },
        "grey_market_risk": "low",
        "grey_market_detail": "EUV-grade tin integrated into ASML service contract; grey market for raw tin exists but is not relevant to fab operations.",
        "critical_mineral": False,
        "geographic_concentration": "Raw tin: China ~40%, Indonesia ~25%, Myanmar ~15%",
        "hs_codes": ["8001.10"],
    },

    "ald_precursors_metal": {
        "name": "ALD Precursors (Metal Organic, Specialty Gas)",
        "aliases": [
            "TMA", "trimethylaluminum", "TDMAT", "TDMAT hafnium", "HfCl4",
            "TiCl4", "TEMAH", "WF6 ALD", "organometallic precursor", "ALD chemical",
        ],
        "category": "chemical",
        "description": (
            "ALD requires highly reactive, volatile metal-organic or halide precursors "
            "that chemisorb to the wafer surface in a self-limiting manner. Key examples: "
            "trimethylaluminum (TMA) for Al2O3, TDMAT/HfCl4 for HfO2 high-k, "
            "TiCl4 for TiN, WF6 for W ALD. Extreme purity and stability required."
        ),
        "used_in_steps": ["ald", "cvd_deposition"],
        "availability": "specialized",
        "key_suppliers": [
            {"name": "Entegris", "country": "USA", "market_share": "~30%"},
            {"name": "Merck KGaA (Sigma-Aldrich / Versum)", "country": "Germany", "market_share": "~25%"},
            {"name": "Air Liquide (SEMIGAS)", "country": "France", "market_share": "~15%"},
            {"name": "Strem Chemicals / STREM", "country": "USA", "market_share": "~10%"},
            {"name": "Tanaka (precious metal precursors)", "country": "Japan", "market_share": "~10%"},
        ],
        "supply_risks": [
            "Each new precursor requires 12–24 months of fab qualification",
            "Specialty organometallic synthesis is done by few companies globally",
            "Precursor supply disruptions can halt ALD processes across a fab",
            "Some precursors contain controlled metals (Hf, Ru, Ir) with their own supply risks",
        ],
        "export_controls": {
            "status": "partial",
            "detail": "Some ALD precursors (Hf, Ta compounds) are export controlled. Organometallic chemicals generally reviewed case by case.",
            "eccn": "Varies by precursor; 1C350 or 3C006 categories possible",
        },
        "grey_market_risk": "low",
        "grey_market_detail": "Specialized chemicals requiring fab qualification; limited grey market pressure.",
        "critical_mineral": False,
        "geographic_concentration": "USA + Germany + France + Japan",
        "hs_codes": ["2931.90", "2812.90"],
    },

    # -----------------------------------------------------------------------
    # Specialty Chemicals
    # -----------------------------------------------------------------------

    "wf6_tungsten_hex": {
        "name": "Tungsten Hexafluoride (WF6)",
        "aliases": ["WF6", "tungsten hexafluoride", "tungsten CVD precursor"],
        "category": "chemical",
        "description": (
            "WF6 is the primary precursor for CVD tungsten deposition in contact "
            "and via fill. Reacts with SiH4 or H2 at elevated temperature to "
            "deposit tungsten metal. Highly corrosive and toxic. Produced by "
            "fluorination of tungsten metal."
        ),
        "used_in_steps": ["metallization_w"],
        "availability": "specialized",
        "key_suppliers": [
            {"name": "Linde (formerly Praxair)", "country": "USA/Germany", "market_share": "~35%"},
            {"name": "Air Products", "country": "USA", "market_share": "~30%"},
            {"name": "Central Glass", "country": "Japan", "market_share": "~20%"},
            {"name": "Kanto Denka Kogyo", "country": "Japan", "market_share": "~10%"},
        ],
        "supply_risks": [
            "WF6 is derived from tungsten metal — Chinese tungsten supply chain concentration risk propagates",
            "Highly corrosive specialty gas; limited number of qualified producers",
            "Transport and storage require specialized handling infrastructure",
        ],
        "export_controls": {
            "status": "partial",
            "detail": "WF6 is a corrosive specialty gas. May be subject to AT controls under US EAR. Requires end-user certificate in some jurisdictions.",
            "eccn": "1C350 (chemical aspect)",
        },
        "grey_market_risk": "low",
        "grey_market_detail": "Specialized chemical; limited grey market. Supply risk primarily from upstream tungsten concentration.",
        "critical_mineral": False,
        "geographic_concentration": "USA + Japan",
        "hs_codes": ["2812.19"],
    },

    "specialty_etch_gases": {
        "name": "Specialty Etch Gases (Cl2, HBr, NF3, CF4, SF6, C4F8)",
        "aliases": [
            "Cl2", "chlorine gas", "HBr", "hydrogen bromide", "NF3", "nitrogen trifluoride",
            "CF4", "carbon tetrafluoride", "SF6", "sulfur hexafluoride", "C4F8", "etch gas",
        ],
        "category": "gas",
        "description": (
            "Halogen-containing gases used in plasma etch chambers. Cl2 and HBr "
            "for silicon/polysilicon etch; CF4, C4F8, C4F6 for dielectric etch; "
            "NF3 for chamber cleaning; SF6 for silicon deep etch. Each requires "
            "ultra-high purity and abatement systems."
        ),
        "used_in_steps": ["etch_dry"],
        "availability": "specialized",
        "key_suppliers": [
            {"name": "Linde", "country": "USA/Germany", "market_share": "~25%"},
            {"name": "Air Products", "country": "USA", "market_share": "~20%"},
            {"name": "Air Liquide", "country": "France", "market_share": "~20%"},
            {"name": "Showa Denko", "country": "Japan", "market_share": "~15%",
             "notes": "Major NF3 and C4F8 producer"},
            {"name": "Kanto Denka", "country": "Japan", "market_share": "~10%"},
        ],
        "supply_risks": [
            "NF3: Showa Denko (Japan) dominant; South Korean capacity growing",
            "SF6 and C4F8 are potent greenhouse gases subject to environmental regulation",
            "Chlorine supply tied to chlor-alkali industry capacity",
            "2019 Japan export controls on HF/HBr/poly-imide to Korea impacted Samsung/SK Hynix",
        ],
        "export_controls": {
            "status": "partial",
            "detail": "Some etch gases (Cl2, HBr) may be subject to CWC reporting. NF3 is not controlled but SF6 has environmental agreements (Kyoto Protocol).",
            "eccn": "1C350 for some halogens",
        },
        "grey_market_risk": "low",
        "grey_market_detail": "Multiple global suppliers; grey market pressure low for most etch gases.",
        "critical_mineral": False,
        "geographic_concentration": "USA + Japan + Germany + France (diversified)",
        "hs_codes": ["2812.11", "2812.12", "2812.19", "2901.19"],
    },

    "copper_sulfate_ecd": {
        "name": "Copper Sulfate Electroplating Bath (ECD)",
        "aliases": ["CuSO4", "copper plating", "ECD chemistry", "electrochemical deposition"],
        "category": "chemical",
        "description": (
            "Copper electrochemical deposition (ECD) fills damascene trenches and "
            "vias with copper to form interconnects. The plating bath contains "
            "CuSO4, H2SO4, Cl- ions, and proprietary organic additives (accelerators, "
            "suppressors, levelers) that control grain structure and fill profile."
        ),
        "used_in_steps": ["metallization_cu"],
        "availability": "specialized",
        "key_suppliers": [
            {"name": "MacDermid Enthone (Element Solutions)", "country": "USA", "market_share": "~35%",
             "notes": "Proprietary additive packages are highly process-specific"},
            {"name": "Atotech (MKS Instruments)", "country": "Germany/USA", "market_share": "~30%"},
            {"name": "Rohm and Haas (Dow)", "country": "USA", "market_share": "~20%"},
        ],
        "supply_risks": [
            "Organic additive formulations are highly proprietary; switching requires extensive requalification",
            "Copper metal itself is commodity; additive chemistry is the value-add",
        ],
        "export_controls": {
            "status": "none",
            "detail": "CuSO4 and standard additives are EAR99. Proprietary process additive formulas are trade secrets but not export controlled.",
            "eccn": "EAR99",
        },
        "grey_market_risk": "low",
        "grey_market_detail": "Commodity chemicals; low grey market pressure.",
        "critical_mineral": False,
        "geographic_concentration": "USA + Germany",
        "hs_codes": ["2833.25", "2804.11"],
    },

    "photomask_blanks": {
        "name": "EUV Photomask Blanks (LTEM Substrate with Mo/Si Multilayer)",
        "aliases": ["mask blank", "EUV blank", "LTEM substrate", "TaN absorber blank"],
        "category": "material",
        "description": (
            "EUV masks are made on low thermal expansion material (LTEM) glass substrates "
            "coated with 40 alternating Mo/Si layers (deposited by magnetron sputtering) "
            "to form a Bragg reflector. A TaN absorber layer is then deposited for "
            "patterning. Zeiss, Hoya, and AGC dominate this very specialized market."
        ),
        "used_in_steps": ["lithography_euv"],
        "availability": "single_source",
        "key_suppliers": [
            {"name": "Hoya", "country": "Japan", "market_share": "~40%",
             "notes": "Dominant EUV mask blank supplier"},
            {"name": "AGC (Asahi Glass)", "country": "Japan", "market_share": "~30%"},
            {"name": "Carl Zeiss (LTEM glass)", "country": "Germany", "market_share": "~30% of glass substrates",
             "notes": "Zeiss provides the LTEM Clearceram-Z glass that others coat"},
        ],
        "supply_risks": [
            "Japan controls ~70% of finished EUV blank supply",
            "Zeiss glass substrate adds a German single-point dependency",
            "Blank yield and defect levels are critical — even one subnm defect ruins a blank",
            "EUV blank capacity is extremely limited; qualification for new suppliers takes years",
        ],
        "export_controls": {
            "status": "strict",
            "detail": "EUV mask blanks controlled under Japanese and Dutch export regulations. Cannot be exported to China under current controls.",
            "eccn": "3C905",
        },
        "grey_market_risk": "medium",
        "grey_market_detail": (
            "EUV blanks cannot function without the corresponding EUV scanner and resist; "
            "grey market limited by this dependency. However, attempts to acquire blanks "
            "ahead of acquiring scanners have been documented as hedging behavior."
        ),
        "critical_mineral": False,
        "geographic_concentration": "Japan ~70%, Germany ~30% (glass)",
        "hs_codes": ["3707.90", "9001.90"],
    },
}


# ---------------------------------------------------------------------------
# Search function
# ---------------------------------------------------------------------------

def search(query: str) -> dict:
    """Return top matching components and process steps for a query.

    Scoring:
      +10  query is substring of component name (case-insensitive)
      +8   query matches an alias
      +5   individual word matches component name
      +4   individual word matches an alias
      +3   query is substring of description
      +2   individual word matches description
    """
    q = query.strip().lower()
    words = [w for w in q.split() if len(w) > 2]

    component_scores: dict[str, int] = {}
    for cid, comp in COMPONENTS.items():
        score = 0
        name_l = comp["name"].lower()
        desc_l = comp.get("description", "").lower()
        aliases_l = [a.lower() for a in comp.get("aliases", [])]

        if q in name_l:
            score += 10
        for alias in aliases_l:
            if q in alias or alias in q:
                score += 8
                break
        if q in desc_l:
            score += 3

        for word in words:
            if word in name_l:
                score += 5
            for alias in aliases_l:
                if word in alias:
                    score += 4
                    break
            if word in desc_l:
                score += 2

        if score > 0:
            component_scores[cid] = score

    step_scores: dict[str, int] = {}
    for sid, step in PROCESS_STEPS.items():
        score = 0
        name_l = step["name"].lower()
        desc_l = step.get("description", "").lower()
        if q in name_l:
            score += 10
        if q in desc_l:
            score += 3
        for word in words:
            if word in name_l:
                score += 5
            if word in desc_l:
                score += 2
        if score > 0:
            step_scores[sid] = score

    top_components = sorted(component_scores.items(), key=lambda x: x[1], reverse=True)[:5]
    top_steps = sorted(step_scores.items(), key=lambda x: x[1], reverse=True)[:3]

    return {
        "query": query,
        "components": [
            {**COMPONENTS[cid], "id": cid, "_score": score}
            for cid, score in top_components
        ],
        "process_steps": [
            {
                **PROCESS_STEPS[sid],
                "id": sid,
                "_score": score,
                "components": [
                    {"id": cid, "name": COMPONENTS[cid]["name"],
                     "availability": COMPONENTS[cid]["availability"]}
                    for cid in PROCESS_STEPS[sid].get("component_ids", [])
                    if cid in COMPONENTS
                ],
            }
            for sid, score in top_steps
        ],
    }
