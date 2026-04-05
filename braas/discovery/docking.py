"""Molecular Docking Simulator Module.

Simulates molecular docking to predict binding affinity between compounds
and protein targets. Uses physics-informed scoring functions combining
shape complementarity, hydrogen bonding, hydrophobic interactions, and
electrostatics.
"""

import random
import math
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

from braas.discovery.models import (
    Compound,
    DockingResult,
    Interaction,
    SelectivityScore,
    Mutation,
)


# Mock receptor structures for scoring
RECEPTOR_PROFILES = {
    "myostatin": {
        "binding_site_hydrophobicity": 0.45,
        "hbd_count": 4,
        "hba_count": 6,
        "shape_complementarity": 0.75,
        "key_residues": ["HIS150", "ASP151", "GLY152", "SER153", "GLN154"],
    },
    "ALK5": {
        "binding_site_hydrophobicity": 0.40,
        "hbd_count": 5,
        "hba_count": 7,
        "shape_complementarity": 0.80,
        "key_residues": ["GLU150", "ALA151", "ASP152", "PHE153", "VAL154"],
    },
    "activin receptor type 1": {
        "binding_site_hydrophobicity": 0.42,
        "hbd_count": 4,
        "hba_count": 6,
        "shape_complementarity": 0.78,
        "key_residues": ["ASP200", "LYS201", "ALA202", "GLY203", "GLU204"],
    },
    "BMPR1A": {
        "binding_site_hydrophobicity": 0.43,
        "hbd_count": 4,
        "hba_count": 6,
        "shape_complementarity": 0.77,
        "key_residues": ["HIS190", "ASP191", "GLY192", "ALA193", "VAL194"],
    },
}

# Default profile for unknown receptors
DEFAULT_RECEPTOR_PROFILE = {
    "binding_site_hydrophobicity": 0.45,
    "hbd_count": 4,
    "hba_count": 6,
    "shape_complementarity": 0.70,
    "key_residues": ["RES1", "RES2", "RES3", "RES4", "RES5"],
}


class DockingSimulator:
    """Simulates molecular docking for drug-target interaction prediction.
    
    Uses physics-informed scoring functions to predict binding affinity
    and key molecular interactions. Supports virtual screening of compound
    libraries against target proteins.
    
    Attributes:
        receptor_profiles: Known receptor binding site profiles
        scoring_weights: Weights for scoring function components
    """
    
    def __init__(self):
        """Initialize the docking simulator."""
        self.receptor_profiles = RECEPTOR_PROFILES
        self.scoring_weights = {
            "shape_complementarity": 0.30,
            "hydrogen_bonding": 0.25,
            "hydrophobic_interaction": 0.20,
            "electrostatics": 0.15,
            "entropy_penalty": 0.10,
        }
    
    def dock_compound(
        self, 
        compound: Compound, 
        target: str
    ) -> DockingResult:
        """Dock a compound to a target protein.
        
        Args:
            compound: Compound to dock
            target: Target protein name
            
        Returns:
            DockingResult with binding score and predicted interactions
        """
        # Get receptor profile
        profile = self.receptor_profiles.get(
            target.lower(),
            DEFAULT_RECEPTOR_PROFILE
        )
        
        # Calculate binding score components
        shape_score = self._calculate_shape_complementarity(compound, profile)
        hbond_score = self._calculate_hydrogen_bonding(compound, profile)
        hydrophobic_score = self._calculate_hydrophobic_interaction(
            compound, profile
        )
        electrostatic_score = self._calculate_electrostatics(compound, profile)
        entropy_penalty = self._calculate_entropy_penalty(compound)
        
        # Combine scores
        binding_score = (
            shape_score * self.scoring_weights["shape_complementarity"] +
            hbond_score * self.scoring_weights["hydrogen_bonding"] +
            hydrophobic_score * self.scoring_weights["hydrophobic_interaction"] +
            electrostatic_score * self.scoring_weights["electrostatics"] -
            entropy_penalty * self.scoring_weights["entropy_penalty"]
        )
        
        # Normalize to kcal/mol (mock conversion)
        binding_score_kcal = -8.0 + binding_score * 4.0
        
        # Predict interactions
        interactions = self.predict_key_interactions(compound, target)
        
        # Calculate pose confidence based on score distribution
        pose_confidence = min(0.95, max(0.3, (binding_score + 1) / 2))
        
        # Predict binding affinity
        predicted_affinity = self.predict_binding_affinity(compound, target)
        
        return DockingResult(
            compound=compound,
            target=target,
            binding_score_kcal=binding_score_kcal,
            interactions=interactions,
            pose_confidence=pose_confidence,
            predicted_affinity=predicted_affinity
        )
    
    def predict_binding_affinity(
        self, 
        compound: Compound, 
        target: str
    ) -> float:
        """Estimate binding affinity in kcal/mol.
        
        Uses knowledge-based scoring combining multiple factors.
        
        Args:
            compound: Compound being evaluated
            target: Target protein name
            
        Returns:
            Predicted binding affinity (kcal/mol)
        """
        profile = self.receptor_profiles.get(
            target.lower(),
            DEFAULT_RECEPTOR_PROFILE
        )
        
        # Base affinity from molecular properties
        base_affinity = -8.0  # Baseline for typical kinase inhibitors
        
        # Adjust for molecular weight (larger = worse binding typically)
        if compound.molecular_weight > 500:
            base_affinity += 0.5
        elif compound.molecular_weight < 350:
            base_affinity -= 0.5
        
        # Adjust for lipophilicity match with binding site
        logp_diff = abs(compound.logp - profile["binding_site_hydrophobicity"] * 10)
        base_affinity += logp_diff * 0.2
        
        # Adjust for H-bonding capacity
        hbond_match = min(compound.hbd, profile["hbd_count"]) / max(compound.hbd, profile["hbd_count"], 1)
        base_affinity -= hbond_match * 1.5
        
        # Penalize excessive polarity
        if compound.tpsa > 140:
            base_affinity += 0.5
        
        # Add some randomness for realistic variation
        base_affinity += random.uniform(-0.5, 0.5)
        
        return base_affinity
    
    def predict_key_interactions(
        self, 
        compound: Compound, 
        target: str
    ) -> List[Interaction]:
        """Predict key molecular interactions.
        
        Args:
            compound: Compound being evaluated
            target: Target protein name
            
        Returns:
            List of predicted Interaction objects
        """
        profile = self.receptor_profiles.get(
            target.lower(),
            DEFAULT_RECEPTOR_PROFILE
        )
        
        interactions = []
        
        # Predict hydrogen bonds
        num_hbonds = min(compound.hbd, profile["hbd_count"])
        for i in range(num_hbonds):
            residue = profile["key_residues"][i % len(profile["key_residues"])]
            interactions.append(Interaction(
                interaction_type="hydrogen_bond",
                atom1=f"{compound.name}_O{i}",
                atom2=residue,
                distance=2.0 + random.uniform(-0.3, 0.3),
                strength=0.7 + random.uniform(-0.2, 0.2)
            ))
        
        # Predict hydrophobic contacts
        num_hydrophobic = int(compound.logp * 2)
        for i in range(min(num_hydrophobic, 5)):
            residue = profile["key_residues"][i % len(profile["key_residues"])]
            interactions.append(Interaction(
                interaction_type="hydrophobic",
                atom1=f"{compound.name}_C{i}",
                atom2=residue,
                distance=3.5 + random.uniform(-0.5, 0.5),
                strength=0.5 + random.uniform(-0.2, 0.2)
            ))
        
        # Predict salt bridges (if applicable)
        if compound.hbd > 3 and compound.hba > 5:
            interactions.append(Interaction(
                interaction_type="salt_bridge",
                atom1=f"{compound.name}_COO-",
                atom2=profile["key_residues"][0],
                distance=3.0 + random.uniform(-0.3, 0.3),
                strength=0.8 + random.uniform(-0.1, 0.1)
            ))
        
        return interactions
    
    def score_selectivity(
        self, 
        compound: Compound, 
        off_targets: List[str]
    ) -> SelectivityScore:
        """Score compound selectivity across multiple targets.
        
        Args:
            compound: Compound being evaluated
            off_targets: List of off-target protein names
            
        Returns:
            SelectivityScore with selectivity analysis
        """
        primary_target = "myostatin"  # Default primary target
        off_target_scores = {}
        
        # Score binding to primary target
        primary_score = self._calculate_overall_binding_score(compound, primary_target)
        
        # Score binding to each off-target
        for off_target in off_targets:
            score = self._calculate_overall_binding_score(compound, off_target)
            off_target_scores[off_target] = score
        
        # Calculate selectivity index (ratio of primary to off-target binding)
        if off_target_scores:
            avg_off_target = sum(off_target_scores.values()) / len(off_target_scores)
            selectivity_index = primary_score / max(avg_off_target, 0.1)
        else:
            selectivity_index = 1.0
        
        return SelectivityScore(
            compound=compound,
            primary_target=primary_target,
            off_targets=off_target_scores,
            selectivity_index=selectivity_index
        )
    
    def predict_resistance_mutations(
        self, 
        compound: Compound, 
        target: str
    ) -> List[Mutation]:
        """Predict potential resistance mutations.
        
        Args:
            compound: Compound being evaluated
            target: Target protein name
            
        Returns:
            List of potential resistance-associated mutations
        """
        profile = self.receptor_profiles.get(
            target.lower(),
            DEFAULT_RECEPTOR_PROFILE
        )
        
        mutations = []
        
        # Common resistance mechanisms for kinase inhibitors
        # Gatekeeper mutations (hydrophobic to larger hydrophobic)
        mutations.append(Mutation(
            position=150,
            original_residue="THR",
            mutant_residue="ILE",
            resistance_impact="moderate",
            description="Gatekeeper mutation reduces inhibitor access to hydrophobic pocket"
        ))
        
        # H-bond disrupting mutations
        mutations.append(Mutation(
            position=151,
            original_residue="ASP",
            mutant_residue="ASN",
            resistance_impact="high",
            description="Loss of critical hydrogen bond reduces binding affinity"
        ))
        
        # Hydrophobic pocket mutations
        mutations.append(Mutation(
            position=152,
            original_residue="GLY",
            mutant_residue="ALA",
            resistance_impact="low",
            description="Reduces flexibility and steric hindrance"
        ))
        
        # Activation loop mutations
        mutations.append(Mutation(
            position=200,
            original_residue="GLU",
            mutant_residue="GLN",
            resistance_impact="moderate",
            description="Affects conformational equilibrium"
        ))
        
        return mutations
    
    def screen_compounds(
        self, 
        compounds: List[Compound], 
        target: str, 
        top_n: int = 20
    ) -> List[DockingResult]:
        """Screen a library of compounds against a target.
        
        Fast virtual screening with detailed analysis of top hits.
        
        Args:
            compounds: List of compounds to screen
            target: Target protein name
            top_n: Number of top compounds for detailed analysis
            
        Returns:
            List of DockingResults sorted by binding score
        """
        results = []
        
        # Fast screening of all compounds
        for compound in compounds:
            result = self.dock_compound(compound, target)
            results.append(result)
        
        # Sort by binding score (more negative = better binding)
        results.sort(key=lambda x: x.binding_score_kcal)
        
        # Return top N results
        return results[:top_n]
    
    def _calculate_shape_complementarity(
        self, 
        compound: Compound, 
        profile: Dict
    ) -> float:
        """Calculate shape complementarity score.
        
        Args:
            compound: Compound being evaluated
            profile: Receptor binding site profile
            
        Returns:
            Shape complementarity score (0-1)
        """
        base_score = profile["shape_complementarity"]
        
        # Adjust for molecular size (vs binding site size)
        mw_factor = 1.0
        if compound.molecular_weight > 600:
            mw_factor = 0.7
        elif compound.molecular_weight > 500:
            mw_factor = 0.85
        elif compound.molecular_weight < 300:
            mw_factor = 0.9
        
        # Adjust for rotatable bonds (flexibility)
        rot_factor = 1.0
        if compound.rotatable_bonds > 10:
            rot_factor = 0.7
        elif compound.rotatable_bonds > 7:
            rot_factor = 0.85
        
        return base_score * mw_factor * rot_factor
    
    def _calculate_hydrogen_bonding(
        self, 
        compound: Compound, 
        profile: Dict
    ) -> float:
        """Calculate hydrogen bonding score.
        
        Args:
            compound: Compound being evaluated
            profile: Receptor binding site profile
            
        Returns:
            Hydrogen bonding score (0-1)
        """
        # Ideal H-bond donor/acceptor count for the binding site
        ideal_hbd = profile["hbd_count"]
        ideal_hba = profile["hba_count"]
        
        # Calculate match factor
        hbd_match = 1.0 - abs(compound.hbd - ideal_hbd) / max(ideal_hbd, 1)
        hba_match = 1.0 - abs(compound.hba - ideal_hba) / max(ideal_hba, 1)
        
        # H-bond capacity bonus
        hbond_capacity = min(compound.hbd, ideal_hbd) / max(ideal_hbd, 1) * 0.5
        hbond_capacity += min(compound.hba, ideal_hba) / max(ideal_hba, 1) * 0.5
        
        return (hbd_match + hba_match) / 2 * 0.5 + hbond_capacity * 0.5
    
    def _calculate_hydrophobic_interaction(
        self, 
        compound: Compound, 
        profile: Dict
    ) -> float:
        """Calculate hydrophobic interaction score.
        
        Args:
            compound: Compound being evaluated
            profile: Receptor binding site profile
            
        Returns:
            Hydrophobic interaction score (0-1)
        """
        site_hydrophobicity = profile["binding_site_hydrophobicity"]
        compound_logp = compound.logp
        
        # Scale compound logp to same range
        compound_hydrophobicity = compound_logp / 10.0
        
        # Perfect match is ideal
        hydrophobic_match = 1.0 - abs(site_hydrophobicity - compound_hydrophobicity)
        
        # Penalize extreme values
        if compound_logp > 6:
            hydrophobic_match *= 0.7
        elif compound_logp < 0:
            hydrophobic_match *= 0.8
        
        return max(0.0, min(1.0, hydrophobic_match))
    
    def _calculate_electrostatics(
        self, 
        compound: Compound, 
        profile: Dict
    ) -> float:
        """Calculate electrostatic interaction score.
        
        Args:
            compound: Compound being evaluated
            profile: Receptor binding site profile
            
        Returns:
            Electrostatic score (0-1)
        """
        # Balance of charges
        charge_balance = 1.0 - abs(compound.hbd - compound.hba) / max(compound.hbd + compound.hba, 1)
        
        # Penalize extreme charges
        net_charge_penalty = 0.0
        if compound.hbd > 6 or compound.hba > 8:
            net_charge_penalty = 0.2
        
        return max(0.0, min(1.0, charge_balance - net_charge_penalty))
    
    def _calculate_entropy_penalty(self, compound: Compound) -> float:
        """Calculate entropy penalty for binding.
        
        Args:
            compound: Compound being evaluated
            
        Returns:
            Entropy penalty (0-1, higher = more penalty)
        """
        # More rotatable bonds = more entropy loss upon binding
        rotatable_fraction = compound.rotatable_bonds / 15.0
        
        # More rings = less entropy loss (pre-organized)
        ring_bonus = 0.0
        if compound.rotatable_bonds < 5:
            ring_bonus = 0.2
        
        return min(1.0, rotatable_fraction * 0.8 - ring_bonus)
    
    def _calculate_overall_binding_score(
        self, 
        compound: Compound, 
        target: str
    ) -> float:
        """Calculate overall binding score for a compound-target pair.
        
        Args:
            compound: Compound being evaluated
            target: Target protein name
            
        Returns:
            Overall binding score
        """
        profile = self.receptor_profiles.get(
            target.lower(),
            DEFAULT_RECEPTOR_PROFILE
        )
        
        shape = self._calculate_shape_complementarity(compound, profile)
        hbond = self._calculate_hydrogen_bonding(compound, profile)
        hydrophobic = self._calculate_hydrophobic_interaction(compound, profile)
        electro = self._calculate_electrostatics(compound, profile)
        
        return (
            shape * 0.30 +
            hbond * 0.25 +
            hydrophobic * 0.25 +
            electro * 0.20
        )
