"""Data models for drug discovery module.

This module defines all dataclasses used across the drug discovery pipeline
for compounds, targets, docking results, and drug candidates.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class Compound:
    """Represents a molecular compound with computed properties.
    
    Attributes:
        name: Unique identifier for the compound
        smiles: SMILES string representation of molecular structure
        molecular_weight: Molecular weight in Daltons
        logp: Partition coefficient (lipophilicity measure)
        tpsa: Topological polar surface area in Å²
        hbd: Number of hydrogen bond donors
        hba: Number of hydrogen bond acceptors
        rotatable_bonds: Number of rotatable single bonds
        source: Origin of the compound (e.g., 'library', 'generated', 'natural_product')
        generation_method: How the compound was generated
    """
    name: str
    smiles: str
    molecular_weight: float
    logp: float
    tpsa: float
    hbd: int
    hba: int
    rotatable_bonds: int
    source: str = "unknown"
    generation_method: str = "unknown"


@dataclass
class CompoundScore:
    """Scoring results for a compound from virtual screening.
    
    Attributes:
        compound: The Compound object being scored
        docking_score: Molecular docking score (higher is better binding)
        admet_score: ADMET properties score (0-1, higher is better)
        synthesizability_score: Ease of synthesis score (0-1, higher is easier)
        overall_score: Combined weighted score across all metrics
        ranking: Rank position among screened compounds
    """
    compound: Compound
    docking_score: float
    admet_score: float
    synthesizability_score: float
    overall_score: float
    ranking: int = 0


@dataclass
class ADMETPrediction:
    """Predicted ADMET (Absorption/Distribution/Metabolism/Excretion/Toxicity) properties.
    
    Attributes:
        absorption: Absorption prediction ('high', 'moderate', 'low', 'poor')
        distribution: Distribution prediction (e.g., 'wide', 'limited', 'CNS')
        metabolism: Metabolism prediction (e.g., 'slow', 'moderate', 'fast')
        excretion: Excretion prediction (e.g., 'renal', 'hepatic', 'biliary')
        toxicity_class: Toxicity classification ('acceptable', 'moderate', 'high')
        warnings: List of specific warnings/adverse predictions
        score: Overall ADMET score (0-1, higher is better)
    """
    absorption: str
    distribution: str
    metabolism: str
    excretion: str
    toxicity_class: str
    warnings: List[str] = field(default_factory=list)
    score: float = 0.5


@dataclass
class DrugCandidate:
    """A compound that has progressed through initial drug discovery screening.
    
    Attributes:
        compound: The underlying Compound object
        target: Primary protein target (e.g., 'myostatin', 'activin receptor')
        indication: Proposed therapeutic indication
        stage: Development stage ('hit', 'lead', 'optimized_lead', 'candidate')
        efficacy_score: Predicted therapeutic efficacy (0-1)
        safety_score: Predicted safety profile (0-1)
        admet_profile: Detailed ADMET predictions
        clinical_relevance: Clinical significance score (0-1)
        novelty_score: Structural novelty compared to known drugs (0-1)
        recommendations: List of suggested next steps
    """
    compound: Compound
    target: str
    indication: str
    stage: str
    efficacy_score: float
    safety_score: float
    admet_profile: ADMETPrediction
    clinical_relevance: float
    novelty_score: float
    recommendations: List[str] = field(default_factory=list)


@dataclass
class BindingSite:
    """Predicted small molecule binding site on a target protein.
    
    Attributes:
        location: Structural location description
        size_angstroms: Volume of binding site in cubic Ångstroms
        hydrophobicity: Hydrophobic character (0-1 scale)
        hydrogen_bond_donors: Number of H-bond donor residues
        hydrogen_bond_acceptors: Number of H-bond acceptor residues
        druglikeness_score: Predicted druglikeness of binding site (0-1)
    """
    location: str
    size_angstroms: float
    hydrophobicity: float
    hydrogen_bond_donors: int
    hydrogen_bond_acceptors: int
    druglikeness_score: float


@dataclass
class Domain:
    """Represents a structural/functional domain in a protein.
    
    Attributes:
        name: Domain name (e.g., 'kinase domain', 'furin-like domain')
        start_residue: Starting residue position
        end_residue: Ending residue position
        domain_type: Type classification ('structural', 'functional', 'regulatory')
        description: Detailed description of domain function
    """
    name: str
    start_residue: int
    end_residue: int
    domain_type: str
    description: str = ""


@dataclass
class DruggabilityScore:
    """Assessment of how "druggable" a target protein is.
    
    Attributes:
        target: Target protein name
        score: Overall druggability score (0-1, higher is more druggable)
        classification: Drugability class ('highly_druggable', 'druggable', 'difficult', 'undruggable')
        rationale: Explanation of the druggability assessment
        kinase_family_score: Specific score for serine/threonine kinase families
    """
    target: str
    score: float
    classification: str
    rationale: str
    kinase_family_score: float = 0.5


@dataclass
class PathwayContext:
    """Context of target role in disease pathways.
    
    Attributes:
        target: Target protein name
        pathway_name: Primary signaling pathway
        pathway_role: Role in pathway ('receptor', 'ligand', 'mediator', 'inhibitor')
        disease_associations: List of associated diseases
        biological_function: Brief description of normal biological function
        safety_concerns: Potential safety issues from pathway modulation
    """
    target: str
    pathway_name: str
    pathway_role: str
    disease_associations: List[str] = field(default_factory=list)
    biological_function: str = ""
    safety_concerns: List[str] = field(default_factory=list)


@dataclass
class TargetAnalysis:
    """Complete analysis of a drug target protein.
    
    Attributes:
        target_name: Name of the target protein
        sequence: Amino acid sequence
        family: Protein family (e.g., 'TGF-beta superfamily')
        receptor_type: Type of receptor (e.g., 'serine/threonine kinase')
        binding_sites: List of predicted binding sites
        druggability: Druggability assessment
        pathway_context: Pathway involvement analysis
        similar_targets: Proteins with similar druggability profiles
    """
    target_name: str
    sequence: str
    family: str
    receptor_type: str
    binding_sites: List[BindingSite] = field(default_factory=list)
    druggability: Optional[DruggabilityScore] = None
    pathway_context: Optional[PathwayContext] = None
    similar_targets: List[str] = field(default_factory=list)


@dataclass
class Interaction:
    """Represents a molecular interaction between compound and target.
    
    Attributes:
        interaction_type: Type of interaction ('hydrogen_bond', 'hydrophobic', 'salt_bridge', 'pi_stacking')
        atom1: First atom/residue involved
        atom2: Second atom/residue involved
        distance: Distance in Ångstroms
        strength: Interaction strength estimate (0-1)
    """
    interaction_type: str
    atom1: str
    atom2: str
    distance: float
    strength: float


@dataclass
class DockingResult:
    """Results from molecular docking simulation.
    
    Attributes:
        compound: The docked Compound
        target: Target protein name
        binding_score_kcal: Calculated binding energy
        pose_confidence: Confidence in the docking pose (0-1)
        predicted_affinity: Predicted binding affinity in kcal/mol
        interactions: List of predicted interactions
    """
    compound: Compound
    target: str
    binding_score_kcal: float
    pose_confidence: float
    predicted_affinity: float
    interactions: List[Interaction] = field(default_factory=list)


@dataclass
class SelectivityScore:
    """Selectivity profile of a compound across multiple targets.
    
    Attributes:
        compound: The Compound being evaluated
        primary_target: Intended primary target
        off_targets: Dictionary mapping off-target names to binding scores
        selectivity_index: Ratio of primary vs off-target activity (higher = more selective)
    """
    compound: Compound
    primary_target: str
    off_targets: Dict[str, float] = field(default_factory=dict)
    selectivity_index: float = 1.0


@dataclass
class Mutation:
    """Represents a resistance-associated mutation.
    
    Attributes:
        position: Residue position in sequence
        original_residue: Original amino acid
        mutant_residue: Substituted amino acid
        resistance_impact: Impact on drug binding ('high', 'moderate', 'low')
        description: Mechanistic explanation of resistance
    """
    position: int
    original_residue: str
    mutant_residue: str
    resistance_impact: str
    description: str = ""


@dataclass
class CytotoxicityPrediction:
    """Predicted cytotoxicity across different cell types.
    
    Attributes:
        compound: The Compound being evaluated
        cell_types: List of cell type names
        ic50_values: Dictionary mapping cell types to predicted IC50 (μM)
        toxicity_profile: Overall toxicity classification
        therapeutic_index: Ratio of effective to toxic concentration
    """
    compound: Compound
    cell_types: List[str]
    ic50_values: Dict[str, float] = field(default_factory=dict)
    toxicity_profile: str = "unknown"
    therapeutic_index: float = 1.0


@dataclass
class Modification:
    """Proposed chemical modification to a lead compound.
    
    Attributes:
        modification_type: Type of modification ('add_group', 'replace_group', 'remove_group')
        location: Location in molecular structure
        suggestion: Specific modification suggestion
        expected_effect: Expected effect on properties
        rationale: Scientific justification
    """
    modification_type: str
    location: str
    suggestion: str
    expected_effect: str
    rationale: str = ""


@dataclass
class SARAnalysis:
    """Structure-Activity Relationship analysis results.
    
    Attributes:
        compounds: List of compounds analyzed
        activity_property: Property being correlated with structure
        key_features: List of important structural features
        activity_trends: Observed trends in structure-activity relationships
        recommendations: Suggested modifications based on SAR
    """
    compounds: List[Compound]
    activity_property: str
    key_features: List[str] = field(default_factory=list)
    activity_trends: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
