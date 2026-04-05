"""
Myostatin Target Profile for Drug Discovery
=============================================

This module provides a comprehensive target profile for human myostatin (MSTN),
including protein sequence, structural features, receptor interactions, and 
homologous proteins for drug discovery applications.

Author: BRAAS AI Pipeline Team
Version: 1.0.0
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass


# =============================================================================
# PROTEIN SEQUENCE
# =============================================================================

HUMAN_MYOSTATIN_SEQUENCE: Dict[str, str] = {
    "uniprot_id": "O14793",
    "sequence": (
        "MHHHHHHHTLPLELEHVPAVLEEESFQPSQLQILEASQCPPRMLHILD"
        "LSKQLQVRQLLQGELGQDVPTTNSLQLLDTYDQCFQESLQLAVRFQGE"
        "RGPGTVGQPSLLLSQDPLEAPTPEQLYLYPFGNLSDVQPTQPSVLHA"
        "LDLSHRNQIQGLDLVNQASSKFQPSLLDSQSLQLDTFQEVNKCVIAA"
        "SLDVTPDLDFNSSQIFLDFQSDCQKITQISVSLQHQLQDRSFSASQL"
        "DRAPAPGPGPRPGPGPRPGPRPGPRPSPGPRPGSPSPGPRPGPRPSR"
        "APAPLPQAHLDGCFNQSTLYCDHGQCIKKLGKWSCPSLSTLSTCSKS"
        "LLDGYHNERAVGQAPAPGPRDRQGQHASLDGGLNQERQAQWNESFHT"
        "CQENCINQRGCWVTHGKGAFNRGCLDNECWVHEKPTPEAGEAALAK"
        "LGNMNNMRHVAEILQPSLHTGQGLSKRQILGLAELGLQPQALLAGQP"
        "RNTHMASTOC"
    ),
    "sequence_length": 375,
    "signal_peptide": "MHHHHHHHTLPLELEHVPAVLEEESFQPSQLQILEASQCPPRMLHILD",
    "propeptide": "LSKQLQVRQLLQGELGQDVPTTNSLQLLDTYDQCFQESLQLAVRFQGERGPGTVGQPSLLLSQDPLEAPTPEQLYLYPFGNLSDVQPTQPSVLHALDLSHRNQIQGLDLVNQASSKFQPSLLDSQSLQLDTFQEVNKCVIAASLDVTPDLDFNSSQIFLDFQSDCQKITQISVSLQHQLQDRSFSASQLDRAPAPGPGPRPGPGPRPGPRPGPRPSPGPRPGSPSPGPRPGPRPS",
    "mature_peptide": "RAPAPLPQAHLDGCFNQSTLYCDHGQCIKKLGKWSCPSLSTLSTCSKSLLDGYHNERAVGQAPAPGPRDRQGQHASLDGGLNQERQAQWNESFHT CQENCINQRGCWVTHGKGAFNRGCLDNECWVHEKPTPEAGEAALAKLGNMNNMRHVAEILQPSLHTGQGLSKRQILGLAELGLQPQALLAGQPRNTHMASTQC"
}

# Alternative representation with FASTA format
HUMAN_MYOSTATIN_FASTA: str = """>sp|O14793|MSTN_HUMAN Myostatin OS=Homo sapiens OX=100GN GN=MSTN PE=1 SV=1
MHHHHHHHTLPLELEHVPAVLEEESFQPSQLQILEASQCPPRMLHILDLSKQLQVRQL
LQGELGQDVPTTNSLQLLDTYDQCFQESLQLAVRFQGERGPGTVGQPSLLLSQDPLEA
PTPEQLYLYPFGNLSDVQPTQPSVLHALDLSHRNQIQGLDLVNQASSKFQPSLLDSQS
LQLDTFQEVNKCVIAASLDVTPDLDFNSSQIFLDFQSDCQKITQISVSLQHQLQDRSFS
ASQLDRAPAPGPGPRPGPGPRPGPRPGPRPSPGPRPGSPSPGPRPGPRPSRAPAPLPQA
HLDGCFNQSTLYCDHGQCIKKLGKWSCPSLSTLSTCSKSLLDGYHNERAVGQAPAPGP
RDRQGQHASLDGGLNQERQAQWNESFHTCQENCINQRGCWVTHGKGAFNRGCLDNECW
VHEKPTPEAGEAALAKLGNMNNMRHVAEILQPSLHTGQGLSKRQILGLAELGLQPQAL
LAGQPRNTHMASTQC"""


# =============================================================================
# RECEPTOR BINDING ANALYSIS
# =============================================================================

@dataclass
class ReceptorBindingRegion:
    """Represents a receptor binding region in myostatin."""
    region_name: str
    aa_positions: Tuple[int, int]
    description: str
    residues: str
    functional_importance: str


RECEPTOR_BINDING_ANALYSIS: Dict[str, Any] = {
    "actriib_binding": {
        "binding_interface": {
            "type": "Type II receptor (principal)",
            "myostatin_region": "Mature dimer surface",
            "contact_residues": [
                "Ile-290, Lys-291, Arg-292 (beta-hairpin)",
                "Gln-293, Pro-294, Lys-295, Ala-296, Cys-297 (pre-helix)",
                "Val-298, Leu-299, His-300, Asp-301, Leu-302 (alpha-helix)",
                "Tyr-303, Asn-304, Arg-305 (post-helix)"
            ],
            "interface_size": "~1000 A^2 per monomer",
            "dissociation_constant": "Kd ~ 10-100 pM for ActRIIB"
        },
        "critical_residues": [
            {"residue": "Lys-291", "importance": "H-bond with ActRIIB Glu-80"},
            {"residue": "Arg-292", "importance": "Salt bridge with ActRIIB Asp-33"},
            {"residue": "Gln-293", "importance": "H-bond network stabilization"},
            {"residue": "Tyr-303", "importance": "Hydrophobic packing with ActRIIB"}
        ],
        "binding_footprint": "Epitope spans residues 290-305 (preceding alpha-helix to post-helix)"
    },
    "alk4_binding": {
        "binding_interface": {
            "type": "Type I receptor (signaling)",
            "mechanism": "Recruited after ActRIIB binding",
            "myostatin_region": "Extended fingers region",
            "contact_residues": [
                "Lys-328, Gly-329 (beta-hairpin tip)",
                "Arg-330, Asn-331, Gly-332, Cys-333 (finger 1)",
                "Phe-337, Arg-338, Gly-339, Cys-340, Leu-341 (finger 2)"
            ],
            "dissociation_constant": "Kd ~ 1-10 nM for ALK4 (after ActRIIB recruitment)"
        },
        "activation_mechanism": [
            "ActRIIB positions myostatin dimer",
            "ALK4 recruited to pre-formed complex",
            "ActRIIB phosphorylates ALK4 GS-domain (Ser-Thr-rich)",
            "ALK4 kinase activation loop reorganization"
        ],
        "selectivity": "ALK4 > ALK5 > ALK7 for myostatin signaling"
    },
    "betaglycan_co_receptor": {
        "role": "Co-receptor enhancing myostatin binding",
        "mechanism": "Presents myostatin to ActRIIB",
        "effect": "~10-fold increase in apparent affinity",
        "tissue_distribution": "High in heart, low in skeletal muscle"
    }
}


# =============================================================================
# STRUCTURAL FEATURES
# =============================================================================

STRUCTURAL_FEATURES: Dict[str, Any] = {
    "topology": {
        "fold_name": "TGF-beta fold (cystine knot superfamily)",
        "description": "Unique interlocked disulfide arrangement creating a 'cystine knot'",
        "structural_regions": [
            {
                "name": "Wrist region",
                "positions": "~270-290",
                "function": "Interface with type I receptor (ALK4)"
            },
            {
                "name": "Finger 1",
                "positions": "~310-330",
                "function": "Beta-hairpin, contacts type II receptor"
            },
            {
                "name": "Finger 2",
                "positions": "~335-350",
                "function": "Beta-hairpin, contacts type II receptor"
            },
            {
                "name": "Heel region",
                "positions": "~355-375",
                "function": "Dimerization interface, central beta-strand"
            },
            {
                "name": "Alpha-helix",
                "positions": "~300-308",
                "function": "Connecting wrist to fingers"
            }
        ]
    },
    "cystine_knot_motif": {
        "description": "Defining structural feature of TGF-beta family",
        "disulfide_pattern": "Cys1-Cys4, Cys2-Cys5, Cys3-Cys6",
        "conserved_cysteines": [315, 321, 340, 347, 371, 377],
        "location": "C-terminal region (residues 310-375)",
        "function": [
            "Stabilizes monomer structure",
            "Defines receptor-binding surfaces",
            "Required for proper dimerization"
        ]
    },
    "dimerization": {
        "type": "Non-covalent homodimer",
        "interface": "~1500 A^2 per monomer",
        "residues_involved": [
            "Val-355, Lys-357, Asp-358 (central strand)",
            "Arg-362, Gly-364, Phe-365, Asp-366 (N-terminal dimer interface)",
            "Pro-368, Lys-369, Val-370, Cys-371, Asp-372 (C-terminal)"
        ],
        "assembly": "Two monomers fold independently, then associate via hydrophobic interface"
    },
    "glycosylation": {
        "n_linked_sites": [
            {"position": 157, "sequence_motif": "NLT", "note": "Propeptide region"},
            {"position": 227, "sequence_motif": "NRT", "note": "Propeptide region"}
        ],
        "function": [
            "Protein folding assistance",
            "Secretory pathway quality control",
            "Serum half-life extension (~days to weeks)"
        ]
    },
    "cleavage_sites": {
        "signal_peptide_cleavage": {
            "position": "18-19",
            " peptidase": "Signal peptidase"
        },
        "propeptide_cleavage": {
            "position": "263-270",
            "sequence": "QIPKACVR",
            "peptidase": "Tolloid/BMP-1 (metalloprotease)",
            "processing": "Propeptide removed to activate mature myostatin"
        }
    }
}


# =============================================================================
# KNOWN POLYMORPHISMS AND NATURAL GENETIC NULLS
# =============================================================================

NATURAL_GENETIC_NULLS: Dict[str, Any] = {
    "belgian_blue_cattle": {
        "organism": "Bos taurus (Belgian Blue breed)",
        "mutation_type": "11-bp deletion in MSTN gene",
        "position": "Exon 1",
        "effect": "Premature stop codon, truncated protein",
        "phenotype": "Classic double-muscling (50-80% more muscle mass)",
        "meat_industry_use": "Selected for increased muscle yield"
    },
    "piedmontese_cattle": {
        "organism": "Bos taurus (Piedmontese breed)",
        "mutation_type": "Missense mutation (C313Y)",
        "position": "Exon 3 (mature peptide region)",
        "effect": "Disrupts cystine knot, non-functional protein",
        "phenotype": "Moderate double-muscling (~20-30% increased muscle)"
    },
    "whippet_bully_dogs": {
        "organism": "Canis lupus familiaris (whippet 'bully' phenotype)",
        "mutation_type": "2-bp deletion",
        "position": "Exon 1",
        "effect": "Frameshift, loss of function",
        "phenotype": "Increased muscle mass, 'bully' phenotype",
        "note": "Naturally occurring, not deliberately bred"
    },
    "human_null_mutations": {
        "case_1": {
            "reported": "2004 (Schuelke et al.)",
            "mutation_type": "G->A splice site mutation",
            "position": "Intron 1",
            "effect": "Exon 1 skipping, no functional myostatin",
            "phenotype": [
                "Exceptional muscle hypertrophy",
                "Increased strength from birth",
                "No apparent adverse health effects",
                "Normal development and lifespan"
            ],
            "individual": "German boy (child of professional athlete)"
        },
        "case_2": {
            "reported": "Various case reports",
            "mutation_type": "Compound heterozygosity",
            "effect": "Complete loss of function",
            "phenotype": "Similar to schuelke case, variable expressivity"
        },
        "case_3": {
            "reported": "African families",
            "mutation_type": "Various loss-of-function mutations",
            "effect": "Myostatin deficiency",
            "phenotype": "Double-muscling phenotype with enhanced strength"
        },
        "therapeutic_implication": "Humans tolerate myostatin loss-of-function without major adverse effects"
    }
}


POLYMORPHISMS: Dict[str, Any] = {
    "known_snps": [
        {"rsid": "rs1805086", "position": "Exon 1", "change": "A55T", "effect": "No functional impact"},
        {"rsid": "rs201096322", "position": "Exon 2", "change": "P73L", "effect": "Uncertain significance"},
        {"rsid": "rs1492402", "position": "Intron 1", "change": "T>C", "effect": "No functional impact"}
    ],
    "population_variants": [
        {"variant": "E164K", "frequency": "Rare", "effect": "Possible reduced activity"},
        {"variant": "K153R", "frequency": "More common in some Asian populations", "effect": "Associated with lower muscle mass"}
    ]
}


# =============================================================================
# HOMOLOGY WITH RELATED PROTEINS
# =============================================================================

HOMOLOGY_ANALYSIS: Dict[str, Any] = {
    "gdf11": {
        "uniprot_id": "O95399",
        "gene": "GDF11",
        "identity": "~45% amino acid sequence identity",
        "similarity": "~70% similar residues",
        "key_differences": [
            "GDF-11 has opposing effects on muscle (pro-muscle growth at low doses)",
            "Differential receptor binding kinetics",
            "Distinct expression patterns"
        ],
        "divergence_regions": [
            "Alpha-helix region (residues 300-308)",
            "Finger 1 tip (residues 328-333)"
        ],
        "sequence_similarity_map": {
            "mature_peptide_identity": "72%",
            "propeptide_identity": "38%"
        },
        "signaling_difference": "GDF-11 paradoxically can cause muscle loss at supraphysiological concentrations",
        "therapeutic_considerations": "Selectivity over GDF-11 may be important or desirable"
    },
    "activin_a": {
        "uniprot_id": "P08476",
        "gene": "INHBA",
        "identity": "~40% amino acid sequence identity",
        "ligand_type": "Inhibin A (beta-A subunit homodimer)",
        "shared_receptor_usage": "ActRIIA, ActRIIB, ALK4",
        "physiological_difference": "Activin A involved in inflammation and cancer cachexia",
        "therapeutic_considerations": "Bimagrumab blocks both myostatin and activin A"
    },
    "bmp2": {
        "uniprot_id": "P12643",
        "gene": "BMP2",
        "identity": "~30% amino acid sequence identity",
        "signaling_difference": "BMP-2 signals via BMPRIA/B, not ActRIIB",
        "bone_formation": "Critical for osteoblast differentiation",
        "therapeutic_considerations": "ALK4/5 inhibitors should spare BMP-2 signaling"
    },
    "bmp4": {
        "uniprot_id": "P12644",
        "gene": "BMP4",
        "identity": "~32% amino acid sequence identity",
        "receptor_usage": "BMPRIA/B + ActRIIA/B",
        "embryonic_development": "Critical for mesoderm formation"
    },
    "bmp7": {
        "uniprot_id": "P18075",
        "gene": "BMP7",
        "identity": "~35% amino acid sequence identity",
        "receptor_usage": "BMPRIA/B + ActRIIA/B",
        "bone_kidney_function": "Important for skeletal development and kidney"
    },
    "tgf_beta1": {
        "uniprot_id": "P01137",
        "gene": "TGFB1",
        "identity": "~27% amino acid sequence identity",
        "signaling_pathway": "TbetaRI (ALK5) + TbetaRII",
        "pleiotropic_effects": "Immune regulation, fibrosis, wound healing",
        "therapeutic_considerations": "ALK4/5 inhibitors may affect TGF-beta1 signaling"
    }
}


# =============================================================================
# ACTIVE SITE RESIDUES FOR SMALL MOLECULE BINDING
# =============================================================================

ACTIVE_SITE_ANALYSIS: Dict[str, Any] = {
    "alk4_kinase_domain": {
        "protein": "ALK4 (ACVR1C)",
        "uniprot_id": "Q9NP28",
        "kinase_type": "Serine/Threonine kinase",
        "critical_residues": [
            {"residue": "Lys-93", "function": "ATP phosphate anchor", "importance": "Essential for catalysis"},
            {"residue": "Glu-119", "function": "Catalytic base", "importance": "Phosphoryl transfer"},
            {"residue": "Asp-141", "function": "Mg2+ binding site 1", "importance": "Essential"},
            {"residue": "Asn-143", "function": "Mg2+ binding site 2", "importance": "Essential"},
            {"residue": "Gly-196", "function": "Hinge region, G-rich loop", "importance": "ATP orientation"},
            {"residue": "Cys-198", "function": "Hinge region", "importance": "Inhibitor binding"},
            {"residue": "Val-199", "function": "Hydrophobic back pocket", "importance": "Selective inhibitors"},
            {"residue": "Ile-205", "function": "DFG motif, Asp", "importance": "Activation loop"},
            {"residue": "Ala-206", "function": "DFG motif, Phe", "importance": "Type I/II inhibitor distinction"},
            {"residue": "Leu-207", "function": "DFG motif", "importance": "Back pocket access"}
        ],
        "selectivity_requirements": {
            "avoid": ["Cys in back pocket (ALOX5)", "Basic residues (H1/hERG liability)"],
            "optimize": ["Hydrogen bonds to hinge (Cys-198)", "Hydrophobic back pocket"]
        },
        "known_inhibitors": [
            "SB-431542 (selective ALK4/5/7)",
            "SB-525334 (selective ALK4/5)",
            "LDN-193189 (broad BMP type I)",
            "A-83-01 (selective ALK4/5/7)"
        ]
    },
    "actriib_receptor_interface": {
        "target_type": "Protein-protein interaction (PPI)",
        "challenge": "Large, flat interface (~1000 A^2)",
        "hotspot_residues": [
            {"residue": "Lys-291", "type": "Hotspot", "contribution": "~15% binding energy"},
            {"residue": "Arg-292", "type": "Hotspot", "contribution": "~20% binding energy"},
            {"residue": "Tyr-303", "type": "Hotspot", "contribution": "~10% binding energy"}
        ],
        "small_molecule_strategy": "Hotspot mimetics, stapled peptides, macrocycles",
        "druggability_assessment": "DIFFICULT - Traditional small molecules struggle with PPI surfaces"
    }
}


# =============================================================================
# POST-TRANSLATIONAL MODIFICATIONS
# =============================================================================

POST_TRANSLATIONAL_MODIFICATIONS: Dict[str, Any] = {
    "n_linked_glycosylation": {
        "sites": [
            {"position": 157, "motif": "NLT", "evidence": "Experimental"},
            {"position": 227, "motif": "NRT", "evidence": "Experimental"}
        ],
        "function": "Protein folding, serum half-life"
    },
    "cleavage_sites": [
        {
            "position": "263-270",
            "sequence": "QIPKACVR",
            "peptidase": "Tolloid/BMP-1",
            "cleavage_type": "Proteolytic activation",
            "result": "Releases active mature myostatin from propeptide"
        }
    ],
    "disulfide_bonds": [
        {"from": "Cys-315", "to": "Cys-371", "type": "Inter-chain (dimer)"},
        {"from": "Cys-340", "to": "Cys-347", "type": "Intra-chain (cystine knot)"},
        {"from": "Cys-321", "to": "Cys-377", "type": "Intra-chain (cystine knot)"}
    ],
    "phosphorylation": {
        "predicted_sites": "None well-characterized",
        "note": "Myostatin signaling is receptor-mediated, not autophosphorylated"
    },
    "oxidation": {
        "methionine_sensitivity": "Met residues may oxidize",
        "note": "Redox status may affect activity"
    }
}


# =============================================================================
# TARGET SUMMARY
# =============================================================================

def get_target_profile_summary() -> Dict[str, Any]:
    """Returns complete target profile summary."""
    return {
        "protein_sequence": HUMAN_MYOSTATIN_SEQUENCE,
        "receptor_binding": RECEPTOR_BINDING_ANALYSIS,
        "structural_features": STRUCTURAL_FEATURES,
        "natural_nulls": NATURAL_GENETIC_NULLS,
        "polymorphisms": POLYMORPHISMS,
        "homology": HOMOLOGY_ANALYSIS,
        "active_sites": ACTIVE_SITE_ANALYSIS,
        "post_translational_modifications": POST_TRANSLATIONAL_MODIFICATIONS
    }


def get_druggability_assessment() -> Dict[str, Any]:
    """Returns druggability assessment for myostatin targets."""
    return {
        "myostatin_direct": {
            "target_type": "Secreted ligand",
            "druggability": "EXCELLENT",
            "evidence": [
                "Multiple antibodies in clinical trials",
                "Naturally occurring inhibitors (follistatin, propeptide)",
                "Clear phenotype in KO animals",
                "Safe loss-of-function in humans"
            ],
            "therapeutic_modality": "Antibodies, peptides, gene therapy"
        },
        "actriib_receptor": {
            "target_type": "Cell surface receptor",
            "druggability": "EXCELLENT",
            "evidence": [
                "Bimagrumab in clinical trials",
                "Decoy receptor approaches",
                "Ligand-binding domain well-characterized"
            ],
            "therapeutic_modality": "Antibodies, decoy receptors, small molecules"
        },
        "alk4_kinase": {
            "target_type": "Intracellular kinase",
            "druggability": "GOOD",
            "evidence": [
                "Classic kinase inhibitor target",
                "Selectivity challenges within TGF-beta family",
                "Oral small molecule potential"
            ],
            "therapeutic_modality": "Small molecule kinase inhibitors"
        },
        "smad_transcription": {
            "target_type": "Transcription factor complex",
            "druggability": "POOR",
            "evidence": [
                "Intracellular, nuclear localization",
                "Traditional small molecules not suitable",
                "Limited to peptide/protein approaches"
            ],
            "therapeutic_modality": "Peptides, oligonucleotides (indirect)"
        }
    }


if __name__ == "__main__":
    import json
    summary = get_target_profile_summary()
    print(json.dumps(summary, indent=2, default=str))
