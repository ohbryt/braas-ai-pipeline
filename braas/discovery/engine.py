"""Drug Discovery Engine Module.

Main orchestrator for the drug discovery pipeline that coordinates compound
generation, target analysis, virtual screening, and candidate ranking.
Provides a unified interface for the complete drug discovery workflow.
"""

import random
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from braas.discovery.models import (
    Compound,
    CompoundScore,
    DrugCandidate,
    TargetAnalysis,
    ADMETPrediction,
    BindingSite,
    DruggabilityScore,
    PathwayContext,
)
from braas.discovery.generator import CompoundGenerator
from braas.discovery.target import TargetAnalyzer
from braas.discovery.docking import DockingSimulator
from braas.discovery.lead_optimizer import LeadOptimizer


# Default weights for candidate ranking
RANKING_WEIGHTS = {
    "efficacy": 0.35,
    "safety": 0.30,
    "admet": 0.20,
    "synthesizability": 0.15,
}


class DrugDiscoveryEngine:
    """Main orchestrator for drug discovery pipeline.
    
    Coordinates compound generation, target analysis, virtual screening,
    and candidate ranking to identify promising drug candidates.
    
    Attributes:
        generator: CompoundGenerator instance
        target_analyzer: TargetAnalyzer instance
        docking_simulator: DockingSimulator instance
        lead_optimizer: LeadOptimizer instance
        ranking_weights: Weights for candidate ranking
    """
    
    def __init__(self):
        """Initialize the drug discovery engine with all sub-modules."""
        self.generator = CompoundGenerator()
        self.target_analyzer = TargetAnalyzer()
        self.docking_simulator = DockingSimulator()
        self.lead_optimizer = LeadOptimizer()
        self.ranking_weights = RANKING_WEIGHTS.copy()
    
    def discover_drugs(
        self,
        target_protein: str,
        disease_area: str,
        organism: str = "human",
        num_leads: int = 50,
        num_candidates: int = 10
    ) -> List[DrugCandidate]:
        """Run full drug discovery pipeline for a target.
        
        Complete workflow:
        1. Analyze target protein
        2. Generate lead compounds
        3. Virtual screening with docking
        4. ADMET prediction
        5. Lead optimization
        6. Candidate ranking
        
        Args:
            target_protein: Name of target protein (e.g., 'myostatin', 'ALK5')
            disease_area: Therapeutic area (e.g., 'muscular dystrophy', 'fibrosis')
            organism: Target organism (default: 'human')
            num_leads: Number of lead compounds to generate
            num_candidates: Number of final candidates to return
            
        Returns:
            List of DrugCandidate objects ranked by overall score
        """
        # Step 1: Analyze target
        target_analysis = self.target_analyzer.analyze_target(target_protein)
        
        # Step 2: Generate lead compounds
        leads = self.generator.generate_lead_compounds(target_protein, num_leads)
        
        # Step 3: Virtual screening
        screened = self.screen_compounds(leads, target_protein)
        
        # Step 4: Generate candidates with ADMET predictions
        candidates = []
        for score_entry in screened[:num_candidates * 2]:  # Get more for filtering
            compound = score_entry.compound
            
            # Predict ADMET
            admet = self.predict_admet(compound)
            
            # Skip compounds with high toxicity
            if admet.toxicity_class == "high":
                continue
            
            # Calculate efficacy score (based on docking)
            efficacy = min(1.0, max(0.0, (score_entry.docking_score + 10) / 20))
            
            # Calculate safety score (based on ADMET)
            safety = admet.score
            
            # Calculate clinical relevance
            clinical_relevance = self._assess_clinical_relevance(
                compound, target_analysis, disease_area
            )
            
            # Calculate novelty score
            novelty = self._assess_novelty(compound)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                compound, admet, efficacy, safety
            )
            
            candidate = DrugCandidate(
                compound=compound,
                target=target_protein,
                indication=disease_area,
                stage="lead",
                efficacy_score=efficacy,
                safety_score=safety,
                admet_profile=admet,
                clinical_relevance=clinical_relevance,
                novelty_score=novelty,
                recommendations=recommendations
            )
            candidates.append(candidate)
        
        # Step 5: Rank candidates
        ranked_candidates = self.rank_candidates(candidates)
        
        # Return top N candidates
        return ranked_candidates[:num_candidates]
    
    def screen_compounds(
        self,
        compounds: List[Compound],
        target: str
    ) -> List[CompoundScore]:
        """Perform virtual screening with scoring.
        
        Args:
            compounds: List of compounds to screen
            target: Target protein name
            
        Returns:
            List of CompoundScore objects sorted by overall score
        """
        scores = []
        
        for compound in compounds:
            # Dock compound
            docking_result = self.docking_simulator.dock_compound(compound, target)
            
            # Predict ADMET
            admet = self.predict_admet(compound)
            
            # Score synthesizability
            synthesizability = self.generator.score_synthesizability(compound)
            
            # Calculate overall score
            overall = (
                docking_result.pose_confidence * 0.4 +
                admet.score * 0.35 +
                synthesizability * 0.25
            )
            
            scores.append(CompoundScore(
                compound=compound,
                docking_score=docking_result.binding_score_kcal,
                admet_score=admet.score,
                synthesizability_score=synthesizability,
                overall_score=overall,
                ranking=0
            ))
        
        # Sort by overall score
        scores.sort(key=lambda x: x.overall_score, reverse=True)
        
        # Assign rankings
        for i, score in enumerate(scores):
            score.ranking = i + 1
        
        return scores
    
    def predict_admet(self, compound: Compound) -> ADMETPrediction:
        """Predict ADMET properties using heuristic models.
        
        Args:
            compound: Compound to evaluate
            
        Returns:
            ADMETPrediction with property predictions
        """
        warnings = []
        
        # Absorption prediction
        if compound.tpsa > 150:
            absorption = "low"
            warnings.append("High TPSA may limit intestinal absorption")
        elif compound.tpsa < 60:
            absorption = "moderate"
        else:
            absorption = "high"
        
        if compound.logp < 0:
            absorption = "poor"
            warnings.append("Very low logP may affect membrane permeability")
        
        # Distribution prediction
        if compound.logp > 4 and compound.tpsa < 100:
            distribution = "wide"
        elif compound.tpsa > 140:
            distribution = "limited"
        else:
            distribution = "moderate"
        
        # Metabolism prediction
        if compound.rotatable_bonds > 8:
            metabolism = "fast"
            warnings.append("High flexibility may lead to rapid metabolism")
        elif compound.molecular_weight > 500:
            metabolism = "slow"
        else:
            metabolism = "moderate"
        
        # Check for metabolically unstable groups
        unstable_groups = ["C(=O)OC", "O-C(=O)", "-O-"]  # Esters, ethers
        for group in unstable_groups:
            if group in compound.smiles:
                metabolism = "fast"
                warnings.append("Contains metabolically labile group")
                break
        
        # Excretion prediction
        if compound.molecular_weight < 400:
            excretion = "renal"
        elif compound.logp > 3:
            excretion = "biliary"
        else:
            excretion = "hepatic"
        
        # Toxicity classification
        toxicity_violations = 0
        
        if compound.molecular_weight > 600:
            toxicity_violations += 1
        if compound.logp > 6:
            toxicity_violations += 1
        if compound.hbd > 6:
            toxicity_violations += 1
        if compound.hba > 12:
            toxicity_violations += 1
        
        if toxicity_violations >= 2:
            toxicity_class = "high"
            warnings.append("Multiple property violations suggest potential toxicity")
        elif toxicity_violations == 1:
            toxicity_class = "moderate"
        else:
            toxicity_class = "acceptable"
        
        # Calculate overall ADMET score
        score = 1.0
        
        # Absorption contribution
        absorption_scores = {"high": 1.0, "moderate": 0.75, "low": 0.5, "poor": 0.25}
        score *= absorption_scores.get(absorption, 0.5)
        
        # Distribution contribution
        dist_scores = {"wide": 0.9, "moderate": 0.8, "limited": 0.6}
        score *= dist_scores.get(distribution, 0.7)
        
        # Metabolism contribution
        metab_scores = {"slow": 0.9, "moderate": 0.8, "fast": 0.6}
        score *= metab_scores.get(metabolism, 0.7)
        
        # Toxicity penalty
        tox_scores = {"acceptable": 1.0, "moderate": 0.7, "high": 0.4}
        score *= tox_scores.get(toxicity_class, 0.5)
        
        return ADMETPrediction(
            absorption=absorption,
            distribution=distribution,
            metabolism=metabolism,
            excretion=excretion,
            toxicity_class=toxicity_class,
            warnings=warnings,
            score=max(0.0, min(1.0, score))
        )
    
    def generate_report(self, candidates: List[DrugCandidate]) -> str:
        """Generate markdown summary report of drug candidates.
        
        Args:
            candidates: List of DrugCandidate objects
            
        Returns:
            Markdown-formatted report string
        """
        if not candidates:
            return "# Drug Discovery Report\n\nNo candidates to report.\n"
        
        report_lines = [
            "# Drug Discovery Report",
            "",
            f"## Summary",
            f"",
            f"- **Total Candidates:** {len(candidates)}",
            f"- **Top Candidate:** {candidates[0].compound.name}",
            f"- **Top Candidate Score:** {self._calculate综合_score(candidates[0]):.3f}",
            "",
            "---",
            "",
            "## Candidate Rankings",
            "",
        ]
        
        # Table header
        report_lines.extend([
            "| Rank | Compound | Target | Efficacy | Safety | ADMET | 综合 Score |",
            "|------|----------|--------|----------|--------|-------|------------|"
        ])
        
        # Table rows
        for i, candidate in enumerate(candidates):
            综合_score = self._calculate综合_score(candidate)
            row = f"| {i+1} | {candidate.compound.name} | {candidate.target} | "
            row += f"{candidate.efficacy_score:.2f} | {candidate.safety_score:.2f} | "
            row += f"{candidate.admet_profile.score:.2f} | {综合_score:.3f} |"
            report_lines.append(row)
        
        report_lines.extend(["", "---", "", "## Detailed Analysis", ""])
        
        # Detailed analysis for top candidates
        for i, candidate in enumerate(candidates[:5]):
            综合_score = self._calculate综合_score(candidate)
            report_lines.extend([
                f"### {i+1}. {candidate.compound.name}",
                "",
                f"**Target:** {candidate.target}",
                f"**Indication:** {candidate.indication}",
                f"**Stage:** {candidate.stage}",
                "",
                f"**Properties:**",
                f"- Molecular Weight: {candidate.compound.molecular_weight:.1f} Da",
                f"- LogP: {candidate.compound.logp:.2f}",
                f"- TPSA: {candidate.compound.tpsa:.1f} Å²",
                f"- HBD: {candidate.compound.hbd}, HBA: {candidate.compound.hba}",
                f"- Rotatable Bonds: {candidate.compound.rotatable_bonds}",
                "",
                f"**Scores:**",
                f"- Efficacy: {candidate.efficacy_score:.3f}",
                f"- Safety: {candidate.safety_score:.3f}",
                f"- ADMET: {candidate.admet_profile.score:.3f}",
                f"- Novelty: {candidate.novelty_score:.3f}",
                f"- **综合 Score: {综合_score:.3f}**",
                "",
                f"**ADMET Profile:**",
                f"- Absorption: {candidate.admet_profile.absorption}",
                f"- Distribution: {candidate.admet_profile.distribution}",
                f"- Metabolism: {candidate.admet_profile.metabolism}",
                f"- Excretion: {candidate.admet_profile.excretion}",
                f"- Toxicity: {candidate.admet_profile.toxicity_class}",
                "",
            ])
            
            if candidate.admet_profile.warnings:
                report_lines.append("**Warnings:**")
                for warning in candidate.admet_profile.warnings:
                    report_lines.append(f"- {warning}")
                report_lines.append("")
            
            if candidate.recommendations:
                report_lines.append("**Recommendations:**")
                for rec in candidate.recommendations:
                    report_lines.append(f"- {rec}")
                report_lines.append("")
            
            report_lines.append("---")
            report_lines.append("")
        
        return "\n".join(report_lines)
    
    def rank_candidates(self, candidates: List[DrugCandidate]) -> List[DrugCandidate]:
        """Rank drug candidates by 综合 score.
        
        综合 score combines efficacy, safety, ADMET properties, and synthesizability.
        
        Args:
            candidates: List of DrugCandidate objects
            
        Returns:
            Sorted list of DrugCandidate objects (best first)
        """
        # Calculate 综合 score for each candidate
        scored_candidates = []
        for candidate in candidates:
            综合_score = self._calculate综合_score(candidate)
            scored_candidates.append((candidate, 综合_score))
        
        # Sort by 综合 score
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        
        # Return sorted candidates
        return [c[0] for c in scored_candidates]
    
    def _calculate综合_score(self, candidate: DrugCandidate) -> float:
        """Calculate 综合 (overall) score for a candidate.
        
        Args:
            candidate: DrugCandidate to score
            
        Returns:
            综合 score (0-1)
        """
        # Calculate synthesizability from optimizer
        synthesizability = self.generator.score_synthesizability(candidate.compound)
        
        综合 = (
            candidate.efficacy_score * self.ranking_weights["efficacy"] +
            candidate.safety_score * self.ranking_weights["safety"] +
            candidate.admet_profile.score * self.ranking_weights["admet"] +
            synthesizability * self.ranking_weights["synthesizability"]
        )
        
        # Boost for novelty
        综合 += candidate.novelty_score * 0.05
        
        # Boost for clinical relevance
        综合 += candidate.clinical_relevance * 0.1
        
        return max(0.0, min(1.0, 综合))
    
    def _assess_clinical_relevance(
        self,
        compound: Compound,
        target_analysis: TargetAnalysis,
        disease_area: str
    ) -> float:
        """Assess clinical relevance of a candidate.
        
        Args:
            compound: Compound being evaluated
            target_analysis: Target analysis results
            disease_area: Proposed disease area
            
        Returns:
            Clinical relevance score (0-1)
        """
        score = 0.5
        
        # Check if target is well-validated
        if target_analysis.druggability:
            if target_analysis.druggability.classification == "highly_druggable":
                score += 0.2
            elif target_analysis.druggability.classification == "druggable":
                score += 0.1
        
        # Check pathway context
        if target_analysis.pathway_context:
            if disease_area.lower() in str(target_analysis.pathway_context.disease_associations).lower():
                score += 0.2
        
        # Check druglikeness
        lipinski_ok, _ = self.lead_optimizer.check_lipinski_compliance(compound)
        if lipinski_ok:
            score += 0.1
        
        return min(1.0, max(0.0, score))
    
    def _assess_novelty(self, compound: Compound) -> float:
        """Assess structural novelty of a compound.
        
        Args:
            compound: Compound to evaluate
            
        Returns:
            Novelty score (0-1)
        """
        # Compare to known scaffolds
        known_scaffolds = self.generator.get_scaffold_library()
        
        # Simple novelty assessment based on molecular properties
        # In practice, would use structural fingerprints or Tanimoto similarity
        
        novelty = 0.5
        
        # Unusual molecular weight
        if compound.molecular_weight < 300 or compound.molecular_weight > 550:
            novelty += 0.2
        
        # Unusual logP
        if compound.logp < 1.5 or compound.logp > 5:
            novelty += 0.1
        
        # Low rotatable bonds (rigidity often indicates novel chemotypes)
        if compound.rotatable_bonds < 4:
            novelty += 0.1
        
        return min(1.0, max(0.0, novelty))
    
    def _generate_recommendations(
        self,
        compound: Compound,
        admet: ADMETPrediction,
        efficacy: float,
        safety: float
    ) -> List[str]:
        """Generate recommendations for compound progression.
        
        Args:
            compound: Compound being evaluated
            admet: ADMET prediction results
            efficacy: Efficacy score
            safety: Safety score
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        # Efficacy-based recommendations
        if efficacy > 0.7:
            recommendations.append("High efficacy - prioritize for lead optimization")
        elif efficacy < 0.4:
            recommendations.append("Consider structural modifications to improve binding")
        
        # Safety-based recommendations
        if safety > 0.8:
            recommendations.append("Favorable safety profile - proceed with IND-enabling studies")
        elif safety < 0.5:
            recommendations.append("Address safety concerns before progression")
        
        # ADMET-based recommendations
        if admet.absorption == "low":
            recommendations.append("Improve solubility/permeability for oral delivery")
        if admet.metabolism == "fast":
            recommendations.append("Consider metabolic stabilization strategies")
        if admet.toxicity_class != "acceptable":
            recommendations.append(f"Address {admet.toxicity_class} toxicity concerns")
        
        # Property-based recommendations
        if compound.molecular_weight > 500:
            recommendations.append("Reduce molecular weight for better druglikeness")
        if compound.logp > 5:
            recommendations.append("Reduce lipophilicity for better ADME properties")
        
        # General recommendations
        if not recommendations:
            recommendations.append("Continue optimization and in vitro validation")
        
        return recommendations
    
    def get_pipeline_status(self) -> Dict[str, str]:
        """Get status of all pipeline components.
        
        Returns:
            Dictionary with component statuses
        """
        return {
            "generator": "ready" if self.generator else "unavailable",
            "target_analyzer": "ready" if self.target_analyzer else "unavailable",
            "docking_simulator": "ready" if self.docking_simulator else "unavailable",
            "lead_optimizer": "ready" if self.lead_optimizer else "unavailable",
            "rdkit_available": str(self.generator.rdkit_available),
        }
