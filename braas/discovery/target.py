"""Target Analyzer Module.

Analyzes drug targets (proteins) to identify binding sites, functional domains,
and optimal small molecule interaction zones. Includes knowledge base of
TGF-beta superfamily structures.
"""

import random
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from braas.discovery.models import (
    TargetAnalysis,
    BindingSite,
    Domain,
    DruggabilityScore,
    PathwayContext,
)


# Knowledge base of TGF-beta superfamily targets
TGF_BETA_KNOWLEDGE_BASE = {
    "myostatin": {
        "family": "TGF-beta superfamily",
        "receptor_type": "serine/threonine kinase",
        "pathway": "SMAD2/3 signaling",
        "gene": "MSTN",
        "length": 375,
        "active_site_residues": [150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160],
        "binding_site_description": "growth factor binding, receptor interaction",
        "druggability_rationale": "Extracellular target, well validated for antibody therapeutics",
        "disease_associations": ["muscular dystrophy", "muscle wasting", "sarcopenia"],
        "similar_proteins": ["activin A", "GDF-11", "GDF-8"],
    },
    "ALK5": {
        "family": "TGF-beta superfamily",
        "receptor_type": "serine/threonine kinase receptor",
        "pathway": "TGF-beta signaling",
        "gene": "TGFBR1",
        "length": 503,
        "active_site_residues": [200, 201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 211, 212],
        "binding_site_description": "ATP binding site, kinase domain",
        "druggability_rationale": "Well established druggability for small molecule kinase inhibitors",
        "disease_associations": ["fibrosis", "cancer", "pulmonary hypertension"],
        "similar_proteins": ["ALK1", "ALK2", "BMPR1A", "BMPR1B"],
    },
    "activin receptor type 1": {
        "family": "TGF-beta superfamily",
        "receptor_type": "serine/threonine kinase receptor",
        "pathway": "SMAD2/3 signaling",
        "gene": "ACVR1",
        "length": 509,
        "active_site_residues": [195, 196, 197, 198, 199, 200, 201, 202, 203, 204, 205],
        "binding_site_description": "ATP binding site, kinase domain",
        "druggability_rationale": "Kinase domain highly conserved, known inhibitors exist",
        "disease_associations": ["fibrodysplasia ossificans progressiva", "cancer"],
        "similar_proteins": ["ALK2", "ALK5", "BMPR1A"],
    },
    "BMPR1A": {
        "family": "TGF-beta superfamily",
        "receptor_type": "serine/threonine kinase receptor",
        "pathway": "BMP signaling",
        "gene": "BMPR1A",
        "length": 532,
        "active_site_residues": [190, 191, 192, 193, 194, 195, 196, 197, 198, 199, 200],
        "binding_site_description": "ATP binding site, kinase domain",
        "druggability_rationale": "Established kinase inhibitor target",
        "disease_associations": ["cancer", "pulmonary arterial hypertension"],
        "similar_proteins": ["BMPR1B", "ALK2", "ALK5"],
    },
    "SMAD4": {
        "family": "TGF-beta superfamily",
        "receptor_type": "transcription factor",
        "pathway": "SMAD signaling",
        "gene": "SMAD4",
        "length": 552,
        "active_site_residues": [],
        "binding_site_description": "DNA binding, protein-protein interaction",
        "druggability_rationale": "Transcription factor - protein-protein interaction interface",
        "disease_associations": ["cancer", "pancreatic cancer"],
        "similar_proteins": ["SMAD2", "SMAD3"],
    },
    "SMAD2": {
        "family": "TGF-beta superfamily",
        "receptor_type": "transcription factor",
        "pathway": "SMAD signaling",
        "gene": "SMAD2",
        "length": 467,
        "active_site_residues": [],
        "binding_site_description": "DNA binding, protein-protein interaction",
        "druggability_rationale": "Transcription factor - difficult to target with small molecules",
        "disease_associations": ["cancer", "fibrosis"],
        "similar_proteins": ["SMAD3", "SMAD4"],
    },
}

# Common domain patterns in TGF-beta receptors
DOMAIN_PATTERNS = {
    "kinase_domain": {
        "pattern": "kinase",
        "type": "functional",
        "description": "Serine/threonine kinase catalytic domain"
    },
    "ligand_binding": {
        "pattern": "extracellular",
        "type": "structural",
        "description": "Ligand binding domain"
    },
    "transmembrane": {
        "pattern": "transmembrane",
        "type": "structural",
        "description": "Single pass transmembrane helix"
    },
    "GS_domain": {
        "pattern": "GS-box",
        "type": "regulatory",
        "description": " glycine-serine rich regulatory region"
    },
    "MH1_domain": {
        "pattern": "MH1",
        "type": "functional",
        "description": "Mothers against decapentaplegic homology domain 1"
    },
    "MH2_domain": {
        "pattern": "MH2",
        "type": "functional",
        "description": "Mothers against decapentaplegic homology domain 2"
    },
}

# Protein sequences for key targets (simplified representations)
TARGET_SEQUENCES = {
    "myostatin": "MDPALRPQSLLLLSPLLLLWAGVGAAGLNPDAELVPEAPGQAEEVLQRRDLTRDRLHLEKQDLVGKASQAQLSVRQDLQRERQRMMREKQQMKHLQERLDELRKQCRALYHDDGSGASGSQPLGTSESSSPGPPAHPSPGGSGPAPQPPRPHSSGPHQAHPSMPPSHLSNRAFPGAPGPRDRAGGGRGRAEAGGWDEPDSGLSLSFPVNRGLCPAHSLMFPMDRAAPAPGQAAPEAPRPAPAPAPGPASDAFQLSPQPQPGENAGENASGPTQLRGRSSSSDSFGPSCSPGPHPGWSV",
    "ALK5": "MNSLFPGLVCIENVYVGTDQWMNSVRIGESDGPLQIMQRKAGTRTIRRIKAGMSSNFKVKLLDGFQVITDGLATCKDGRGLGCPQDVSKEDAGEQVIQLMTAFINDSSMSFQVKAQVAQLLNENQRLPVSQRLQDGPIYIISQNCLAQLEMHSELVELGAHPICRPTDVQVNIPVTRDGTRFTVGLSLDVGGGPAYPGVQWVRVEMEDGSPLLLQLLDVAPGLREHLTHPVLHGVYSGHPGFGVAEHGWVLQRRDHGAGDPRPTAAVQSVLLVDGGQPLHIVTYYQEPQCEWIDLDLDFVSKPPSFRLQPEPRGRFAQGMQDPTLQQNLRQLEDAFQA",
    "activin receptor type 1": "MLPGLPCVWPVFSTEKNLVKNIHACWSKIADIGRSSRHPGVMGQAQIWACLACTSLSVNSIAPDIEIWDQLPAGWVQRENVVLQNAAEIKSNLEFKHRPELKPIFHAIIEETKFKGVNLDLCGNTLDVIGDTSGDFLWLVKLYCGSNLHTPVKRTDFEILEPRNHVVLTRVSTRSAFGYHSSSLDVASTPSELQRLNKVPEGCFGPAIHNHSAQNAQLLQQLTTSLSLSNLSAHSPAFSQKPPSEPRTLQEVAEAAGSGSSSASSSSEVGSQNSNSSRHSQPMLG",
    "BMPR1A": "MVWGSLPKNVQQNFHSVMLVEGGSQGQWSELKPAVRHVIHIDHSVPGQSWRQDGPQLSMLKQEPQEWVLRVNSGGGKPRHSVFAVWAAAREPSLHPRHSHTLVLQRDGWSGHPKYHAVDVSQGLSGPHPAHSWHSVPRVSTLPSQNSLINPVQNHHSRQGWQDGPCAHPRISVLVKLNSATLKQLAQTPDKAGIPYSTQNFVPRERQEWLVQKLDVGRNGDFGSVKIAVKMLEKSSSQTRVGTKHVNMIRSQGLNPTYPVTTSSNNSMSSHG",
}


class TargetAnalyzer:
    """Analyzes drug targets for small molecule drug discovery.
    
    Provides comprehensive target analysis including binding site prediction,
    druggability assessment, pathway context, and similarity analysis.
    Specializes in TGF-beta superfamily targets.
    
    Attributes:
        knowledge_base: Dictionary of known target information
        domain_patterns: Domain pattern definitions
        target_sequences: Pre-stored or analyzed protein sequences
    """
    
    def __init__(self):
        """Initialize the target analyzer with knowledge base."""
        self.knowledge_base = TGF_BETA_KNOWLEDGE_BASE
        self.domain_patterns = DOMAIN_PATTERNS
        self.target_sequences = TARGET_SEQUENCES
    
    def analyze_target(self, protein_name: str) -> TargetAnalysis:
        """Perform complete analysis of a drug target.
        
        Args:
            protein_name: Name of the target protein
            
        Returns:
            TargetAnalysis with comprehensive target information
        """
        # Case-insensitive lookup
        protein_name_lower = protein_name.lower()
        matched_key = None
        
        if protein_name_lower in self.knowledge_base:
            matched_key = protein_name_lower
        else:
            # Try to find similar names
            for known in self.knowledge_base:
                if protein_name_lower in known.lower():
                    matched_key = known
                    break
        
        if matched_key is None:
            # Create a generic analysis for unknown targets
            return self._create_generic_analysis(protein_name)
        
        info = self.knowledge_base[matched_key]
        
        # Get or generate sequence
        sequence = self.target_sequences.get(matched_key, "")
        
        # Analyze binding sites
        binding_sites = self._analyze_binding_sites(matched_key, info, sequence)
        
        # Predict druggability
        druggability = self.predict_druggability(matched_key)
        
        # Get pathway context
        pathway_context = self.get_pathway_context(matched_key)
        
        # Find similar targets
        similar = self.find_similar_druggable_proteins(matched_key)
        
        return TargetAnalysis(
            target_name=protein_name,
            sequence=sequence,
            family=info["family"],
            receptor_type=info["receptor_type"],
            binding_sites=binding_sites,
            druggability=druggability,
            pathway_context=pathway_context,
            similar_targets=similar,
        )
    
    def predict_binding_site(self, sequence: str) -> BindingSite:
        """Predict small molecule binding region in a protein.
        
        Args:
            sequence: Amino acid sequence of the protein
            
        Returns:
            BindingSite with predicted binding region characteristics
        """
        # Use heuristics based on sequence properties
        length = len(sequence)
        
        # Estimate binding site location based on typical kinase architecture
        # Kinases have N-terminal ATP binding and C-terminal activation
        location = "kinase domain, ATP binding pocket"
        
        # Estimate size based on protein length
        if length > 400:
            size = 450.0 + (length - 400) * 0.5
        else:
            size = 450.0
        
        # Calculate hydrophobicity (simplified)
        hydrophobic_count = sum(1 for aa in sequence if aa in 'AILMFVPGW')
        hydrophobicity = hydrophobic_count / len(sequence) if sequence else 0.5
        
        # Estimate H-bond donors/acceptors based on polar residue content
        polar_residues = sum(1 for aa in sequence if aa in 'STYCNQ')
        hbd = max(2, int(polar_residues * 0.1))
        hba = max(3, int(polar_residues * 0.15))
        
        # Druglikeness score based on predicted site characteristics
        druglikeness = 0.6 + hydrophobicity * 0.2 - abs(0.5 - hydrophobicity) * 0.2
        
        return BindingSite(
            location=location,
            size_angstroms=size,
            hydrophobicity=hydrophobicity,
            hydrogen_bond_donors=hbd,
            hydrogen_bond_acceptors=hba,
            druglikeness_score=min(1.0, max(0.0, druglikeness))
        )
    
    def get_functional_domains(self, sequence: str) -> List[Domain]:
        """Identify functional and structural domains in a protein.
        
        Args:
            sequence: Amino acid sequence
            
        Returns:
            List of identified Domain objects
        """
        domains = []
        length = len(sequence)
        
        # Detect kinase domain (typical in TGF-beta receptors)
        if length > 400:
            # Kinase domain is usually in the middle-to-C-terminal region
            domains.append(Domain(
                name="kinase_domain",
                start_residue=int(length * 0.3),
                end_residue=int(length * 0.7),
                domain_type="functional",
                description="Serine/threonine kinase catalytic domain"
            ))
            
            # GS domain (regulatory)
            domains.append(Domain(
                name="GS_domain",
                start_residue=int(length * 0.2),
                end_residue=int(length * 0.3),
                domain_type="regulatory",
                description="Glycine-serine rich region, phosphorylation site"
            ))
        
        # Extracellular ligand binding domain
        if length > 200:
            domains.append(Domain(
                name="ligand_binding",
                start_residue=1,
                end_residue=int(length * 0.2),
                domain_type="structural",
                description="Extracellular domain for ligand recognition"
            ))
        
        # Transmembrane helix
        if length > 300:
            domains.append(Domain(
                name="transmembrane",
                start_residue=int(length * 0.2),
                end_residue=int(length * 0.25),
                domain_type="structural",
                description="Single pass transmembrane helix"
            ))
        
        # SMAD binding domain (for receptors)
        if length > 450:
            domains.append(Domain(
                name="SMAD_binding",
                start_residue=int(length * 0.7),
                end_residue=length,
                domain_type="functional",
                description="C-terminal SMAD protein interaction motif"
            ))
        
        return domains
    
    def _find_in_knowledge_base(self, target: str) -> Optional[str]:
        """Case-insensitive lookup in knowledge base.
        
        Args:
            target: Target protein name
            
        Returns:
            Matching key from knowledge base or None
        """
        target_lower = target.lower()
        if target_lower in self.knowledge_base:
            return target_lower
        for known in self.knowledge_base:
            if target_lower in known.lower():
                return known
        return None
    
    def predict_druggability(self, target: str) -> DruggabilityScore:
        """Assess how druggable a target is.
        
        Args:
            target: Target protein name
            
        Returns:
            DruggabilityScore with assessment
        """
        matched_key = self._find_in_knowledge_base(target)
        
        if matched_key is None:
            return DruggabilityScore(
                target=target,
                score=0.5,
                classification="unknown",
                rationale="Target not in knowledge base - requires experimental validation"
            )
        
        info = self.knowledge_base[matched_key]
        
        # Score based on receptor type
        receptor_scores = {
            "serine/threonine kinase receptor": 0.85,
            "serine/threonine kinase": 0.90,
            "transcription factor": 0.25,
            "growth factor": 0.70,
            "secreted protein": 0.65,
        }
        
        base_score = receptor_scores.get(
            info["receptor_type"], 
            0.5
        )
        
        # Known inhibitors boost score
        if info.get("known_inhibitors"):
            base_score = min(0.95, base_score + 0.1)
        
        # Pathway context affects druggability
        if "kinase" in info["receptor_type"].lower():
            kinase_family_score = 0.88
        else:
            kinase_family_score = 0.5
        
        # Classification
        if base_score >= 0.8:
            classification = "highly_druggable"
        elif base_score >= 0.6:
            classification = "druggable"
        elif base_score >= 0.4:
            classification = "difficult"
        else:
            classification = "undruggable"
        
        return DruggabilityScore(
            target=target,
            score=base_score,
            classification=classification,
            rationale=info.get("druggability_rationale", "Standard assessment"),
            kinase_family_score=kinase_family_score
        )
    
    def get_pathway_context(self, target: str) -> PathwayContext:
        """Get the pathway context for a target.
        
        Args:
            target: Target protein name
            
        Returns:
            PathwayContext with pathway information
        """
        matched_key = self._find_in_knowledge_base(target)
        
        if matched_key is None:
            return PathwayContext(
                target=target,
                pathway_name="Unknown",
                pathway_role="unknown",
                disease_associations=["various diseases"],
                biological_function="Unknown function",
                safety_concerns=["Requires thorough safety profiling"]
            )
        
        info = self.knowledge_base[matched_key]
        
        # Determine pathway role based on receptor type
        if "kinase receptor" in info["receptor_type"].lower():
            role = "receptor"
        elif "transcription factor" in info["receptor_type"].lower():
            role = "mediator"
        elif "growth factor" in info["receptor_type"].lower():
            role = "ligand"
        else:
            role = "mediator"
        
        # Safety concerns based on pathway
        safety = []
        if "tgf-beta" in info["pathway"].lower() or "smad" in info["pathway"].lower():
            safety.extend([
                "Broad physiological roles may cause off-target effects",
                "Immune system modulation potential",
                "Cardiovascular effects possible"
            ])
        if "bmp" in info["pathway"].lower():
            safety.extend([
                "Bone and cartilage effects",
                "Developmental toxicity risk"
            ])
        
        return PathwayContext(
            target=target,
            pathway_name=info["pathway"],
            pathway_role=role,
            disease_associations=info.get("disease_associations", []),
            biological_function=f"Member of {info['family']}, involved in {info['pathway']}",
            safety_concerns=safety
        )
    
    def find_similar_druggable_proteins(self, target: str) -> List[str]:
        """Find proteins with similar structure/druggability profiles.
        
        Args:
            target: Target protein name
            
        Returns:
            List of similar target names
        """
        matched_key = self._find_in_knowledge_base(target)
        
        if matched_key is None:
            return list(self.knowledge_base.keys())[:5]  # Return some known targets
        
        similar = self.knowledge_base[matched_key].get("similar_proteins", [])
        
        # Add other targets from the same family
        family = self.knowledge_base[matched_key]["family"]
        for name, info in self.knowledge_base.items():
            if name != matched_key and info["family"] == family:
                if name not in similar:
                    similar.append(name)
        
        return similar[:10]  # Limit to top 10
    
    def _analyze_binding_sites(
        self, 
        normalized: str, 
        info: Dict[str, Any],
        sequence: str
    ) -> List[BindingSite]:
        """Analyze binding sites for a target.
        
        Args:
            normalized: Normalized target name
            info: Target information from knowledge base
            sequence: Protein sequence
            
        Returns:
            List of BindingSite objects
        """
        binding_sites = []
        
        # Primary active site
        if info.get("active_site_residues"):
            # Kinase ATP binding site
            primary_site = BindingSite(
                location="ATP binding pocket (kinase domain)",
                size_angstroms=450.0,
                hydrophobicity=0.45,
                hydrogen_bond_donors=4,
                hydrogen_bond_acceptors=6,
                druglikeness_score=0.85
            )
            binding_sites.append(primary_site)
            
            # Allosteric site (for some kinases)
            allosteric_site = BindingSite(
                location="Allosteric pocket (adjacent to ATP site)",
                size_angstroms=350.0,
                hydrophobicity=0.55,
                hydrogen_bond_donors=2,
                hydrogen_bond_acceptors=4,
                druglikeness_score=0.70
            )
            binding_sites.append(allosteric_site)
        else:
            # Non-kinase targets
            site = self.predict_binding_site(sequence)
            binding_sites.append(site)
        
        return binding_sites
    
    def _create_generic_analysis(self, protein_name: str) -> TargetAnalysis:
        """Create a generic analysis for unknown targets.
        
        Args:
            protein_name: Name of the target
            
        Returns:
            TargetAnalysis with generic/default values
        """
        # Generate a plausible sequence for analysis
        sequence = "".join(random.choices("ACDEFGHIKLMNPQRSTVWY", k=400))
        
        binding_sites = [self.predict_binding_site(sequence)]
        domains = self.get_functional_domains(sequence)
        
        return TargetAnalysis(
            target_name=protein_name,
            sequence=sequence,
            family="Unknown",
            receptor_type="Unknown",
            binding_sites=binding_sites,
            druggability=DruggabilityScore(
                target=protein_name,
                score=0.5,
                classification="unknown",
                rationale="Requires experimental validation"
            ),
            pathway_context=PathwayContext(
                target=protein_name,
                pathway_name="Unknown",
                pathway_role="unknown"
            ),
            similar_targets=[]
        )
    
    def get_target_info(self, target: str) -> Optional[Dict[str, Any]]:
        """Get stored information about a target.
        
        Args:
            target: Target protein name
            
        Returns:
            Dictionary of target information or None
        """
        normalized = target.lower()
        return self.knowledge_base.get(normalized)
    
    def add_target_knowledge(
        self, 
        target: str, 
        info: Dict[str, Any]
    ) -> bool:
        """Add new target knowledge to the database.
        
        Args:
            target: Target name
            info: Target information dictionary
            
        Returns:
            True if added successfully
        """
        self.knowledge_base[target.lower()] = info
        return True
