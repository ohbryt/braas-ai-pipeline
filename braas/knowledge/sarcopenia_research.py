"""
Sarcopenia and Myostatin Inhibition Drug Development Research
=============================================================

This module provides comprehensive research knowledge on sarcopenia
(age-related muscle loss) and myostatin inhibition as a therapeutic strategy.

Author: BRAAS AI Pipeline Team
Version: 1.0.0
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class DrugStatus(Enum):
    """Clinical trial status for myostatin inhibitors."""
    APPROVED = "approved"
    PHASE_3 = "phase_3"
    PHASE_2 = "phase_2"
    PHASE_1 = "phase_1"
    DISCONTINUED = "discontinued"
    HALTED = "halted"
    PRECLINICAL = "preclinical"


class MechanismType(Enum):
    """Mechanism types for myostatin inhibition."""
    MYOSTATIN_ANTIBODY = "myostatin_antibody"
    ACTRII_ANTIBODY = "actrii_antibody"
    KINASE_INHIBITOR = "kinase_inhibitor"
    GENE_THERAPY = "gene_therapy"
    SMALL_MOLECULE = "small_molecule"
    NATURAL_PRODUCT = "natural_product"


# =============================================================================
# MYOSTATIN BIOLOGY
# =============================================================================

MYOSTATIN_BIOLOGY: Dict[str, Any] = {
    "gene_info": {
        "gene_symbol": "MSTN",
        "gene_name": "Myostatin",
        "chromosome": "2q32.2",
        "exons": 3,
        "mRNA_length": "2,308 bp",
        "protein_length": "375 amino acids",
        "uniprot_id": "O14793",
        "refseq_nucleotide": "NM_005259.3",
        "refseq_protein": "NP_005250.1"
    },
    "protein_structure": {
        "superfamily": "TGF-beta (Transforming Growth Factor Beta)",
        "family": "TGF-beta family, BMP subfamily",
        "molecular_weight": "~42.8 kDa (mature dimer)",
        "domain_structure": {
            "signal_peptide": "1-18 (aa)",
            "propeptide": "19-263 (aa)",
            "latency_associated_peptide": "19-263 (aa)",
            "cleavage_site": "QIPKACVR (263-270)",
            "mature_peptide": "271-375 (aa)",
            "cysteine_knot": "311-375 (aa)"
        },
        "structural_features": [
            "Cystine knot motif (defining feature of TGF-beta family)",
            "Homodimer structure (active form)",
            "N-linked glycosylation sites at N-157 and N-227",
            "Disulfide bonds: Cys-315, Cys-371 (inter-chain), Cys-340, Cys-347 (intra-chain)"
        ],
        "topology": "TGF-beta fold with fingers, wrists, and thumb-like regions"
    },
    "signaling_pathway": {
        "pathway_name": "SMAD2/3 Canonical Signaling",
        "receptor_complex": {
            "type_i_receptor": "ALK4 (Activin receptor-like kinase 4) / ALK5",
            "type_ii_receptor": "ActRIIB (Activin receptor type IIB)",
            "co_receptor": "Betaglycan (optional)"
        },
        "cascade": [
            "1. Myostatin binds ActRIIB (type II receptor)",
            "2. ActRIIB recruits and phosphorylates ALK4/5 (type I receptor)",
            "3. ALK4/5 phosphorylates SMAD2/3 at C-terminal serines",
            "4. p-SMAD2/3 forms complex with SMAD4",
            "5. SMAD4-pSMAD2/3 translocates to nucleus",
            "6. Nuclear complex activates muscle-specific gene transcription",
            "7. Result: muscle protein degradation, reduced protein synthesis, atrophy"
        ],
        "negative_regulators": [
            "Follistatin (binds myostatin, blocks receptor interaction)",
            "Myostatin propeptide (binds mature myostatin, maintains latency)",
            "GDF-11 (binds same receptors, opposite effect on muscle)",
            "FLRG (Follistatin-related gene protein)",
            "LTBP (Latent TGF-beta binding protein)"
        ],
        "target_genes": [
            "Atrogin-1 (Fbxo32) - ubiquitin ligase, promotes proteolysis",
            "MuRF-1 (Trim63) - ubiquitin ligase, targets sarcomeric proteins",
            "MyoD - myogenic differentiation factor (suppressed by myostatin)",
            "Myogenin - muscle differentiation marker",
            "IGF-1 - insulin-like growth factor (suppressed)"
        ]
    },
    "natural_inhibitors": {
        "follistatin": {
            "description": "Glycoprotein that binds and neutralizes myostatin",
            "mechanism": "Direct binding to myostatin, blocks ActRIIB interaction",
            "effect": "Muscle hypertrophy in transgenic mice (2-3x muscle mass)",
            "gene": "FST (chromosome 5)",
            "therapeutic_approach": "Follistatin gene therapy (AAV-mediated)"
        },
        "gdf11": {
            "description": "Growth differentiation factor 11, myostatin analog",
            "mechanism": "Binds ActRIIB/ALK4 but induces SMAD2/3 differently",
            "effect": "Age-related muscle decline; opposite to myostatin in some contexts",
            "note": "Paradoxically can cause muscle loss at high concentrations"
        },
        "myostatin_propeptide": {
            "description": "N-terminal propeptide cleaved during processing",
            "mechanism": "Non-covalently binds mature myostatin, maintains latent complex",
            "effect": "Endogenous inhibitor; mutation causes myostatin activation",
            "therapeutic_approach": "Propeptide mimetics, propeptide antibodies"
        }
    },
    "biological_function": {
        "normal_role": "Negative regulator of skeletal muscle growth",
        "tissue_specificity": "Expressed predominantly in skeletal muscle",
        "temporal_expression": "Highest during embryonic development, continues postnatally",
        "knockout_phenotype": {
            "organism": "Mouse",
            "effect": "40% increase in muscle mass (double-muscling)",
            "mechanism": "Increased fiber number (hyperplasia) and fiber size (hypertrophy)"
        },
        "physiological_role": [
            "Limits muscle size after development",
            "Regulates muscle protein turnover",
            "Modulates satellite cell activity",
            "Controls muscle fiber type composition"
        ]
    }
}


# =============================================================================
# SARCOPENIA DISEASE OVERVIEW
# =============================================================================

SARCOPENIA_DISEASE: Dict[str, Any] = {
    "definition": {
        "ewgsop_definition": "Progressive and generalized loss of skeletal muscle mass and strength",
        "iwgscp_definition": "Age-associated muscle changes meeting certain thresholds",
        "falls_related": "Key risk factor for falls, fractures, and loss of independence"
    },
    "pathophysiology": {
        "primary_mechanisms": [
            {
                "name": "Satellite Cell Dysfunction",
                "description": "Decline in muscle satellite cells (muscle stem cells)",
                "effect": "Reduced regenerative capacity, impaired repair",
                "markers": ["Pax7+ cells reduced 30-50% in elderly", "Satellite cell proliferation reduced"]
            },
            {
                "name": "Mitochondrial Decline",
                "description": "Age-related mitochondrial dysfunction",
                "effect": "Reduced ATP production, increased oxidative stress",
                "markers": ["Complex I-IV activity decreased 20-40%", "mtDNA mutations accumulate"]
            },
            {
                "name": "Anabolic Resistance",
                "description": "Impaired response to protein/amino acid stimulation",
                "effect": "Reduced protein synthesis despite adequate nutrition",
                "mechanism": ["mTOR signaling impairment", "IRS-1 dysregulation", "Akt phosphorylation reduced"]
            },
            {
                "name": "Systemic Inflammation",
                "description": "Chronic low-grade inflammation (inflammaging)",
                "effect": "Muscle catabolism, satellite cell senescence",
                "markers": ["IL-6 elevated", "TNF-alpha elevated", "CRP elevated", "IL-1beta elevated"]
            },
            {
                "name": "Neuromuscular Junction Degeneration",
                "description": "Denervation of muscle fibers",
                "effect": "Fiber type switching (IIb to IIa), weakness",
                "mechanism": ["Motor neuron loss", "NMJ fragmentation"]
            },
            {
                "name": "Hormonal Changes",
                "description": "Decline in anabolic hormones",
                "effect": "Reduced muscle protein synthesis",
                "factors": ["Testosterone 30-40% decline", "GH/IGF-1 decline", "Cortisol increase"]
            }
        ],
        "molecular_markers": [
            "Increased myostatin expression (2-3x higher in elderly muscle)",
            "Increased MurF-1 and Atrogin-1 expression",
            "Decreased Akt/mTOR phosphorylation",
            "Increased autophagy markers (LC3, Beclin-1)",
            "Senescence markers (p16, p21 elevated in satellite cells)"
        ]
    },
    "epidemiology": {
        "prevalence": {
            "age_60_70": "10-15%",
            "age_over_70": "50%+",
            "overall_elderly": "~50 million worldwide (estimated 200 million by 2050)"
        },
        "impact": [
            "Falls (1/3 of elderly >65 fall annually)",
            "Fractures (hip fracture mortality 20-30% at 1 year)",
            "Loss of independence",
            "Sarcopenia-related healthcare costs $20-40B annually (US)",
            "Increased mortality risk (HR 1.5-3.0)"
        ]
    },
    "current_treatment_landscape": {
        "approved_pharmacotherapies": "NONE (no drugs approved specifically for sarcopenia)",
        "interventions": {
            "resistance_exercise": {
                "efficacy": "Gold standard, 10-30% strength improvement",
                "limitation": "Difficult for frail elderly, requires adherence"
            },
            "protein_supplementation": {
                "efficacy": "1.0-1.5 g/kg/day recommended",
                "agents": ["Leucine-rich whey protein", "Creatine", "HMB (beta-hydroxy beta-methylbutyrate)"],
                "limitation": "Anabolic resistance limits effectiveness"
            },
            "vitamin_d": {
                "efficacy": "Improves strength when deficient",
                "target": "Serum 25(OH)D > 30 ng/mL",
                "limitation": "Limited benefit if not deficient"
            },
            "hormone_therapy": {
                "testosterone": {
                    "efficacy": "Modest improvement in muscle mass",
                    "limitation": "Cardiovascular risk, prostate concerns"
                },
                "gh_therapy": {
                    "efficacy": "Increases muscle mass but not strength",
                    "limitation": "Side effects, cost, not approved for sarcopenia"
                }
            }
        }
    },
    "market_analysis": {
        "market_size_2023": "$1.2B (global)",
        "market_size_2030_projection": "$2.8B (global)",
        "cagr": "10.5%",
        "key_drivers": [
            "Aging population (global demographic shift)",
            "Unmet medical need (no approved drugs)",
            "Healthcare cost burden of sarcopenia complications",
            "Increased awareness and screening",
            "Potential pipeline success"
        ],
        "competitive_landscape": "Fragmented, no dominant player",
        "strategic_opportunities": [
            "First-to-market myostatin inhibitor",
            "Combination therapy approaches",
            "Biomarker-driven patient selection",
            "Novel mechanisms beyond myostatin"
        ]
    }
}


# =============================================================================
# DRUG TARGET LANDSCAPE
# =============================================================================

@dataclass
class DrugCandidate:
    """Represents a drug candidate in the myostatin inhibition space."""
    name: str
    company: str
    mechanism: str
    mechanism_type: MechanismType
    stage: str
    status: DrugStatus
    indication: str
    route: str
    key_data: Optional[str] = None
    clinical_trial_id: Optional[str] = None
    status_note: Optional[str] = None


DRUG_TARGET_LANDSCAPE: List[DrugCandidate] = [
    DrugCandidate(
        name="Apitegromab (SRK-015)",
        company="Scholar Rock",
        mechanism="Anti-myostatin propeptide antibody; binds latency-associated propeptide",
        mechanism_type=MechanismType.MYOSTATIN_ANTIBODY,
        stage="Phase 3",
        status=DrugStatus.PHASE_3,
        indication="Sarcopenia",
        route="Subcutaneous",
        key_data="TOPAZA trial (Phase 3): Primary endpoint 6MWT improvement of 22.6m (p=0.045) at Week 24; Significant lean body mass increase; Positive 2022 results",
        clinical_trial_id="NCT04359455"
    ),
    DrugCandidate(
        name="Bimagrumab (BM-003)",
        company="Novartis / MediGene",
        mechanism="Anti-ActRIIA/B antibody; blocks myostatin and activin A binding",
        mechanism_type=MechanismType.ACTRII_ANTIBODY,
        stage="Phase 2",
        status=DrugStatus.PHASE_2,
        indication="Sarcopenia/Type 2 Diabetes",
        route="Intravenous",
        key_data="Phase 2: 10.8% increase in lean body mass at 24 weeks; 6MWT improved 31.8m",
        clinical_trial_id="NCT03571659"
    ),
    DrugCandidate(
        name="LY2495655 (Basimi)",
        company="Eli Lilly",
        mechanism="Anti-myostatin antibody",
        mechanism_type=MechanismType.MYOSTATIN_ANTIBODY,
        stage="Phase 2",
        status=DrugStatus.PHASE_2,
        indication="Sarcopenia, Cancer Cachexia",
        route="Subcutaneous",
        key_data="Phase 2 sarcopenia: Improved appendicular lean mass 0.98kg vs placebo; Development continued in oncology",
        clinical_trial_id="NCT01658055"
    ),
    DrugCandidate(
        name="Talditercept (ACE-249)",
        company="Acceleron Pharma (Merck)",
        mechanism="ALK4/Fc fusion protein; binds myostatin",
        mechanism_type=MechanismType.ACTRII_ANTIBODY,
        stage="Phase 2",
        status=DrugStatus.PHASE_2,
        indication="Sarcopenia",
        route="Subcutaneous",
        key_data="Phase 2: Showed trends in lean body mass increase; Development ongoing",
        clinical_trial_id="NCT03952129"
    ),
    DrugCandidate(
        name="Domagrozumab (PF-06252616)",
        company="Pfizer",
        mechanism="Anti-myostatin antibody",
        mechanism_type=MechanismType.MYOSTATIN_ANTIBODY,
        stage="Phase 2",
        status=DrugStatus.DISCONTINUED,
        indication="Duchenne Muscular Dystrophy",
        route="Intravenous",
        key_data="Phase 2 DMD: Did not meet primary endpoint (4DSTM muscle MRI); Discontinued 2018",
        clinical_trial_id="NCT02310763"
    ),
    DrugCandidate(
        name="Ataluren (PTC124)",
        company="PTC Therapeutics",
        mechanism="Small molecule; promotes read-through of premature stop codons",
        mechanism_type=MechanismType.SMALL_MOLECULE,
        stage="Phase 2/3",
        status=DrugStatus.HALTED,
        indication="Muscular Dystrophy",
        route="Oral",
        key_data="Originally for nonsense mutations in dystrophin; Also studied for myostatin; Halted due to futility",
        clinical_trial_id="NCT02396132"
    ),
    DrugCandidate(
        name="ACE-083",
        company="Acceleron Pharma",
        mechanism="Follistatin-Fc fusion protein; binds myostatin",
        mechanism_type=MechanismType.ACTRII_ANTIBODY,
        stage="Phase 2",
        status=DrugStatus.DISCONTINUED,
        indication="Focal muscle disorders (FSHD, ALS)",
        route="Intramuscular",
        key_data="Phase 2 FSHD: Showed local muscle hypertrophy; Discontinued 2019",
        clinical_trial_id="NCT02987871"
    ),
    DrugCandidate(
        name="Recifercept (FCRT-100)",
        company="Ferring Pharmaceuticals",
        mechanism="Decoy receptor (ActRIIB-Fc)",
        mechanism_type=MechanismType.ACTRII_ANTIBODY,
        stage="Preclinical",
        status=DrugStatus.PRECLINICAL,
        indication="Sarcopenia",
        route="Subcutaneous",
        key_data="Novel decoy receptor approach; Early development stage",
        clinical_trial_id=None
    ),
    DrugCandidate(
        name="Eteplirsen",
        company="Sarepta Therapeutics",
        mechanism="Antisense oligonucleotide; skips exon 51 in dystrophin",
        mechanism_type=MechanismType.SMALL_MOLECULE,
        stage="Approved",
        status=DrugStatus.APPROVED,
        indication="Duchenne Muscular Dystrophy",
        route="Intravenous",
        key_data="Approved 2016; Related therapeutic area; Demonstrates antisense feasibility",
        clinical_trial_id="NCT01396239"
    )
]


# =============================================================================
# MECHANISMS OF ACTION
# =============================================================================

MECHANISMS_OF_ACTION: Dict[str, Any] = {
    "antibody_based": {
        "anti_myostatin_antibodies": {
            "description": "Monoclonal antibodies targeting myostatin directly",
            "examples": ["LY2495655 (Lilly)", "Domagrozumab (Pfizer)"],
            "pros": ["High specificity", "Long half-life", "Subcutaneous administration"],
            "cons": ["Large molecule (IV/SC only)", "High development cost", "Immunogenicity risk"]
        },
        "anti_propeptide_antibodies": {
            "description": "Antibodies targeting myostatin propeptide to release inhibition",
            "examples": ["Apitegromab (SRK-015, Scholar Rock)"],
            "pros": ["Novel mechanism", "Potential for improved efficacy"],
            "cons": ["Novel mechanism = higher development risk"]
        },
        "actrii_receptor_antibodies": {
            "description": "Antibodies blocking ActRIIA and/or ActRIIB receptors",
            "examples": ["Bimagrumab (Novartis)", "ActRIIA antibodies"],
            "pros": ["Blocks multiple ligands (myostatin + activin A)", "Dual benefit"],
            "cons": ["Broader mechanism = more off-target effects potential"]
        }
    },
    "small_molecule_kinase_inhibitors": {
        "alk4_inhibitors": {
            "description": "Small molecules inhibiting ALK4 kinase activity",
            "examples": ["SB-431542", "SB-525334 (Pfizer)", "LDN-193189"],
            "mechanism": "Selective ALK4/5/7 inhibition blocks SMAD2/3 phosphorylation",
            "pros": ["Oral bioavailability possible", "Small molecule advantages"],
            "cons": ["Selectivity challenges", "TGF-beta family selectivity critical"]
        },
        "alk5_inhibitors": {
            "description": "Inhibitors of ALK5 (TBRI) kinase",
            "examples": ["Galunisertib (Eli Lilly)", "GW-788388"],
            "note": "ALK5 also signals in muscle; dual ALK4/5 inhibition may be needed"
        },
        "smad3_inhibitors": {
            "description": "Inhibitors of SMAD3 transcriptional activity",
            "examples": ["SIS3", "Alexidine"],
            "pros": ["Downstream of receptor", "Potential for combination"],
            "cons": ["Intracellular target", "Drug delivery challenges"]
        }
    },
    "gene_therapy_approaches": {
        "aav_follistatin": {
            "description": "AAV-mediated follistatin expression for durable myostatin inhibition",
            "examples": ["AAV1-CMV-follistatin (various academic groups)"],
            "pros": ["Durable expression", "One-time treatment potential", "Strong preclinical efficacy"],
            "cons": ["AAV immunogenicity", "Long-term expression concerns", "Regulatory complexity"]
        },
        "rna_interference": {
            "myostatin_siRNA": {
                "description": "SiRNA targeting myostatin mRNA for degradation",
                "examples": ["Dyanapro (Dynaligned), various academic constructs"],
                "pros": ["Specific gene silencing", "Potential for tissue targeting"],
                "cons": ["Delivery challenges", "Short-lived effect requiring repeat dosing"]
            },
            "antisense_oligos": {
                "description": "Antisense oligonucleotides targeting myostatin",
                "examples": ["Eteplirsen-class (Sarepta), various"],
                "pros": ["Validated chemistry", "Modifications for stability"],
                "cons": ["Delivery to muscle tissue challenging"]
            }
        }
    },
    "natural_products": {
        "curcumin": {
            "description": "Turmeric polyphenol with anti-inflammatory effects",
            "mechanism": "NF-kappaB inhibition reduces myostatin expression; Antioxidant effects",
            "evidence_level": "Preclinical (cell culture, mouse models)",
            "note": "Poor bioavailability; Formulation critical"
        },
        "resveratrol": {
            "description": "Red wine polyphenol; SIRT1 activator",
            "mechanism": "May reduce myostatin via SIRT1/AMPK pathways; Reduces inflammation",
            "evidence_level": "Preclinical",
            "note": "Similar bioavailability concerns as curcumin"
        },
        "catechins": {
            "description": "Green tea polyphenols (EGCG)",
            "mechanism": "AMPK activation; May counteract catabolic pathways",
            "evidence_level": "Preclinical"
        }
    }
}


# =============================================================================
# CLINICAL TRIAL INSIGHTS
# =============================================================================

CLINICAL_TRIAL_INSIGHTS: Dict[str, Any] = {
    "primary_endpoints": {
        "six_minute_walk_test": {
            "abbreviation": "6MWT",
            "description": "Distance walked in 6 minutes (functional capacity)",
            "unit": "meters",
            "mcw_change_minimal": "20-30m improvement considered clinically meaningful",
            "use_case": "Primary endpoint in Apitegromab TOPAZA trial"
        },
        "lean_body_mass": {
            "abbreviation": "LBM",
            "description": "Fat-free mass measured by DXA",
            "unit": "kg",
            "mcw_change_minimal": "0.5-1.0 kg improvement in sarcopenia trials",
            "use_case": "Widely used secondary endpoint"
        },
        "grip_strength": {
            "description": "Hand grip strength measurement",
            "unit": "kg or N",
            "mcw_change_minimal": "5-10% improvement from baseline",
            "use_case": "Common strength proxy"
        },
        "leg_strength": {
            "description": "Knee extension/flexion strength",
            "unit": "Nm or kg",
            "use_case": "Direct measure of lower extremity strength"
        },
        "spiroergometry": {
            "description": "VO2 max testing",
            "unit": "mL/kg/min",
            "use_case": "Cardiovascular fitness assessment"
        },
        "short_physical_performance_battery": {
            "abbreviation": "SPPB",
            "description": "Composite of balance, gait, chair stand tests",
            "range": "0-12",
            "mcw_change_minimal": "1 point improvement",
            "use_case": "Comprehensive functional assessment"
        }
    },
    "patient_populations": {
        "typical_enrollment": {
            "age_range": ">=65 years (some studies >=75)",
            "gender": "Both sexes, often slightly more females",
            "awm_criteria": "Appendicular lean mass >1 SD below young adult mean (DXA)",
            "strength_criteria": "Grip strength <20-30 kg (males), <15-20 kg (females)"
        },
        "exclusion_criteria": {
            "common": [
                "Active inflammatory disease",
                "Cancer (recent)",
                "Chronic kidney disease (eGFR <30)",
                "Liver disease",
                "Uncontrolled cardiovascular disease",
                "Recent fracture or surgery",
                "Metal implants (DXA interference)",
                "Insulin-dependent diabetes (some studies)"
            ]
        },
        "subgroup_populations": {
            "sarcopenic_obesity": "Muscle loss + increased fat mass",
            "cachexic_sarcopenia": "Disease-related muscle loss (COPD, cancer, CHF)",
            "dynapenic_sarcopenia": "Low strength but normal muscle mass"
        }
    },
    "combination_therapy_approaches": {
        "rationale": "Multifactorial pathogenesis suggests combination approaches",
        "potential_combinations": [
            "Myostatin inhibitor + resistance exercise",
            "Myostatin inhibitor + protein/leucine supplementation",
            "Myostatin inhibitor + vitamin D",
            "Myostatin inhibitor + anabolic agents (SARM, testosterone)",
            "Myostatin inhibitor + sarcopenia的其他 mechanism (AMPK activators, mTOR modulators)"
        ],
        "challenges": [
            "Regulatory pathway complexity",
            "Safety profile interactions",
            "Dosing optimization"
        ]
    }
}


# =============================================================================
# COMPETITIVE ANALYSIS TABLE
# =============================================================================

COMPOUND_ANALYSIS_TABLE: List[Dict[str, Any]] = [
    {
        "rank": 1,
        "compound": "Apitegromab (SRK-015)",
        "company": "Scholar Rock",
        "mechanism": "Anti-propeptide antibody",
        "stage": "Phase 3",
        "status": "Active",
        "key_data": "TOPAZA: +22.6m 6MWT (p=0.045)",
        "differentiation": "Novel mechanism targeting latent complex",
        "competitive_advantage": "Only Phase 3 myostatin inhibitor with positive results"
    },
    {
        "rank": 2,
        "compound": "Bimagrumab",
        "company": "MediGene (Novartis license)",
        "mechanism": "ActRIIA/B blocker",
        "stage": "Phase 2",
        "status": "Active",
        "key_data": "+10.8% LBM, +31.8m 6MWT",
        "differentiation": "Dual ligand blocking (myostatin + activin A)",
        "competitive_advantage": "Broader mechanism, metabolic benefits"
    },
    {
        "rank": 3,
        "compound": "LY2495655",
        "company": "Eli Lilly",
        "mechanism": "Anti-myostatin antibody",
        "stage": "Phase 2",
        "status": "Active",
        "key_data": "+0.98kg appendicular LBM",
        "differentiation": "Oncology-focused development",
        "competitive_advantage": "Large pharma resources"
    },
    {
        "rank": 4,
        "compound": "Talditercept",
        "company": "Acceleron/Merck",
        "mechanism": "ALK4-Fc fusion",
        "stage": "Phase 2",
        "status": "Active",
        "key_data": "LBM trending increase",
        "differentiation": "Receptor fusion mechanism",
        "competitive_advantage": "Distinct from antibody approaches"
    },
    {
        "rank": 5,
        "compound": "Domagrozumab",
        "company": "Pfizer",
        "mechanism": "Anti-myostatin antibody",
        "stage": "Phase 2",
        "status": "Discontinued",
        "key_data": "Failed primary endpoint in DMD",
        "differentiation": "N/A (discontinued)",
        "competitive_advantage": "N/A"
    },
    {
        "rank": 6,
        "compound": "ACE-083",
        "company": "Acceleron",
        "mechanism": "Follistatin-Fc",
        "stage": "Phase 2",
        "status": "Discontinued",
        "key_data": "Local hypertrophy in FSHD",
        "differentiation": "N/A (discontinued)",
        "competitive_advantage": "N/A"
    },
    {
        "rank": 7,
        "compound": "Recifercept",
        "company": "Ferring",
        "mechanism": "ActRIIB-Fc decoy",
        "stage": "Preclinical",
        "status": "Active",
        "key_data": "Early stage",
        "differentiation": "Decoy receptor approach",
        "competitive_advantage": "Novel structure"
    }
]


# =============================================================================
# KEY PATENTS AND IP LANDSCAPE
# =============================================================================

PATENT_LANDSCAPE: Dict[str, Any] = {
    "key_patents": [
        {
            "patent_id": "US patent 7,563,442",
            "title": "Myostatin antibodies and uses thereof",
            "holder": "Johns Hopkins University / Wyeth",
            "expiration": "2024-2025 (expired)",
            "relevance": "Foundational myostatin antibody patents"
        },
        {
            "patent_id": "US patent 8,445,632",
            "title": "Method for treating muscle atrophy",
            "holder": "MediGene (formerly Novartis)",
            "expiration": "2030+",
            "relevance": "ActRIIB antibody patents for muscle disorders"
        },
        {
            "patent_id": "US patent 10,293,258",
            "title": "Anti-myostatin antibodies with improved properties",
            "holder": "Eli Lilly",
            "expiration": "2036+",
            "relevance": "LY2495655 related"
        },
        {
            "patent_id": "US patent 11,124,418",
            "title": "Method of treating sarcopenia using anti-myostatin propeptide antibodies",
            "holder": "Scholar Rock",
            "expiration": "2037+",
            "relevance": "Apitegromab composition of matter"
        },
        {
            "patent_id": "US patent 11,459,348",
            "title": "Follistatin gene therapy for muscle disorders",
            "holder": "University of Washington",
            "expiration": "2035+",
            "relevance": "AAV-follistatin IP"
        }
    ],
    "ip_strategic_considerations": [
        "Myostatin propeptide mechanism may provide freedom to operate around earlier antibody patents",
        "ActRIIB patents heavily licensed; freedom to operate challenging",
        "Gene therapy approaches have distinct IP landscape",
        "Small molecule kinase inhibitors likely unencumbered"
    ]
}


# =============================================================================
# UNMET NEEDS AND OPPORTUNITIES
# =============================================================================

UNMET_NEEDS: Dict[str, Any] = {
    "clinical_unmet_needs": [
        {
            "need": "Improved efficacy over current best-in-class",
            "description": "Apitegromab 22.6m improvement may not be clinically transformative",
            "opportunity": "Higher efficacy compounds or combination approaches"
        },
        {
            "need": "Oral administration option",
            "description": "All current candidates require injection (IV/SC)",
            "opportunity": "Oral small molecule ALK4/5 inhibitors"
        },
        {
            "need": "Durable effects",
            "description": "Antibodies require repeat dosing; gene therapy potential but regulatory complexity",
            "opportunity": "Long-acting formulations or one-time gene therapy"
        },
        {
            "need": "Muscle strength improvement",
            "description": "Many candidates show LBM increase but not translated to strength",
            "opportunity": "Better understanding of LBM vs strength disconnect"
        },
        {
            "need": "Patient stratification",
            "description": "Heterogeneous population; no validated biomarkers",
            "opportunity": "Biomarker-driven enrichment strategies"
        }
    ],
    "differentiation_opportunities": [
        {
            "area": "Novel mechanisms",
            "approaches": [
                "SAT1 (spermidine acetyltransferase) targeting",
                "GDF-8/11 pharmacokinetics manipulation",
                "Satellite cell activation (Pax7 targeting)",
                "Mitochondrial biogenesis enhancement",
                "AMPK activator combination"
            ]
        },
        {
            "area": "Improved delivery",
            "approaches": [
                "Oral bioavailability optimization",
                "Tissue-targeted delivery (muscle-specific peptides)",
                "Cell-penetrating conjugates"
            ]
        },
        {
            "area": "Combination therapy",
            "approaches": [
                "Myostatin inhibitor + exercise mimetic",
                "Myostatin inhibitor + anabolic steroid",
                "Myostatin inhibitor + protein metabolism optimizer"
            ]
        },
        {
            "area": "Biomarker strategy",
            "approaches": [
                "Myostatin serum levels for patient selection",
                "Genetic polymorphisms for response prediction",
                "Real-time muscle mass monitoring"
            ]
        }
    ],
    "market_opportunities": [
        "Sarcopenia (primary indication) - $2.8B by 2030",
        "Cancer cachexia - $2B+ addressable market",
        "Duchenne Muscular Dystrophy - rare disease incentives",
        "COPD-related muscle loss",
        "Chronic kidney disease sarcopenia",
        "Geriatric frailty"
    ]
}


# =============================================================================
# SUMMARY DATA
# =============================================================================

def get_research_summary() -> Dict[str, Any]:
    """Returns a summary dictionary of all research knowledge."""
    return {
        "myostatin_biology": MYOSTATIN_BIOLOGY,
        "sarcopenia_disease": SARCOPENIA_DISEASE,
        "drug_target_landscape": [d.__dict__ for d in DRUG_TARGET_LANDSCAPE],
        "mechanisms_of_action": MECHANISMS_OF_ACTION,
        "clinical_trial_insights": CLINICAL_TRIAL_INSIGHTS,
        "competitive_analysis": COMPOUND_ANALYSIS_TABLE,
        "patent_landscape": PATENT_LANDSCAPE,
        "unmet_needs": UNMET_NEEDS
    }


if __name__ == "__main__":
    import json
    summary = get_research_summary()
    print(json.dumps(summary, indent=2, default=str))
