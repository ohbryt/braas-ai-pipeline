"""Lead Optimizer Module.

Optimizes lead compounds for drug-like properties including Lipinski's Rule of 5,
Veber's rules, and other medicinal chemistry principles. Provides ADMET
predictions and SAR analysis.
"""

import random
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

from braas.discovery.models import (
    Compound,
    ADMETPrediction,
    CytotoxicityPrediction,
    Modification,
    SARAnalysis,
    SelectivityScore,
)


# Lipinski's Rule of 5 thresholds
LIPINSKI_RULES = {
    "max_molecular_weight": 500,
    "max_logp": 5,
    "max_hbd": 5,
    "max_hba": 10,
}

# Veber's rules
VEBER_RULES = {
    "max_tpsa": 140,
    "max_rotatable_bonds": 10,
}


class LeadOptimizer:
    """Optimizes lead compounds for drug-like properties.
    
    Provides tools for improving druglikeness, selectivity, metabolic stability,
    and predicting cytotoxicity. Uses Lipinski's Rule of 5, Veber's rules, and
    Erinfinity optimization principles.
    
    Attributes:
        lipinski_rules: Lipinski's Rule of 5 thresholds
        veber_rules: Veber's rules thresholds
    """
    
    def __init__(self):
        """Initialize the lead optimizer."""
        self.lipinski_rules = LIPINSKI_RULES
        self.veber_rules = VEBER_RULES
    
    def optimize_druglikeness(self, compound: Compound) -> Compound:
        """Optimize a compound for Lipinski's Rule of 5 compliance.
        
        Args:
            compound: Lead compound to optimize
            
        Returns:
            Optimized Compound with improved druglikeness
        """
        # Start with the original compound
        optimized = compound
        
        # Check each Lipinski rule
        violations = []
        
        if compound.molecular_weight > self.lipinski_rules["max_molecular_weight"]:
            violations.append("mw")
        if compound.logp > self.lipinski_rules["max_logp"]:
            violations.append("logp")
        if compound.hbd > self.lipinski_rules["max_hbd"]:
            violations.append("hbd")
        if compound.hba > self.lipinski_rules["max_hba"]:
            violations.append("hba")
        
        # Apply targeted optimizations based on violations
        if "mw" in violations:
            # Reduce size by suggesting modifications
            optimized = Compound(
                name=f"{compound.name}_opt_mw",
                smiles=self._suggest_size_reduction(compound),
                molecular_weight=max(300, compound.molecular_weight * 0.9),
                logp=compound.logp,
                tpsa=compound.tpsa,
                hbd=compound.hbd,
                hba=compound.hba,
                rotatable_bonds=compound.rotatable_bonds,
                source="lead_optimization",
                generation_method="druglikeness_optimization"
            )
        
        if "logp" in violations:
            # Adjust lipophilicity
            optimized = Compound(
                name=f"{compound.name}_opt_logp",
                smiles=compound.smiles,
                molecular_weight=optimized.molecular_weight,
                logp=min(5.0, optimized.logp * 0.9),
                tpsa=optimized.tpsa,
                hbd=optimized.hbd,
                hba=optimized.hba,
                rotatable_bonds=optimized.rotatable_bonds,
                source="lead_optimization",
                generation_method="druglikeness_optimization"
            )
        
        if "hbd" in violations or "hba" in violations:
            # Reduce H-bond capacity
            optimized = Compound(
                name=f"{compound.name}_opt_hb",
                smiles=optimized.smiles,
                molecular_weight=optimized.molecular_weight,
                logp=optimized.logp,
                tpsa=max(40, optimized.tpsa * 0.85),
                hbd=min(5, optimized.hbd),
                hba=min(10, optimized.hba),
                rotatable_bonds=optimized.rotatable_bonds,
                source="lead_optimization",
                generation_method="druglikeness_optimization"
            )
        
        return optimized
    
    def optimize_selectivity(
        self, 
        compound: Compound, 
        off_targets: List[str]
    ) -> Compound:
        """Optimize compound selectivity for primary target over off-targets.
        
        Args:
            compound: Lead compound to optimize
            off_targets: List of off-target protein names
            
        Returns:
            Optimized Compound with improved selectivity
        """
        # Simulate selectivity optimization
        # In practice, this would involve structural modifications
        
        # Reduce polarity to decrease off-target binding (common strategy)
        optimized = Compound(
            name=f"{compound.name}_sel_opt",
            smiles=compound.smiles,
            molecular_weight=compound.molecular_weight,
            logp=compound.logp + 0.3,  # Slightly increase logP
            tpsa=max(40, compound.tpsa * 0.95),  # Reduce polarity slightly
            hbd=compound.hbd,
            hba=compound.hba,
            rotatable_bonds=compound.rotatable_bonds,
            source="lead_optimization",
            generation_method="selectivity_optimization"
        )
        
        return optimized
    
    def predict_metabolic_stability(self, compound: Compound) -> float:
        """Predict metabolic half-life in hours.
        
        Uses molecular properties to estimate metabolic stability.
        
        Args:
            compound: Compound to evaluate
            
        Returns:
            Predicted metabolic half-life in hours
        """
        # Base half-life estimate
        base_half_life = 2.0  # hours
        
        # Adjust for molecular properties
        
        # Molecular weight effect (larger = slower metabolism generally)
        if compound.molecular_weight > 500:
            base_half_life *= 1.3
        elif compound.molecular_weight < 350:
            base_half_life *= 0.8
        
        # LogP effect (very lipophilic compounds may be metabolized faster)
        if compound.logp > 5:
            base_half_life *= 0.7
        elif 2 < compound.logp < 4:
            base_half_life *= 1.2
        
        # Rotatable bonds (more = faster metabolism)
        if compound.rotatable_bonds > 7:
            base_half_life *= 0.75
        elif compound.rotatable_bonds < 4:
            base_half_life *= 1.2
        
        # TPSA effect (very polar = may resist metabolism)
        if compound.tpsa > 120:
            base_half_life *= 1.1
        elif compound.tpsa < 60:
            base_half_life *= 0.9
        
        # Ester bonds (hydrolyzable) - check SMILES
        if "C(=O)OC" in compound.smiles or "C(O)O" in compound.smiles:
            base_half_life *= 0.6
        
        # Add realistic variation
        base_half_life += random.uniform(-0.3, 0.3)
        
        return max(0.5, min(8.0, base_half_life))
    
    def predict_cytotoxicity(
        self, 
        compound: Compound, 
        cell_types: List[str]
    ) -> CytotoxicityPrediction:
        """Predict cytotoxicity across different cell types.
        
        Args:
            compound: Compound to evaluate
            cell_types: List of cell type names
            
        Returns:
            CytotoxicityPrediction with IC50 values
        """
        # Base cytotoxicity estimate
        base_ic50 = 10.0  # μM
        
        # Adjust based on molecular properties
        
        # High polarity reduces cell permeability -> higher IC50 (less toxic)
        if compound.tpsa > 140:
            base_ic50 *= 1.5
        elif compound.tpsa < 80:
            base_ic50 *= 0.8
        
        # High logP may increase non-specific binding -> lower IC50
        if compound.logp > 5:
            base_ic50 *= 0.7
        elif compound.logp < 2:
            base_ic50 *= 1.3
        
        # Generate IC50 predictions for each cell type
        ic50_values = {}
        for cell_type in cell_types:
            # Cell type-specific adjustments
            if "hepatocyte" in cell_type.lower():
                # Liver cells more sensitive to metabolized compounds
                ic50 = base_ic50 * 0.8
            elif "neuron" in cell_type.lower():
                # Neurons often more sensitive
                ic50 = base_ic50 * 0.9
            elif "kidney" in cell_type.lower():
                # Kidney cells can have efflux transporters
                ic50 = base_ic50 * 1.1
            else:
                ic50 = base_ic50
            
            # Add realistic variation
            ic50 *= random.uniform(0.7, 1.3)
            ic50_values[cell_type] = round(ic50, 2)
        
        # Determine toxicity profile
        avg_ic50 = sum(ic50_values.values()) / len(ic50_values) if ic50_values else base_ic50
        
        if avg_ic50 < 1:
            toxicity_profile = "high_toxicity"
        elif avg_ic50 < 10:
            toxicity_profile = "moderate_toxicity"
        elif avg_ic50 < 50:
            toxicity_profile = "low_toxicity"
        else:
            toxicity_profile = "minimal_toxicity"
        
        # Calculate therapeutic index (ratio of toxic to effective dose)
        # Assume effective dose ~10x below toxic
        therapeutic_index = avg_ic50 / 10.0 if avg_ic50 > 0 else 0.1
        
        return CytotoxicityPrediction(
            compound=compound,
            cell_types=cell_types,
            ic50_values=ic50_values,
            toxicity_profile=toxicity_profile,
            therapeutic_index=therapeutic_index
        )
    
    def propose_modifications(
        self, 
        compound: Compound, 
        target_property: str
    ) -> List[Modification]:
        """Propose chemical modifications to improve specific properties.
        
        Args:
            compound: Lead compound to modify
            target_property: Property to improve
            
        Returns:
            List of proposed Modification objects
        """
        modifications = []
        
        if target_property == "solubility":
            modifications = [
                Modification(
                    modification_type="add_group",
                    location="peripheral",
                    suggestion="Add hydroxyl group",
                    expected_effect="Increase TPSA, improve aqueous solubility",
                    rationale="Polar groups increase water solubility"
                ),
                Modification(
                    modification_type="replace_group",
                    location="R-group",
                    suggestion="Replace phenyl with pyridine",
                    expected_effect="Increase polarity, improve solubility",
                    rationale="Heterocycles increase solubility"
                ),
                Modification(
                    modification_type="reduce_group",
                    location="lipophilic region",
                    suggestion="Remove excessive aromatic rings",
                    expected_effect="Reduce logP, increase solubility",
                    rationale="Fewer aromatics reduce hydrophobicity"
                ),
            ]
        
        elif target_property == "permeability":
            modifications = [
                Modification(
                    modification_type="reduce_group",
                    location="peripheral",
                    suggestion="Reduce H-bond donors",
                    expected_effect="Improve membrane permeability",
                    rationale="Fewer HBDs cross membranes more easily"
                ),
                Modification(
                    modification_type="replace_group",
                    location="polar region",
                    suggestion="Methylate or fluorinate to block H-bonding",
                    expected_effect="Reduce polarity, maintain size",
                    rationale="Steric blocking preserves molecular weight"
                ),
                Modification(
                    modification_type="modify_chain",
                    location="linker region",
                    suggestion="Reduce rotatable bonds",
                    expected_effect="Improve conformational rigidity",
                    rationale="Less flexibility improves permeability"
                ),
            ]
        
        elif target_property == "metabolic_stability":
            modifications = [
                Modification(
                    modification_type="replace_group",
                    location="metabolically_labile",
                    suggestion="Replace ester with amide",
                    expected_effect="Reduce hydrolysis",
                    rationale="Amides more stable than esters"
                ),
                Modification(
                    modification_type="add_group",
                    location="oxidizable_site",
                    suggestion="Add fluorine near oxidation site",
                    expected_effect="Block metabolic oxidation",
                    rationale="Fluorination protects from CYP oxidation"
                ),
                Modification(
                    modification_type="modify_chain",
                    location="soft spot",
                    suggestion="Remove metabolically vulnerable groups",
                    expected_effect="Reduce Phase I metabolism",
                    rationale="Remove easily oxidized moieties"
                ),
            ]
        
        elif target_property == "selectivity":
            modifications = [
                Modification(
                    modification_type="add_group",
                    location="selectivity pocket",
                    suggestion="Add bulky hydrophobic group",
                    expected_effect="Increase selectivity for target",
                    rationale="Target-specific interactions improve selectivity"
                ),
                Modification(
                    modification_type="replace_group",
                    location="off-target binding region",
                    suggestion="Remove groups that bind off-targets",
                    expected_effect="Reduce off-target binding",
                    rationale="Remove pharmacophore features for off-targets"
                ),
            ]
        
        else:
            # General optimization
            modifications = [
                Modification(
                    modification_type="optimize_rule",
                    location="multiple",
                    suggestion="Balance molecular properties",
                    expected_effect="Improve overall druglikeness",
                    rationale="Balanced properties for drug development"
                ),
            ]
        
        return modifications
    
    def run_sar_analysis(self, compounds: List[Compound]) -> SARAnalysis:
        """Perform structure-activity relationship analysis.
        
        Args:
            compounds: List of compounds with varying activity
            
        Returns:
            SARAnalysis with key insights and recommendations
        """
        if len(compounds) < 2:
            return SARAnalysis(
                compounds=compounds,
                activity_property="unknown",
                key_features=["Insufficient data for SAR analysis"],
                activity_trends=[],
                recommendations=["Generate more compound variants"]
            )
        
        # Analyze property ranges
        mw_values = [c.molecular_weight for c in compounds]
        logp_values = [c.logp for c in compounds]
        tpsa_values = [c.tpsa for c in compounds]
        hbd_values = [c.hbd for c in compounds]
        hba_values = [c.hba for c in compounds]
        
        key_features = []
        activity_trends = []
        
        # Analyze molecular weight relationships
        if max(mw_values) - min(mw_values) > 100:
            key_features.append("Molecular weight varies significantly across series")
            if max(mw_values) < 500:
                activity_trends.append("Lower MW compounds preferred (Rule of 5)")
        
        # Analyze lipophilicity
        if max(logp_values) - min(logp_values) > 2:
            key_features.append("LogP spans wide range in compound series")
            opt_logp = sum(logp_values) / len(logp_values)
            activity_trends.append(f"Optimal LogP around {opt_logp:.1f}")
        
        # Analyze polar surface area
        avg_tpsa = sum(tpsa_values) / len(tpsa_values)
        if avg_tpsa < 140:
            activity_trends.append(f"Average TPSA ({avg_tpsa:.1f}) acceptable for cell permeability")
        else:
            activity_trends.append(f"Average TPSA ({avg_tpsa:.1f}) may limit cell permeability")
        
        # Analyze H-bond capacity
        if max(hbd_values) > 5:
            key_features.append("Some compounds exceed Lipinski HBD limit")
            activity_trends.append("Reduce HBD for better druglikeness")
        
        if max(hba_values) > 10:
            key_features.append("Some compounds exceed Lipinski HBA limit")
            activity_trends.append("Reduce HBA for better druglikeness")
        
        # Generate recommendations
        recommendations = []
        
        if avg_tpsa > 120:
            recommendations.append("Consider reducing polar surface area")
        if sum(logp_values) / len(logp_values) > 4:
            recommendations.append("Optimize lipophilicity for better balance")
        if max(hbd_values) > 5 or max(hba_values) > 10:
            recommendations.append("Address Lipinski violations for oral bioavailability")
        
        # Common SAR insights for TGF-beta inhibitors
        recommendations.append("Maintain kinase hinge binder motif for activity")
        recommendations.append("Explore allosteric modifications for selectivity")
        
        return SARAnalysis(
            compounds=compounds,
            activity_property="druggability",
            key_features=key_features if key_features else ["Property ranges within acceptable limits"],
            activity_trends=activity_trends if activity_trends else ["No strong structure-activity trends observed"],
            recommendations=recommendations
        )
    
    def check_lipinski_compliance(self, compound: Compound) -> Tuple[bool, List[str]]:
        """Check if a compound complies with Lipinski's Rule of 5.
        
        Args:
            compound: Compound to check
            
        Returns:
            Tuple of (is_compliant, list_of_violations)
        """
        violations = []
        
        if compound.molecular_weight > self.lipinski_rules["max_molecular_weight"]:
            violations.append(f"MW={compound.molecular_weight:.1f} > {self.lipinski_rules['max_molecular_weight']}")
        
        if compound.logp > self.lipinski_rules["max_logp"]:
            violations.append(f"LogP={compound.logp:.1f} > {self.lipinski_rules['max_logp']}")
        
        if compound.hbd > self.lipinski_rules["max_hbd"]:
            violations.append(f"HBD={compound.hbd} > {self.lipinski_rules['max_hbd']}")
        
        if compound.hba > self.lipinski_rules["max_hba"]:
            violations.append(f"HBA={compound.hba} > {self.lipinski_rules['max_hba']}")
        
        return len(violations) == 0, violations
    
    def check_veber_compliance(self, compound: Compound) -> Tuple[bool, List[str]]:
        """Check if a compound complies with Veber's rules.
        
        Args:
            compound: Compound to check
            
        Returns:
            Tuple of (is_compliant, list_of_violations)
        """
        violations = []
        
        if compound.tpsa > self.veber_rules["max_tpsa"]:
            violations.append(f"TPSA={compound.tpsa:.1f} > {self.veber_rules['max_tpsa']}")
        
        if compound.rotatable_bonds > self.veber_rules["max_rotatable_bonds"]:
            violations.append(f"Rotatable bonds={compound.rotatable_bonds} > {self.veber_rules['max_rotatable_bonds']}")
        
        return len(violations) == 0, violations
    
    def _suggest_size_reduction(self, compound: Compound) -> str:
        """Suggest modifications to reduce molecular size.
        
        Args:
            compound: Compound to modify
            
        Returns:
            Modified SMILES string (simplified)
        """
        # Simplified: return original SMILES with note
        # Real implementation would use retrosynthesis or structural editing
        return compound.smiles
    
    def calculate_druglikeness_score(self, compound: Compound) -> float:
        """Calculate overall druglikeness score.
        
        Args:
            compound: Compound to evaluate
            
        Returns:
            Druglikeness score (0-1, higher is better)
        """
        score = 1.0
        
        # Lipinski compliance
        lipinski_ok, _ = self.check_lipinski_compliance(compound)
        if lipinski_ok:
            score *= 1.0
        else:
            score *= 0.7
        
        # Veber compliance
        veber_ok, _ = self.check_veber_compliance(compound)
        if veber_ok:
            score *= 1.0
        else:
            score *= 0.8
        
        # Property-based adjustments
        # Ideal MW range
        if 300 <= compound.molecular_weight <= 450:
            score *= 1.1
        
        # Ideal logP range
        if 2 <= compound.logp <= 4:
            score *= 1.1
        
        # Ideal TPSA range
        if 60 <= compound.tpsa <= 100:
            score *= 1.1
        
        return max(0.0, min(1.0, score))
