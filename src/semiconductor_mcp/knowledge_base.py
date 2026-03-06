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
            "highpurity_filters_pou", "upw_system_components", "ipa_electronic_grade",
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
        "component_ids": ["argon_gas_bulk", "cvd_system", "quartz_process_components"],
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
            "barc_coating", "duv_pellicle", "hmds_adhesion_promoter",
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
            "electrostatic_chuck", "ceramic_chamber_components",
            "mfc_mass_flow_controller", "perfluoroelastomer_seals",
            "gas_abatement_systems",
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
        "component_ids": [
            "hf_acid_electronic", "argon_gas_bulk",
            "buffered_hf_boe", "tmah_developer",
            "highpurity_filters_pou", "upw_system_components", "ipa_electronic_grade",
        ],
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
            "argon_gas_bulk", "teos_cvd_precursor", "silane_sih4",
            "mfc_mass_flow_controller", "specialty_gas_purifiers",
            "ceramic_chamber_components", "gas_abatement_systems",
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
            "argon_gas_bulk", "mfc_mass_flow_controller", "specialty_gas_purifiers",
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
            "electrostatic_chuck", "ceramic_chamber_components",
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
            "hf_acid_electronic", "cmp_conditioner_disc",
            "highpurity_filters_pou", "upw_system_components",
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
    "wafer_dicing": {
        "name": "Wafer Dicing & Singulation",
        "category": "back_end",
        "description": (
            "Mechanical or laser dicing to separate individual dies from the "
            "finished wafer. Blade dicing uses diamond or CBN blades at high "
            "rotational speed with DI water cooling. Stealth dicing (laser) used "
            "for thin wafers and hard materials. Yield impact is significant — "
            "chipping and cracking at die edges is a primary failure mode."
        ),
        "node_applicability": ["all nodes"],
        "component_ids": ["wafer_dicing_blades"],
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

    # -----------------------------------------------------------------------
    # Process-Critical Consumables
    # -----------------------------------------------------------------------

    "highpurity_filters_pou": {
        "name": "High-Purity Point-of-Use Filters",
        "aliases": ["POU filter", "point of use filter", "process filter", "in-line filter", "membrane filter", "PTFE filter", "UPW filter", "photoresist filter", "chemical filter"],
        "category": "process_consumable",
        "description": (
            "Membrane filtration devices installed at the point of chemical or "
            "gas delivery to remove particulates, gel particles, and microbial "
            "contamination immediately before contact with the wafer. Used across "
            "virtually every wet process: photoresist delivery, CMP slurry supply, "
            "UPW polishing loops, chemical dispensing, and immersion lithography "
            "water systems. Filter membranes are PTFE, PVDF, UPE, or nylon "
            "depending on chemical compatibility. Pore sizes range from 0.003µm "
            "(ultrafiltration) to 0.1µm (standard). A single particle breach can "
            "kill an entire wafer lot — filter integrity is yield-critical."
        ),
        "used_in_steps": ["wafer_prep", "etch_wet", "lithography_duv", "lithography_euv", "cvd_deposition", "cmp"],
        "availability": "specialized",
        "key_suppliers": [
            {"name": "Entegris", "country": "USA", "market_share": "~50%",
             "notes": "Mykrolis brand; dominant in advanced node photoresist and chemical filtration"},
            {"name": "Pall Corporation (Danaher)", "country": "USA", "market_share": "~25%",
             "notes": "Ultipor and Supor membrane series; strong in UPW and bulk chemical"},
            {"name": "Parker Hannifin", "country": "USA", "market_share": "~12%",
             "notes": "domnick hunter semiconductor series"},
            {"name": "Porvair Filtration", "country": "UK", "market_share": "~5%",
             "notes": "Specialist in high-purity gas and liquid filtration"},
        ],
        "supply_risks": [
            "Entegris concentration — also supplies FOUPs, specialty chemicals, and gas purifiers; single-company exposure",
            "PTFE and PVDF membrane polymers subject to EU PFAS regulations (2025+ restrictions could affect fluoropolymer membranes)",
            "Counterfeit filters documented in secondary market — yield impact from fake filters is catastrophic and often undetected until pattern defects appear",
            "Qualification of new filter suppliers requires extensive testing (particle generation, extractables, chemical compatibility) — 6–12 months minimum",
            "Specialty filter formats (e.g., dispense point filters for EUV photoresist) are application-specific with very limited supplier alternatives",
        ],
        "export_controls": {
            "status": "none",
            "detail": "Standard filtration products are not export controlled. Advanced versions for EUV photoresist may attract scrutiny as part of broader EUV process controls.",
            "eccn": "EAR99",
        },
        "grey_market_risk": "medium",
        "grey_market_detail": (
            "Counterfeit high-purity filters are a documented problem. Fake filters "
            "with correct external appearance but substandard membranes have been found "
            "in grey market supply chains. The defect is undetectable without destructive "
            "testing and may only manifest as yield loss. Procurement exclusively through "
            "authorized distributors is critical."
        ),
        "critical_mineral": False,
        "geographic_concentration": "USA dominant (Entegris, Pall, Parker); UK secondary",
        "hs_codes": ["8421.29", "8421.39"],
    },

    "electrostatic_chuck": {
        "name": "Electrostatic Chuck (ESC)",
        "aliases": ["ESC", "e-chuck", "wafer chuck", "Coulomb chuck", "Johnsen-Rahbek chuck", "ceramic chuck"],
        "category": "process_consumable",
        "description": (
            "A ceramic or polymer device that holds the wafer flat against the "
            "process chamber pedestal using electrostatic force during plasma "
            "processing, PVD, and CVD. Provides precise wafer temperature control "
            "through a helium back-side cooling channel. ESC material and design "
            "is specific to each tool model and process chemistry — a given ESC "
            "works in exactly one tool configuration. Replace frequency: "
            "approximately every 500,000–1,000,000 wafer passes depending on "
            "process aggressiveness. Failure causes wafer drop, contamination, "
            "or particle events. Critical for uniformity and yield."
        ),
        "used_in_steps": ["etch_dry", "pvd_sputtering", "cvd_deposition", "ald"],
        "availability": "specialized",
        "key_suppliers": [
            {"name": "Sumitomo Osaka Cement", "country": "Japan", "market_share": "~30%",
             "notes": "AlN and Al2O3 ESC; major OEM supplier to Lam and Applied Materials"},
            {"name": "Kyocera", "country": "Japan", "market_share": "~25%",
             "notes": "High-purity alumina and aluminum nitride ESCs"},
            {"name": "NGK Insulators", "country": "Japan", "market_share": "~15%",
             "notes": "Advanced ceramic ESC and heater components"},
            {"name": "CoorsTek", "country": "USA", "market_share": "~15%",
             "notes": "Alumina and AlN ceramic ESC for US OEMs"},
            {"name": "Applied Materials / Lam Research", "country": "USA", "market_share": "~15%",
             "notes": "Captive supply integrated into tool; sold as spare parts"},
        ],
        "supply_risks": [
            "Japan concentration (~70%) for ceramic ESC components",
            "Long lead times: 12–20 weeks for custom configurations; standard parts 6–10 weeks",
            "Tool-specific designs mean no interchangeability — an ESC for a Lam Kiyo will not fit an Applied Sym3",
            "AlN (aluminum nitride) ESCs require high-purity aluminum nitride powder with limited global supply",
            "Refurbished ESCs from decommissioned tools circulate in grey market; condition verification difficult",
        ],
        "export_controls": {
            "status": "partial",
            "detail": "Advanced ESCs designed for sub-10nm processes may fall under EAR 3B991 or 3B001 controls as components of controlled semiconductor manufacturing equipment. Japan has tightened export controls on advanced semiconductor components since 2023.",
            "eccn": "3B991",
        },
        "grey_market_risk": "medium",
        "grey_market_detail": (
            "Used and refurbished ESCs from decommissioned fabs or tools are widely "
            "traded. Condition is difficult to assess — internal delamination and "
            "helium leak paths are not visible externally. Installing a degraded ESC "
            "causes temperature non-uniformity, yield loss, and potential wafer "
            "breakage. Particularly active grey market from DRAM fab consolidations."
        ),
        "critical_mineral": False,
        "geographic_concentration": "Japan ~70% (Sumitomo, Kyocera, NGK); USA ~30%",
        "hs_codes": ["8543.70", "6909.19"],
    },

    "mfc_mass_flow_controller": {
        "name": "Mass Flow Controller (MFC)",
        "aliases": ["MFC", "mass flow controller", "gas flow controller", "thermal MFC", "Coriolis MFC", "flow controller"],
        "category": "process_consumable",
        "description": (
            "Precision instruments that measure and control the volumetric or mass "
            "flow rate of process gases into deposition, etch, and implant chambers. "
            "Thermal MFCs use a heated capillary sensor; Coriolis MFCs measure mass "
            "directly for corrosive or high-flow applications. Accuracy requirements "
            "for ALD are ±0.5% of setpoint — drift causes film thickness non-uniformity. "
            "Each process chamber uses 4–20 MFCs. A single miscalibrated MFC can cause "
            "systematic yield loss across an entire product line before detection."
        ),
        "used_in_steps": ["cvd_deposition", "ald", "etch_dry", "pvd_sputtering", "ion_implant"],
        "availability": "specialized",
        "key_suppliers": [
            {"name": "MKS Instruments", "country": "USA", "market_share": "~35%",
             "notes": "Type 1179 and Cirrus series; dominant in etch and CVD applications"},
            {"name": "Brooks Instrument (Emerson)", "country": "USA", "market_share": "~20%",
             "notes": "GF series; strong in corrosive gas applications"},
            {"name": "Horiba", "country": "Japan", "market_share": "~20%",
             "notes": "SEC-Z series; dominant in Japanese and Korean fabs"},
            {"name": "Fujikin", "country": "Japan", "market_share": "~12%",
             "notes": "High-purity gas delivery components and MFCs"},
            {"name": "Hitachi Metals / Proterial", "country": "Japan", "market_share": "~8%",
             "notes": "MFC and gas control components"},
        ],
        "supply_risks": [
            "MKS Instruments dominance — also supplies pressure controllers, RF power, and gas analysis; broad single-company exposure",
            "Semiconductor-grade MFCs require cleanroom assembly with particle-free wetted surfaces — cannot substitute industrial MFCs",
            "Calibration gas standards required for re-calibration; calibration drift increases with process gas exposure",
            "Lead times: 8–20 weeks for standard models; 26+ weeks for specialty configurations (H2, F2, HCl service)",
            "Advanced MFCs for sub-14nm ALD processes may be subject to EAR controls as part of controlled equipment",
        ],
        "export_controls": {
            "status": "partial",
            "detail": "MFCs with specifications meeting 3B991 thresholds (for use in deposition of <45nm films) may be controlled under EAR. Japan has included precision gas delivery equipment in its 2023 export control expansion.",
            "eccn": "3B991",
        },
        "grey_market_risk": "medium",
        "grey_market_detail": (
            "Used MFCs from decommissioned tools are widely traded. Calibration "
            "state is unknown and drift is common. Contaminated MFCs (from F2, Cl2, "
            "or HBr service) can release residual process gas into new applications. "
            "Counterfeit calibration stickers have been documented on used units "
            "sold as 'factory calibrated.'"
        ),
        "critical_mineral": False,
        "geographic_concentration": "USA ~55% (MKS, Brooks); Japan ~40% (Horiba, Fujikin, Proterial)",
        "hs_codes": ["9026.20", "9032.89"],
    },

    "foup_wafer_carrier": {
        "name": "FOUP (Front Opening Unified Pod)",
        "aliases": ["FOUP", "front opening unified pod", "wafer carrier", "wafer pod", "300mm carrier", "wafer transport container"],
        "category": "process_consumable",
        "description": (
            "Sealed polycarbonate or PEEK containers that transport and store 300mm "
            "wafers between process steps in the fab environment. FOUPs maintain an "
            "ultra-low particle and humidity environment around the wafer stack. "
            "Each FOUP holds 25 wafers in precision slots. A 300mm fab requires "
            "thousands of FOUPs in constant circulation through automated material "
            "handling systems (AMHS). FOUP outgassing, cleanliness, and mechanical "
            "integrity directly affect wafer contamination and yield. Damaged or "
            "degraded FOUPs are a significant source of defects."
        ),
        "used_in_steps": ["wafer_prep", "lithography_duv", "lithography_euv", "etch_dry", "etch_wet", "cvd_deposition", "ald", "cmp", "metallization_cu", "inspection_metrology"],
        "availability": "specialized",
        "key_suppliers": [
            {"name": "Entegris", "country": "USA", "market_share": "~60%",
             "notes": "300mm FOUP dominant supplier; also supplies chemical management systems"},
            {"name": "Miraial", "country": "Japan", "market_share": "~20%",
             "notes": "Strong in Japanese fabs; precision molded polymer FOUPs"},
            {"name": "Shin-Etsu Polymer", "country": "Japan", "market_share": "~12%",
             "notes": "Semiconductor packaging and FOUP components"},
            {"name": "Gudeng Precision", "country": "Taiwan", "market_share": "~8%",
             "notes": "FOUP and reticle pod supplier; growing with TSMC expansion"},
        ],
        "supply_risks": [
            "Entegris concentration — dominates both FOUP and many chemical delivery products",
            "Ultra-low outgassing polymer resins (polycarbonate, PEEK) have limited qualified suppliers",
            "FOUP door seal degradation causes contamination — replacement seals require qualification",
            "Taiwan fab expansion driving Gudeng capacity constraints",
            "AMHS compatibility — FOUPs are qualified to specific AMHS track specifications; cannot mix standards",
        ],
        "export_controls": {
            "status": "none",
            "detail": "FOUPs are generally not export controlled as standalone items. Advanced FOUPs designed specifically for EUV reticle transport may attract scrutiny.",
            "eccn": "EAR99",
        },
        "grey_market_risk": "low",
        "grey_market_detail": (
            "Grey market FOUP activity is limited — most are purchased through authorized channels "
            "due to AMHS qualification requirements. Used FOUPs from decommissioned fabs are "
            "sometimes refurbished, but contamination history makes reuse in leading-edge fabs risky."
        ),
        "critical_mineral": False,
        "geographic_concentration": "USA (Entegris) ~60%; Japan ~32%; Taiwan ~8%",
        "hs_codes": ["3923.10", "3926.90"],
    },

    "ceramic_chamber_components": {
        "name": "Ceramic Process Chamber Components",
        "aliases": ["chamber liner", "focus ring", "edge ring", "ceramic ring", "yttria coating", "alumina liner", "SiC ring", "quartz ring", "AlN component", "Y2O3 component"],
        "category": "process_consumable",
        "description": (
            "Precision ceramic parts that line plasma etch and CVD chamber interiors: "
            "liners, focus rings, edge rings, upper/lower electrodes, gas distribution "
            "plates (showerheads), and confinement rings. Materials include alumina "
            "(Al2O3), yttria (Y2O3), aluminum nitride (AlN), and silicon carbide (SiC), "
            "selected for plasma resistance and low particle generation. Yttria-coated "
            "components are specifically required for fluorine-chemistry etch processes "
            "at advanced nodes — Y2O3 resists HF and F-radical attack far better than "
            "Al2O3. Replace frequency: every 100,000–500,000 RF hours depending on "
            "process chemistry. Worn ceramics are the leading source of metallic "
            "contamination in etch chambers."
        ),
        "used_in_steps": ["etch_dry", "cvd_deposition", "pvd_sputtering"],
        "availability": "specialized",
        "key_suppliers": [
            {"name": "Kyocera", "country": "Japan", "market_share": "~30%",
             "notes": "Alumina, AlN, and yttria components; major OEM to Lam and Applied Materials"},
            {"name": "NGK Insulators", "country": "Japan", "market_share": "~20%",
             "notes": "Large-format ceramics and yttria-coated components"},
            {"name": "CoorsTek", "country": "USA", "market_share": "~20%",
             "notes": "Alumina and SiC chamber components; strong with US OEMs"},
            {"name": "Saint-Gobain", "country": "France", "market_share": "~15%",
             "notes": "SiC and advanced ceramic components; CVD SiC coating capability"},
            {"name": "Morgan Advanced Materials", "country": "UK", "market_share": "~10%",
             "notes": "Specialty ceramics for extreme environments"},
        ],
        "supply_risks": [
            "Japan concentration for yttria-coated components (~50%) — critical for advanced fluorine etch",
            "Yttrium oxide (Y2O3) raw material sourced primarily from China and rare earth supply chains",
            "Silicon carbide (SiC) ceramic production is energy-intensive and capacity-constrained",
            "Component qualification to a specific tool/process chemistry takes 3–6 months — cannot switch suppliers quickly",
            "Japan export controls (2023) now include some advanced ceramic components for semiconductor equipment",
        ],
        "export_controls": {
            "status": "partial",
            "detail": "Advanced etch-resistant ceramics (particularly yttria-coated components for sub-14nm etch) may fall under EAR 3B991 or Japan's expanded export controls as components of controlled semiconductor equipment.",
            "eccn": "3B991",
        },
        "grey_market_risk": "medium",
        "grey_market_detail": (
            "Used ceramic components from decommissioned etch chambers are traded in secondary "
            "markets. Wear state is difficult to assess visually — microcracking and yttria "
            "coating depletion are only detectable by metrology. Worn ceramics installed as "
            "'new' are a documented source of particle and metal contamination events."
        ),
        "critical_mineral": False,
        "geographic_concentration": "Japan ~50% (Kyocera, NGK); USA ~20% (CoorsTek); Europe ~25%",
        "hs_codes": ["6909.19", "6914.10"],
    },

    "quartz_process_components": {
        "name": "Quartz Process Components",
        "aliases": ["quartz tube", "quartz boat", "quartz paddle", "fused silica", "quartz furnace tube", "diffusion tube", "process tube", "quartz flange"],
        "category": "process_consumable",
        "description": (
            "High-purity fused silica (synthetic quartz) components used in thermal "
            "processing equipment: furnace tubes, wafer boats, paddles, baffles, "
            "and flanges. Purity requirements are extreme — metallic contamination "
            "at ppb levels causes doping anomalies and gate oxide defects. Used in "
            "diffusion furnaces (thermal oxidation, LPCVD), RTP chambers, and "
            "ion implant equipment. Operating temperatures up to 1200°C. Quartz "
            "components are consumables that degrade through thermal cycling, "
            "chemical attack, and devitrification (crystallization) — typically "
            "replaced every 6–18 months depending on process conditions."
        ),
        "used_in_steps": ["thermal_oxidation", "cvd_deposition", "ion_implant", "rtp_anneal"],
        "availability": "specialized",
        "key_suppliers": [
            {"name": "Heraeus Quarzglas", "country": "Germany", "market_share": "~35%",
             "notes": "Synthetic fused silica leader; Suprasil grades for semiconductor"},
            {"name": "Shin-Etsu Quartz", "country": "Japan", "market_share": "~30%",
             "notes": "High-purity quartz glass for semiconductor process equipment"},
            {"name": "Momentive (formerly GE Quartz)", "country": "USA", "market_share": "~20%",
             "notes": "HPFS fused silica; optical and process grades"},
            {"name": "Tosoh Quartz", "country": "Japan", "market_share": "~10%",
             "notes": "Semiconductor process quartz components"},
        ],
        "supply_risks": [
            "Spruce Pine, NC (USA) quartz sand mine — historically the primary global source of ultra-high-purity quartz for synthetic production; Hurricane Helene (Sept 2024) caused significant supply disruption",
            "Germany and Japan dominate finished component production (~65% combined)",
            "High-purity natural quartz feedstock concentrated in very few global locations (Spruce Pine, Norway, Australia)",
            "Devitrification during use is irreversible — cannot be refurbished, only replaced",
            "Specialty shapes (large-diameter tubes, complex geometries) require long lead times of 8–16 weeks",
        ],
        "export_controls": {
            "status": "none",
            "detail": "Quartz process components are generally not export controlled, though quartz optics for EUV are separately controlled.",
            "eccn": "EAR99",
        },
        "grey_market_risk": "low",
        "grey_market_detail": (
            "Low grey market activity — quartz quality is deterministic and easily tested. "
            "Counterfeit risk is low but substitution of lower-purity quartz for semiconductor-grade "
            "has occurred and causes metallic contamination issues that are difficult to trace."
        ),
        "critical_mineral": False,
        "geographic_concentration": "Germany ~35% (Heraeus); Japan ~40% (Shin-Etsu, Tosoh); USA ~20%",
        "hs_codes": ["7020.00", "7001.00"],
    },

    "perfluoroelastomer_seals": {
        "name": "Perfluoroelastomer (FFKM) Seals & O-Rings",
        "aliases": ["Kalrez", "FFKM", "perfluoroelastomer", "FFKM O-ring", "Chemraz", "Perlast", "process seal", "chamber seal", "fluoroelastomer seal"],
        "category": "process_consumable",
        "description": (
            "Perfluoroelastomer elastomeric seals used in semiconductor process "
            "equipment wherever standard FKM (Viton) seals cannot survive aggressive "
            "chemistry or plasma exposure. Required in virtually all etch, CVD, ALD, "
            "and wet process tools. FFKM provides near-universal chemical resistance "
            "including resistance to HF, plasma fluorine, chlorine, and strong "
            "oxidizers. DuPont's Kalrez is the market-defining product — 'Kalrez' "
            "is often used generically. Seals are consumable items replaced during "
            "preventive maintenance cycles (typically every 3–6 months per chamber). "
            "A failed seal causes equipment downtime, vacuum loss, or chemical leak — "
            "a safety and yield incident."
        ),
        "used_in_steps": ["etch_dry", "cvd_deposition", "ald", "pvd_sputtering", "etch_wet"],
        "availability": "single_source",
        "key_suppliers": [
            {"name": "DuPont (Kalrez)", "country": "USA", "market_share": "~60%",
             "notes": "Kalrez is the de facto standard for aggressive semiconductor chemistries; some grades have no qualified alternative"},
            {"name": "Parker Hannifin (Chemraz)", "country": "USA", "market_share": "~20%",
             "notes": "Alternative to Kalrez in some applications; qualified in many tool PM kits"},
            {"name": "Greene Tweed (Chemraz/Isolast)", "country": "USA", "market_share": "~10%",
             "notes": "FFKM for extreme chemical environments"},
            {"name": "Trelleborg (Isolast)", "country": "Sweden", "market_share": "~8%",
             "notes": "European alternative; growing semiconductor qualification"},
        ],
        "supply_risks": [
            "DuPont near-monopoly on Kalrez for highest-performance applications (plasma etch at <7nm) — alternatives are not qualified in many tool configurations",
            "PFAS regulatory pressure: EU PFAS restrictions (2025+ phase-in) could restrict fluoropolymer production including FFKM monomers",
            "Perfluorinated raw material (TFE, PMVE) production concentrated in a small number of chemical plants globally",
            "Counterfeit Kalrez is well-documented — fake seals that look identical to genuine seals cause equipment damage when they fail in aggressive chemistry",
            "Custom sizes and durometer specifications require long qualification cycles — cannot switch suppliers without process re-qualification",
        ],
        "export_controls": {
            "status": "none",
            "detail": "FFKM seals are not directly export controlled, though they are components of controlled semiconductor equipment.",
            "eccn": "EAR99",
        },
        "grey_market_risk": "high",
        "grey_market_detail": (
            "Counterfeit Kalrez is one of the most documented counterfeiting problems in "
            "semiconductor consumables. Fake seals with correct part numbers and packaging "
            "have been found through authorized-looking distributors. Seal failure in "
            "plasma or corrosive chemistry environments causes immediate equipment damage, "
            "safety incidents, and potential chemical exposure. Procurement exclusively "
            "through DuPont-authorized channels is strongly recommended. Authentication "
            "codes on packaging should be verified."
        ),
        "critical_mineral": False,
        "geographic_concentration": "USA dominant (DuPont, Parker, Greene Tweed); Sweden (Trelleborg)",
        "hs_codes": ["4016.93", "4016.99"],
    },

    "cmp_conditioner_disc": {
        "name": "CMP Pad Conditioner Disc",
        "aliases": ["conditioner disc", "diamond disc", "CMP conditioner", "pad conditioner", "dressing disc", "diamond conditioner"],
        "category": "process_consumable",
        "description": (
            "Diamond-studded discs that continuously condition (dress) CMP polishing "
            "pads during wafer polishing to maintain pad surface roughness and slurry "
            "transport channels. Without conditioning, CMP pads glaze and lose removal "
            "rate, causing within-wafer non-uniformity. Diamonds are embedded in a "
            "brazed or electroplated nickel matrix on a stainless steel disc. Diamond "
            "size (typically 100–400 µm grit), density, and protrusion height are "
            "precisely engineered. Disc lifetime: approximately 500–2,000 wafer passes "
            "depending on process. Each CMP tool uses 1–3 conditioning discs simultaneously."
        ),
        "used_in_steps": ["cmp"],
        "availability": "specialized",
        "key_suppliers": [
            {"name": "3M", "country": "USA", "market_share": "~30%",
             "notes": "A165 and A2000 series; dominant in logic and leading-edge memory CMP"},
            {"name": "Kinik Company", "country": "Taiwan", "market_share": "~25%",
             "notes": "Strong in memory fabs; competitive pricing; TSMC qualified"},
            {"name": "Saesol Diamond Industry", "country": "South Korea", "market_share": "~20%",
             "notes": "Growing share in Korean memory fabs (Samsung, SK Hynix)"},
            {"name": "Abrasive Technology", "country": "USA", "market_share": "~12%",
             "notes": "Custom and specialty conditioner discs"},
            {"name": "Morgan Advanced Materials", "country": "UK", "market_share": "~8%",
             "notes": "PCD and CVD diamond conditioners for specialty applications"},
        ],
        "supply_risks": [
            "Synthetic diamond quality and supply — industrial diamond production concentrated in China (~80% of global synthetic diamond)",
            "Diamond-metal brazing and electroplating expertise concentrated in a small number of facilities",
            "Taiwan (Kinik) geopolitical risk — significant share of TSMC-qualified supply",
            "Application-specific qualification: a conditioner disc qualified for oxide CMP may not be qualified for copper or STI CMP",
        ],
        "export_controls": {
            "status": "none",
            "detail": "CMP conditioner discs are not export controlled.",
            "eccn": "EAR99",
        },
        "grey_market_risk": "low",
        "grey_market_detail": (
            "Low grey market risk — counterfeit conditioner discs are uncommon. "
            "Used discs have limited resale value as wear state is apparent. "
            "Main risk is substitution of unqualified (but genuine) discs from "
            "non-qualified suppliers into critical process applications."
        ),
        "critical_mineral": False,
        "geographic_concentration": "USA ~42% (3M, Abrasive Technology); Taiwan ~25% (Kinik); South Korea ~20%",
        "hs_codes": ["6804.21", "8202.99"],
    },

    # -----------------------------------------------------------------------
    # Wet Chemistry & Chemical Delivery
    # -----------------------------------------------------------------------

    "tmah_developer": {
        "name": "TMAH (Tetramethylammonium Hydroxide) Developer",
        "aliases": ["TMAH", "tetramethylammonium hydroxide", "photoresist developer", "2.38% TMAH", "positive resist developer", "Si etchant TMAH"],
        "category": "wet_chemistry",
        "description": (
            "The universal developer for positive-tone photoresists in DUV and EUV "
            "lithography. A 2.38% aqueous TMAH solution selectively dissolves "
            "exposed photoresist. Also used as an anisotropic silicon etchant for "
            "MEMS and sensor fabrication. Semiconductor-grade TMAH requires metallic "
            "impurities below 1 ppb — a single sodium or potassium ion can cause "
            "threshold voltage shifts in transistors. TMAH is a systemic toxin with "
            "no antidote — dermal absorption is lethal, requiring strict handling protocols."
        ),
        "used_in_steps": ["lithography_duv", "lithography_euv", "etch_wet"],
        "availability": "specialized",
        "key_suppliers": [
            {"name": "SACHEM Inc.", "country": "USA", "market_share": "~30%",
             "notes": "Leading US supplier of semiconductor-grade TMAH; strong in North American fabs"},
            {"name": "Chang Chun Group", "country": "Taiwan", "market_share": "~25%",
             "notes": "Major Asian supplier; qualified at TSMC and UMC"},
            {"name": "Stella Chemifa", "country": "Japan", "market_share": "~20%",
             "notes": "High-purity electronic chemicals including TMAH"},
            {"name": "Tama Chemicals", "country": "Japan", "market_share": "~15%",
             "notes": "Specialty electronic chemicals"},
        ],
        "supply_risks": [
            "Taiwan concentration (Chang Chun ~25%) — geopolitical risk for Asian fab supply",
            "TMAH toxicity creates transport and storage regulatory requirements that limit supplier flexibility",
            "Semiconductor-grade purity specification (<1 ppb metals) narrows qualified supplier pool significantly",
            "Increasing regulatory scrutiny of TMAH as an acutely toxic substance may restrict production in some jurisdictions",
        ],
        "export_controls": {
            "status": "none",
            "detail": "TMAH is not directly export controlled under EAR, though it is subject to hazardous materials regulations. Some jurisdictions restrict import due to toxicity classification.",
            "eccn": "EAR99",
        },
        "grey_market_risk": "low",
        "grey_market_detail": (
            "TMAH grey market activity is minimal due to toxicity — informal trade is hazardous "
            "and heavily regulated. The main risk is purity substitution: industrial-grade TMAH "
            "sold as semiconductor grade, causing metal contamination that is difficult to trace."
        ),
        "critical_mineral": False,
        "geographic_concentration": "USA ~30%; Taiwan ~25%; Japan ~35%",
        "hs_codes": ["2923.90"],
    },

    "buffered_hf_boe": {
        "name": "Buffered Oxide Etch (BOE / BHF)",
        "aliases": ["BOE", "BHF", "buffered HF", "buffered oxide etch", "ammonium fluoride buffer", "6:1 BOE", "10:1 BOE", "oxide etchant"],
        "category": "wet_chemistry",
        "description": (
            "An ammonium fluoride (NH4F) buffered hydrofluoric acid solution used "
            "for controlled, uniform etching of silicon dioxide (SiO2) and silicon "
            "nitride (Si3N4). Unlike anhydrous or concentrated HF, BOE provides "
            "stable, reproducible etch rates and better selectivity to silicon. "
            "Common concentrations: 6:1 (6 parts 40% NH4F : 1 part 49% HF) for "
            "standard oxide etch; 10:1 for delicate structures. Used in gate oxide "
            "preparation, contact opening, MEMS release, and surface preparation. "
            "Purity requirements are extreme — metallic contamination causes "
            "gate oxide integrity failures."
        ),
        "used_in_steps": ["etch_wet", "wafer_prep"],
        "availability": "specialized",
        "key_suppliers": [
            {"name": "Stella Chemifa", "country": "Japan", "market_share": "~35%",
             "notes": "Leading supplier of high-purity fluorine chemistry including BOE; critical Japan concentration"},
            {"name": "Honeywell (Specialty Chemicals)", "country": "USA", "market_share": "~20%",
             "notes": "Electronic-grade BOE for North American fabs"},
            {"name": "Solvay", "country": "Belgium", "market_share": "~18%",
             "notes": "Specialty fluorine chemistry; European fab supply"},
            {"name": "Air Products", "country": "USA", "market_share": "~15%",
             "notes": "Electronic specialty gases and chemicals"},
        ],
        "supply_risks": [
            "Stella Chemifa Japan concentration — HF and fluorine chemistry supply heavily Japan-dependent",
            "Anhydrous HF feedstock — global fluorite (CaF2) mining concentrated in China, Mexico, South Africa",
            "BOE is acutely hazardous (HF burns have high lethality) — strict transport and handling requirements",
            "Japan export controls (2023) include some high-purity fluorine chemistry",
        ],
        "export_controls": {
            "status": "partial",
            "detail": "HF and fluorine compounds have dual-use classification in some jurisdictions. Japan export controls (2023) include certain ultra-high-purity fluorine chemistry products. Not directly controlled under US EAR for standard semiconductor use.",
            "eccn": "EAR99 (standard grades)",
        },
        "grey_market_risk": "low",
        "grey_market_detail": (
            "BOE grey market activity is low — the extreme hazard limits informal trade. "
            "Purity substitution risk exists: lower-grade material sold as semiconductor-grade "
            "causes defects that may not be immediately traceable to the chemical source."
        ),
        "critical_mineral": False,
        "geographic_concentration": "Japan ~35% (Stella Chemifa); USA ~35%; Europe ~18%",
        "hs_codes": ["2811.11", "2827.11"],
    },

    "ipa_electronic_grade": {
        "name": "Electronic Grade Isopropyl Alcohol (IPA)",
        "aliases": ["IPA", "isopropyl alcohol", "2-propanol", "electronic IPA", "semiconductor IPA", "wafer rinse IPA", "Marangoni IPA"],
        "category": "wet_chemistry",
        "description": (
            "Ultra-high-purity isopropyl alcohol (IPA) used extensively in wafer "
            "cleaning, drying (Marangoni drying), photoresist thinning, and equipment "
            "cleaning throughout the fab. Electronic grade requires metallic impurities "
            "below 1 ppb and particulate counts below 10 particles/mL. The Marangoni "
            "drying technique uses IPA vapor to create a surface tension gradient that "
            "removes water without mechanical contact, eliminating watermarks. "
            "IPA is one of the highest-volume liquid chemicals in a semiconductor fab — "
            "a 300mm fab consumes thousands of liters daily."
        ),
        "used_in_steps": ["wafer_prep", "etch_wet", "lithography_duv"],
        "availability": "specialized",
        "key_suppliers": [
            {"name": "Tokuyama Corporation", "country": "Japan", "market_share": "~30%",
             "notes": "Largest electronic-grade IPA supplier globally; dominant in Asian fabs"},
            {"name": "Mitsui Chemicals", "country": "Japan", "market_share": "~20%",
             "notes": "Electronic specialty chemicals including IPA"},
            {"name": "LG Chem", "country": "South Korea", "market_share": "~15%",
             "notes": "Growing semiconductor chemical supply; IPA for Korean fabs"},
            {"name": "KMG Chemicals (CMC Materials)", "country": "USA", "market_share": "~15%",
             "notes": "Electronic grade IPA for North American fab supply"},
            {"name": "Dow Chemical", "country": "USA", "market_share": "~12%",
             "notes": "Broad chemical supply including electronic grade IPA"},
        ],
        "supply_risks": [
            "COVID-19 (2020) caused global IPA shortage — semiconductor fabs competed with pharmaceutical and sanitizer demand; supply disrupted for 6–12 months",
            "Japan dominance (~50%) for highest purity grades used in leading-edge processes",
            "IPA is a commodity at industrial grade but semiconductor grade has very limited qualified suppliers",
            "High consumption volume means storage and logistics infrastructure must be substantial",
        ],
        "export_controls": {
            "status": "none",
            "detail": "IPA is not export controlled. Subject to standard flammable liquid transport regulations.",
            "eccn": "EAR99",
        },
        "grey_market_risk": "low",
        "grey_market_detail": (
            "IPA grey market risk is low but purity substitution is a concern — "
            "industrial-grade IPA sold as semiconductor grade. The main indicator "
            "is metallic contamination causing device yield loss, which is "
            "difficult to source to a specific chemical without full supply chain audit."
        ),
        "critical_mineral": False,
        "geographic_concentration": "Japan ~50% (Tokuyama, Mitsui); South Korea ~15%; USA ~27%",
        "hs_codes": ["2905.12"],
    },

    "upw_system_components": {
        "name": "Ultrapure Water (UPW) System Components",
        "aliases": ["UPW", "ultrapure water", "DI water system", "deionized water", "18 megohm water", "water purification", "RO membrane", "ion exchange resin", "UPW polishing"],
        "category": "wet_chemistry",
        "description": (
            "Ultrapure water (18.2 MΩ·cm resistivity, <1 ppb TOC, <1 ppt metals) "
            "is the highest-volume consumable in semiconductor manufacturing — a "
            "300mm fab uses 2–10 million gallons per day. UPW systems combine: "
            "reverse osmosis (RO) membranes, mixed-bed ion exchange resins, "
            "UV oxidation units (TOC reduction), ultrafiltration (UF) membranes, "
            "and electrodeionization (EDI) modules. All of these are consumable "
            "components requiring periodic replacement. UPW system failure halts "
            "all wet processing. Water quality directly affects particle counts, "
            "oxide growth rates, and metal contamination."
        ),
        "used_in_steps": ["wafer_prep", "etch_wet", "cmp", "lithography_duv"],
        "availability": "specialized",
        "key_suppliers": [
            {"name": "Kurita Water Industries", "country": "Japan", "market_share": "~25%",
             "notes": "Leading UPW system integrator; dominant in Japan and Taiwan fabs"},
            {"name": "Organo Corporation", "country": "Japan", "market_share": "~20%",
             "notes": "UPW systems and ion exchange resins; strong in Japanese fabs"},
            {"name": "Veolia Water Technologies", "country": "France", "market_share": "~20%",
             "notes": "Global water treatment; UPW systems for US and European fabs"},
            {"name": "Evoqua Water Technologies", "country": "USA", "market_share": "~15%",
             "notes": "EDI modules and UPW polishing components"},
            {"name": "MilliporeSigma (Merck KGaA)", "country": "Germany", "market_share": "~10%",
             "notes": "UF membranes and analytical-grade water system components"},
        ],
        "supply_risks": [
            "Japan concentration (Kurita, Organo ~45%) for UPW system integration and components",
            "Ion exchange resin supply — Dow, Purolite, Lanxess; capacity can be constrained during fab buildout cycles",
            "RO membrane supply — DowDuPont (Filmtec), Toray, Hydranautics; fluoropolymer PFAS regulatory risk",
            "UPW system failure has immediate production impact — no buffer stock possible for water itself",
            "Water scarcity increasing in Taiwan and Arizona (TSMC fab locations) — UPW efficiency becoming strategic",
        ],
        "export_controls": {
            "status": "none",
            "detail": "UPW system components are not export controlled as standalone items.",
            "eccn": "EAR99",
        },
        "grey_market_risk": "low",
        "grey_market_detail": (
            "Low grey market risk for UPW components — these are infrastructure items "
            "with long qualification cycles. Used ion exchange resins are occasionally "
            "sold as regenerated product; purity verification is straightforward."
        ),
        "critical_mineral": False,
        "geographic_concentration": "Japan ~45% (Kurita, Organo); France/USA/Germany ~45%",
        "hs_codes": ["8421.21", "8421.99"],
    },

    # -----------------------------------------------------------------------
    # CVD / ALD Precursors & Specialty Gases
    # -----------------------------------------------------------------------

    "teos_cvd_precursor": {
        "name": "TEOS (Tetraethyl Orthosilicate) CVD Precursor",
        "aliases": ["TEOS", "tetraethyl orthosilicate", "TEOS precursor", "PECVD precursor", "CVD silicon dioxide", "silica precursor"],
        "category": "cvd_precursor",
        "description": (
            "The primary precursor for chemical vapor deposition of silicon dioxide "
            "(SiO2) films. TEOS decomposes at 650–750°C (LPCVD) or at lower "
            "temperatures with plasma assistance (PECVD-TEOS) to deposit conformal "
            "SiO2 used as inter-layer dielectric (ILD), hardmask, liner oxide, and "
            "shallow trench isolation fill. PECVD-TEOS deposits near room temperature, "
            "enabling use over metal layers. One of the highest-volume liquid CVD "
            "precursors by consumption. Semiconductor grade requires <1 ppb metallic "
            "impurities and precise water content control."
        ),
        "used_in_steps": ["cvd_deposition", "ald"],
        "availability": "specialized",
        "key_suppliers": [
            {"name": "Evonik Industries", "country": "Germany", "market_share": "~30%",
             "notes": "Dynasylan TEOS; major global semiconductor-grade supplier"},
            {"name": "Merck KGaA", "country": "Germany", "market_share": "~25%",
             "notes": "Electronic-grade TEOS through Sigma-Aldrich and specialty materials brands"},
            {"name": "Shin-Etsu Chemical", "country": "Japan", "market_share": "~20%",
             "notes": "Silicon-based chemical precursors for semiconductor"},
            {"name": "Gelest (Mitsubishi Chemical)", "country": "USA", "market_share": "~15%",
             "notes": "Specialty organosilicon precursors including electronic grade TEOS"},
        ],
        "supply_risks": [
            "Germany concentration (~55% of global semiconductor-grade TEOS production) in Evonik and Merck",
            "TEOS is moisture-sensitive — specialty packaging and handling required for semiconductor grade",
            "Organosilicon precursor production concentrated in Germany and Japan",
        ],
        "export_controls": {
            "status": "none",
            "detail": "TEOS is not export controlled under EAR for standard semiconductor applications.",
            "eccn": "EAR99",
        },
        "grey_market_risk": "low",
        "grey_market_detail": (
            "Low grey market risk. Purity substitution is the main concern — "
            "industrial TEOS sold as semiconductor grade causes oxide film defects."
        ),
        "critical_mineral": False,
        "geographic_concentration": "Germany ~55% (Evonik, Merck); Japan ~20%; USA ~15%",
        "hs_codes": ["2920.90"],
    },

    "silane_sih4": {
        "name": "Silane (SiH4)",
        "aliases": ["SiH4", "silane", "monosilane", "silicon hydride", "polysilicon precursor", "LPCVD silane", "amorphous silicon precursor"],
        "category": "cvd_precursor",
        "description": (
            "The primary precursor for LPCVD deposition of polycrystalline silicon "
            "(poly-Si), amorphous silicon (a-Si), and silicon nitride (with NH3). "
            "Polysilicon deposited from silane is used for gate electrodes (legacy "
            "nodes), capacitor electrodes (DRAM), and resistors. Silane is a "
            "pyrophoric gas — it ignites spontaneously on contact with air. This "
            "property requires specialized gas cabinets, automated valve systems, "
            "and dedicated abatement. Ultra-high-purity silane (99.9999%+) is "
            "required for advanced semiconductor applications — metallic impurities "
            "cause catastrophic device defects."
        ),
        "used_in_steps": ["cvd_deposition", "ald"],
        "availability": "specialized",
        "key_suppliers": [
            {"name": "SK Materials", "country": "South Korea", "market_share": "~35%",
             "notes": "Dominant Asian supplier; primary source for Samsung and SK Hynix"},
            {"name": "Air Products", "country": "USA", "market_share": "~25%",
             "notes": "Global specialty gas leader; Silane Plus ultra-high purity grade"},
            {"name": "Linde", "country": "UK/Germany", "market_share": "~20%",
             "notes": "Global industrial gas; semiconductor-grade silane"},
            {"name": "REC Silicon", "country": "Norway/USA", "market_share": "~10%",
             "notes": "Polysilicon and silane from fluidized bed reactor process"},
        ],
        "supply_risks": [
            "Pyrophoric nature requires specialized transport vessels, storage, and abatement — limits logistics flexibility",
            "Ultra-high purity production is capital-intensive with few qualified global facilities",
            "SK Materials dominance in Asia — Korean supply disruption would affect DRAM and logic fabs significantly",
            "Silane is a WMD-relevant precursor in some regulatory frameworks — subject to enhanced scrutiny in certain export scenarios",
        ],
        "export_controls": {
            "status": "partial",
            "detail": "Silane has dual-use classification in some jurisdictions as a potential WMD precursor and is subject to enhanced export controls to certain destinations. Standard semiconductor supply under EAR99 but may require end-use certificates.",
            "eccn": "EAR99 (standard); may require end-use certification",
        },
        "grey_market_risk": "low",
        "grey_market_detail": (
            "Grey market activity is very low — silane's pyrophoric nature and "
            "specialized handling requirements make informal trade extremely hazardous. "
            "The main risk is counterfeit purity certification on cylinders."
        ),
        "critical_mineral": False,
        "geographic_concentration": "South Korea ~35% (SK Materials); USA ~25%; Europe ~20%",
        "hs_codes": ["2850.00"],
    },

    "hmds_adhesion_promoter": {
        "name": "HMDS (Hexamethyldisilazane) Adhesion Promoter",
        "aliases": ["HMDS", "hexamethyldisilazane", "adhesion promoter", "photoresist adhesion", "resist primer", "HMDS vapor prime"],
        "category": "cvd_precursor",
        "description": (
            "A silylating agent vapor-deposited on wafer surfaces immediately before "
            "photoresist coating to improve adhesion. HMDS reacts with surface hydroxyl "
            "groups on SiO2 to create a hydrophobic trimethylsilyl surface that bonds "
            "strongly to photoresist polymers. Applied in a vapor prime oven at "
            "100–120°C with nitrogen carrier gas. Without HMDS priming, photoresist "
            "delamination during wet processing is common. A standard step before "
            "every lithography level. Purity requirements focus on moisture content "
            "and metallic contamination — water contamination deactivates HMDS."
        ),
        "used_in_steps": ["lithography_duv", "lithography_euv"],
        "availability": "specialized",
        "key_suppliers": [
            {"name": "Dow Chemical", "country": "USA", "market_share": "~30%",
             "notes": "Electronic-grade HMDS; broad semiconductor customer base"},
            {"name": "Shin-Etsu Chemical", "country": "Japan", "market_share": "~30%",
             "notes": "Silicone chemistry leader; semiconductor-grade HMDS"},
            {"name": "Momentive Performance Materials", "country": "USA", "market_share": "~20%",
             "notes": "Organosilicon specialty chemicals"},
            {"name": "Evonik Industries", "country": "Germany", "market_share": "~15%",
             "notes": "Dynasylan brand organosilicon specialty chemicals"},
        ],
        "supply_risks": [
            "HMDS production is well-distributed between US and Japan — moderate supply security",
            "Moisture sensitivity requires specialty packaging (anhydrous conditions) — degrades rapidly if improperly stored",
            "Japan export controls on lithography-related chemicals (2023) could theoretically impact HMDS supply to certain destinations",
        ],
        "export_controls": {
            "status": "none",
            "detail": "HMDS is not export controlled under EAR for standard semiconductor use.",
            "eccn": "EAR99",
        },
        "grey_market_risk": "low",
        "grey_market_detail": (
            "Low grey market risk. HMDS degradation from moisture contamination is "
            "the primary quality risk — degraded product causes adhesion failures "
            "that manifest as pattern lift during development."
        ),
        "critical_mineral": False,
        "geographic_concentration": "USA ~50% (Dow, Momentive); Japan ~30% (Shin-Etsu); Germany ~15%",
        "hs_codes": ["2931.90"],
    },

    # -----------------------------------------------------------------------
    # Lithography Consumables
    # -----------------------------------------------------------------------

    "barc_coating": {
        "name": "Bottom Anti-Reflective Coating (BARC)",
        "aliases": ["BARC", "ARC", "anti-reflective coating", "bottom ARC", "DARC", "organic ARC", "inorganic ARC", "light absorbing layer"],
        "category": "lithography_consumable",
        "description": (
            "Thin film coatings applied to the wafer before photoresist to absorb "
            "reflected light from underlying topography, preventing standing wave "
            "effects and CD variations caused by reflective notching. Organic BARCs "
            "are spin-coated polymer films; inorganic BARCs (DARCs) are CVD silicon "
            "oxynitride films. Critical at DUV (193nm) where substrate reflectivity "
            "causes severe CD non-uniformity without BARC. EUV uses specialized BARC "
            "formulations. BARC selection and optimization is specific to the resist "
            "system, substrate, and exposure wavelength — cannot be universally "
            "substituted between processes."
        ),
        "used_in_steps": ["lithography_duv", "lithography_euv"],
        "availability": "specialized",
        "key_suppliers": [
            {"name": "Brewer Science", "country": "USA", "market_share": "~40%",
             "notes": "Inventor of BARC; dominant for advanced node organic BARCs; AZ Electronics acquisition"},
            {"name": "JSR Corporation", "country": "Japan", "market_share": "~25%",
             "notes": "Lithography materials including BARC; Japan export controls 2023 impact"},
            {"name": "Merck KGaA (AZ Materials)", "country": "Germany", "market_share": "~20%",
             "notes": "AZ brand lithography materials including ARC/BARC"},
            {"name": "Shin-Etsu Chemical", "country": "Japan", "market_share": "~10%",
             "notes": "Lithography ancillary materials"},
        ],
        "supply_risks": [
            "Japan concentration (JSR, Shin-Etsu ~35%) — subject to Japan export controls on advanced semiconductor materials (2023)",
            "Brewer Science (USA) dominance for leading-edge node BARC formulations",
            "BARC formulations are IP-sensitive — only 2–3 suppliers qualified for any given advanced process",
            "Japan's 2023 export controls explicitly include photoresist-related materials, potentially including some BARC formulations",
        ],
        "export_controls": {
            "status": "partial",
            "detail": "Japan export controls (July 2023) include 'photoresist-related chemicals' which may encompass advanced BARC formulations. US-made BARCs are generally EAR99 for standard semiconductor use.",
            "eccn": "EAR99 (US); Japan-controlled for some advanced formulations",
        },
        "grey_market_risk": "low",
        "grey_market_detail": (
            "BARC grey market risk is low — these are highly engineered materials "
            "qualified to specific process nodes. Substitution with unqualified material "
            "immediately causes patterning defects detectable at first inspection."
        ),
        "critical_mineral": False,
        "geographic_concentration": "USA ~40% (Brewer Science); Japan ~35% (JSR, Shin-Etsu); Germany ~20%",
        "hs_codes": ["3707.90", "3811.90"],
    },

    "duv_pellicle": {
        "name": "DUV Photomask Pellicle",
        "aliases": ["DUV pellicle", "ArF pellicle", "193nm pellicle", "mask pellicle", "reticle pellicle", "nitrocellulose pellicle", "fluoropolymer pellicle"],
        "category": "lithography_consumable",
        "description": (
            "A thin transparent membrane stretched over a metal frame and mounted "
            "on the photomask to keep particles out of the focal plane of exposure. "
            "Particles landing on the pellicle are out of focus and do not print. "
            "DUV pellicles use nitrocellulose or fluoropolymer membranes transmissive "
            "at 193nm. Each mask reticle has one pellicle; a 300mm fab has hundreds "
            "of active reticles each requiring a qualified pellicle. Pellicle lifetime "
            "is limited by UV dose accumulated — typically 50–500 billion pulses. "
            "Distinct from EUV pellicles (which are a different, far more challenging "
            "technology already in the knowledge base)."
        ),
        "used_in_steps": ["lithography_duv"],
        "availability": "specialized",
        "key_suppliers": [
            {"name": "Mitsui Chemicals", "country": "Japan", "market_share": "~40%",
             "notes": "Leading DUV pellicle supplier; Pellicle brand dominant in Asia"},
            {"name": "Asahi Kasei", "country": "Japan", "market_share": "~25%",
             "notes": "DUV pellicle materials and membranes"},
            {"name": "FST (Freudenberg Sealing Technologies)", "country": "Germany/Taiwan", "market_share": "~20%",
             "notes": "DUV pellicles; manufacturing in Taiwan"},
            {"name": "Micro Lithography Inc.", "country": "USA", "market_share": "~10%",
             "notes": "DUV and broadband pellicles for US fabs"},
        ],
        "supply_risks": [
            "Japan concentration (~65%) in Mitsui Chemicals and Asahi Kasei",
            "Nitrocellulose and fluoropolymer membrane materials require ultra-high purity processing",
            "Pellicle frame and adhesive materials must be outgassing-free to avoid contaminating photomask",
            "DUV pellicle supply is more resilient than EUV (multiple suppliers vs. EUV near-monopoly) but still concentrated",
        ],
        "export_controls": {
            "status": "none",
            "detail": "DUV pellicles are not export controlled as standalone items (unlike EUV pellicles which may attract scrutiny as part of broader EUV process controls).",
            "eccn": "EAR99",
        },
        "grey_market_risk": "low",
        "grey_market_detail": (
            "Low grey market activity. Used pellicles have limited resale value as "
            "UV dose history is difficult to verify. Contaminated or damaged pellicles "
            "that cause mask defects are the primary failure mode."
        ),
        "critical_mineral": False,
        "geographic_concentration": "Japan ~65% (Mitsui, Asahi Kasei); Germany/Taiwan ~20%; USA ~10%",
        "hs_codes": ["3920.99", "9001.90"],
    },

    # -----------------------------------------------------------------------
    # Gas & Fluid Infrastructure
    # -----------------------------------------------------------------------

    "specialty_gas_purifiers": {
        "name": "Point-of-Use Specialty Gas Purifiers",
        "aliases": ["gas purifier", "POU purifier", "getter purifier", "in-line purifier", "gas scrubber", "SAES purifier", "hot getter", "Nanochem purifier"],
        "category": "gas_infrastructure",
        "description": (
            "Inline purification modules installed in gas delivery lines immediately "
            "before the process chamber to remove trace moisture (H2O), oxygen (O2), "
            "and hydrocarbons from specialty process gases. Use reactive metal getter "
            "materials (Zr alloys, Ti) or catalytic beds that chemisorb contaminants "
            "at elevated temperatures. Critical for ALD and CVD processes where ppb-level "
            "oxygen contamination causes interface traps and film quality degradation. "
            "For high-k gate dielectrics (HfO2), O2 contamination at 10 ppb levels "
            "causes measurable threshold voltage shifts. Purifier cartridges are "
            "consumables replaced every 6–24 months; exhausted purifiers can outgas "
            "previously captured contaminants if temperature cycles occur."
        ),
        "used_in_steps": ["cvd_deposition", "ald", "etch_dry"],
        "availability": "specialized",
        "key_suppliers": [
            {"name": "Entegris (SAES Getters acquisition)", "country": "USA/Italy", "market_share": "~45%",
             "notes": "SAES brand point-of-use purifiers; Entegris acquired SAES Getters semiconductor division"},
            {"name": "Matheson Gas (IXYS/Air Products)", "country": "USA", "market_share": "~25%",
             "notes": "Nanochem series gas purifiers; strong in inert and reactive gas purification"},
            {"name": "Mott Corporation", "country": "USA", "market_share": "~15%",
             "notes": "Porous metal and specialty gas filtration/purification"},
            {"name": "Japan Pionics", "country": "Japan", "market_share": "~10%",
             "notes": "Specialty gas purification for Japanese fabs"},
        ],
        "supply_risks": [
            "Entegris concentration — SAES acquisition added gas purifiers to an already broad Entegris semiconductor consumable portfolio",
            "Getter material supply — reactive metal alloys (Zr, Ti) for getter beds have some geographic concentration",
            "Purifier qualification to specific gas/tool/process combinations is extensive — cannot switch mid-process",
            "Exhausted purifiers require specialized disposal (pyrophoric getter materials)",
        ],
        "export_controls": {
            "status": "partial",
            "detail": "Advanced gas purifiers for ALD/CVD of sub-7nm films may be subject to EAR controls as components of controlled semiconductor equipment. Standard purifiers are EAR99.",
            "eccn": "EAR99 (standard); 3B991 (advanced process)",
        },
        "grey_market_risk": "medium",
        "grey_market_detail": (
            "Used or exhausted gas purifiers are sometimes sold as functional product. "
            "An exhausted getter purifier provides no protection and may release captured "
            "contaminants — causing immediate process excursions. Visual inspection cannot "
            "distinguish a functional from an exhausted purifier."
        ),
        "critical_mineral": False,
        "geographic_concentration": "USA dominant (Entegris/SAES, Matheson, Mott); Japan ~10%",
        "hs_codes": ["8421.39", "8419.89"],
    },

    "gas_abatement_systems": {
        "name": "Process Gas Abatement Systems",
        "aliases": ["abatement system", "scrubber", "gas scrubber", "exhaust treatment", "PFC abatement", "burn box", "wet scrubber", "plasma abatement"],
        "category": "gas_infrastructure",
        "description": (
            "End-of-pipe treatment systems that destroy or capture toxic, hazardous, "
            "and environmentally regulated process gases from fab exhaust streams. "
            "Types: combustion (burn box) for silane/pyrophorics; wet scrubbers for "
            "acid gases (HCl, HF, Cl2); catalytic oxidizers for PFCs (CF4, SF6, NF3); "
            "and plasma abatement for mixed gas streams. Required by safety regulations "
            "and environmental permits — a fab cannot legally operate without adequate "
            "abatement. PFC abatement is increasingly critical under carbon footprint "
            "reduction commitments (SF6 has 22,800× CO2 global warming potential). "
            "Abatement systems are capital equipment but have significant consumable "
            "costs: combustion fuel, scrubber water, and catalyst replacement."
        ),
        "used_in_steps": ["etch_dry", "cvd_deposition", "ald"],
        "availability": "specialized",
        "key_suppliers": [
            {"name": "Edwards Vacuum (Atlas Copco)", "country": "UK", "market_share": "~40%",
             "notes": "GSX and EPX series; dominant global abatement supplier for logic fabs"},
            {"name": "CS Clean Solutions", "country": "Germany", "market_share": "~20%",
             "notes": "High-efficiency abatement for PFC and acid gas streams"},
            {"name": "Ebara Corporation", "country": "Japan", "market_share": "~20%",
             "notes": "Strong in Japanese and Korean memory fabs; dry pump and abatement systems"},
            {"name": "DAS Environmental Expert", "country": "Germany", "market_share": "~12%",
             "notes": "Catalytic oxidation abatement for PFC destruction"},
        ],
        "supply_risks": [
            "Abatement is a regulatory compliance requirement — failure to maintain abatement systems risks fab operating permit",
            "Edwards (UK/Atlas Copco) dominance in logic fab segment",
            "Abatement consumables (catalyst, burner fuel, scrubber water treatment) are ongoing costs",
            "PFC abatement efficiency standards tightening under semiconductor industry sustainability commitments",
        ],
        "export_controls": {
            "status": "none",
            "detail": "Abatement systems are generally not export controlled. Components may be subject to standard dual-use rules.",
            "eccn": "EAR99",
        },
        "grey_market_risk": "low",
        "grey_market_detail": (
            "Low grey market risk — abatement systems are capital equipment with "
            "known provenance. Used systems are traded at decommissioned fabs but "
            "require full certification and compliance testing before reuse."
        ),
        "critical_mineral": False,
        "geographic_concentration": "UK ~40% (Edwards); Germany ~32% (CS Clean, DAS); Japan ~20% (Ebara)",
        "hs_codes": ["8421.39", "8421.29"],
    },

    # -----------------------------------------------------------------------
    # Back-End Process
    # -----------------------------------------------------------------------

    "wafer_dicing_blades": {
        "name": "Wafer Dicing Blades",
        "aliases": ["dicing blade", "diamond blade", "CBN blade", "dicing saw blade", "Disco blade", "semiconductor dicing", "die singulation blade"],
        "category": "back_end_consumable",
        "description": (
            "Precision diamond or cubic boron nitride (CBN) abrasive blades used "
            "in wafer dicing saws to singulate individual dies from finished wafers. "
            "Blades are hub-mounted or hubless (resin or metal bond), 40–300µm thick, "
            "and rotate at 30,000–60,000 RPM with deionized water cooling. Blade "
            "specification (diamond grit size, bond hardness, blade thickness) is "
            "optimized for each die material, street width, and target kerf quality. "
            "Chipping at die edges — both front-side (silicon) and back-side — "
            "is a primary cause of die cracking in assembly. Blade lifetime: "
            "approximately 30–100 linear meters of cut. A 300mm fab with multiple "
            "product types may use dozens of blade specifications simultaneously."
        ),
        "used_in_steps": ["wafer_dicing"],
        "availability": "specialized",
        "key_suppliers": [
            {"name": "Disco Corporation", "country": "Japan", "market_share": "~70%",
             "notes": "Near-monopoly in wafer dicing blades and dicing saw equipment; both blade and saw sold together"},
            {"name": "Kulicke & Soffa (K&S)", "country": "USA/Singapore", "market_share": "~15%",
             "notes": "Dicing blades and wire bonding equipment"},
            {"name": "ADT (Advanced Dicing Technologies)", "country": "Israel", "market_share": "~10%",
             "notes": "Specialty dicing blades; thin blade specialist"},
        ],
        "supply_risks": [
            "Disco Corporation near-monopoly (~70%) in both dicing blades and the saws they run on — extreme single-company concentration",
            "Japan concentration — Disco is headquartered and manufactures primarily in Japan",
            "Diamond abrasive supply — synthetic diamond production concentrated in China (~80% of global synthetic industrial diamond)",
            "Blade specification qualification: optimizing a blade for a new die material or street width requires weeks of development",
            "Disco dicing blades are optimized for Disco saws; third-party blades on Disco equipment require qualification",
        ],
        "export_controls": {
            "status": "none",
            "detail": "Dicing blades are not export controlled. Dicing saws (capital equipment) may attract scrutiny for export to certain destinations.",
            "eccn": "EAR99",
        },
        "grey_market_risk": "low",
        "grey_market_detail": (
            "Grey market activity in dicing blades is low — blades are consumables with "
            "clear lifetime limits. The main risk is use of incorrect or unqualified blade "
            "specifications that cause excessive chipping, reducing die yield in assembly."
        ),
        "critical_mineral": False,
        "geographic_concentration": "Japan dominant (Disco ~70%); USA/Singapore ~15%; Israel ~10%",
        "hs_codes": ["8202.39", "6804.21"],
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
