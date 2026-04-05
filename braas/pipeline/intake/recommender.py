"""
BRaaS Pipeline Stage 1 - Experiment Recommender.

Given a research goal, suggest experiment types with estimated
cost, time, and success probability from a built-in knowledge base.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from braas.core.enums import ExperimentType, Organism, SampleType
from braas.core.models import ExperimentRecommendation, IntakeResult


class ExperimentRecommender:
    """
    Recommends experiment types based on research goals.

    Uses a built-in knowledge base of common bioassays with
    cost, time, and success rate estimates to make suggestions.
    """

    # ── Knowledge Base ────────────────────────────────────────────────

    EXPERIMENT_KNOWLEDGE_BASE: Dict[ExperimentType, Dict[str, Any]] = {
        ExperimentType.ELISA: {
            "description": "Enzyme-Linked Immunosorbent Assay for quantitative protein detection",
            "cost_usd": 150.0,
            "time_hours": 6.0,
            "success_probability": 0.90,
            "use_cases": [
                "protein quantification", "cytokine detection",
                "antibody titer", "biomarker screening",
                "serum protein levels", "antigen detection",
            ],
            "compatible_samples": [
                SampleType.SERUM, SampleType.PLASMA, SampleType.CELL_LYSATE,
                SampleType.SUPERNATANT, SampleType.URINE, SampleType.CSF,
            ],
            "prerequisites": [
                "validated antibody pair", "plate reader",
                "standard curve reagents",
            ],
            "throughput": "96-384 samples per run",
            "sensitivity": "pg/mL to ng/mL range",
        },
        ExperimentType.QPCR: {
            "description": "Quantitative PCR for gene expression analysis",
            "cost_usd": 200.0,
            "time_hours": 4.0,
            "success_probability": 0.92,
            "use_cases": [
                "gene expression", "mrna quantification",
                "viral load", "copy number variation",
                "pathogen detection", "gene regulation",
            ],
            "compatible_samples": [
                SampleType.RNA, SampleType.DNA, SampleType.CELL_LYSATE,
                SampleType.TISSUE,
            ],
            "prerequisites": [
                "RNA extraction kit", "reverse transcriptase",
                "validated primers", "qPCR instrument",
            ],
            "throughput": "96-384 reactions per run",
            "sensitivity": "single copy detection",
        },
        ExperimentType.WESTERN_BLOT: {
            "description": "Immunoblotting for protein detection and semi-quantification",
            "cost_usd": 250.0,
            "time_hours": 10.0,
            "success_probability": 0.80,
            "use_cases": [
                "protein detection", "protein size verification",
                "post-translational modifications", "protein expression",
                "signaling pathway analysis", "protein-protein interaction",
            ],
            "compatible_samples": [
                SampleType.CELL_LYSATE, SampleType.TISSUE, SampleType.PROTEIN,
            ],
            "prerequisites": [
                "primary antibody", "secondary antibody",
                "gel electrophoresis system", "transfer apparatus",
                "imaging system",
            ],
            "throughput": "10-15 samples per gel",
            "sensitivity": "ng range",
        },
        ExperimentType.CELL_CULTURE: {
            "description": "In vitro cell propagation and maintenance",
            "cost_usd": 300.0,
            "time_hours": 72.0,
            "success_probability": 0.85,
            "use_cases": [
                "cell expansion", "drug treatment",
                "toxicity testing", "cell-based assay",
                "differentiation", "transfection",
            ],
            "compatible_samples": [
                SampleType.CELL_SUSPENSION, SampleType.TISSUE,
            ],
            "prerequisites": [
                "cell line or primary cells", "growth medium",
                "CO2 incubator", "biosafety cabinet",
                "sterile supplies",
            ],
            "throughput": "variable",
            "sensitivity": "N/A",
        },
        ExperimentType.FLOW_CYTOMETRY: {
            "description": "Multi-parameter cell analysis and sorting",
            "cost_usd": 400.0,
            "time_hours": 5.0,
            "success_probability": 0.85,
            "use_cases": [
                "cell phenotyping", "immune profiling",
                "cell cycle analysis", "apoptosis detection",
                "cell sorting", "surface marker analysis",
            ],
            "compatible_samples": [
                SampleType.CELL_SUSPENSION, SampleType.WHOLE_BLOOD,
            ],
            "prerequisites": [
                "fluorescent antibodies", "flow cytometer",
                "compensation controls",
            ],
            "throughput": "10,000+ cells per second",
            "sensitivity": "single cell",
        },
        ExperimentType.IMMUNOFLUORESCENCE: {
            "description": "Fluorescence-based protein localization in cells/tissues",
            "cost_usd": 200.0,
            "time_hours": 8.0,
            "success_probability": 0.82,
            "use_cases": [
                "protein localization", "co-localization",
                "tissue staining", "cellular morphology",
                "subcellular distribution",
            ],
            "compatible_samples": [
                SampleType.CELL_SUSPENSION, SampleType.TISSUE,
            ],
            "prerequisites": [
                "fluorescent antibodies or probes",
                "fluorescence microscope", "mounting medium",
            ],
            "throughput": "10-50 samples per session",
            "sensitivity": "single molecule (with STORM/PALM)",
        },
        ExperimentType.MASS_SPECTROMETRY: {
            "description": "Mass spectrometry-based protein/metabolite identification",
            "cost_usd": 800.0,
            "time_hours": 24.0,
            "success_probability": 0.78,
            "use_cases": [
                "protein identification", "proteomics",
                "metabolomics", "post-translational modifications",
                "protein quantification", "biomarker discovery",
            ],
            "compatible_samples": [
                SampleType.PROTEIN, SampleType.CELL_LYSATE, SampleType.TISSUE,
                SampleType.SERUM, SampleType.PLASMA,
            ],
            "prerequisites": [
                "mass spectrometer", "sample preparation workflow",
                "bioinformatics pipeline",
            ],
            "throughput": "1000+ proteins per run",
            "sensitivity": "femtomolar range",
        },
        ExperimentType.RNA_SEQ: {
            "description": "Next-generation sequencing of RNA for transcriptome analysis",
            "cost_usd": 1200.0,
            "time_hours": 72.0,
            "success_probability": 0.88,
            "use_cases": [
                "transcriptome profiling", "differential expression",
                "alternative splicing", "novel transcript discovery",
                "gene fusion detection",
            ],
            "compatible_samples": [
                SampleType.RNA, SampleType.CELL_LYSATE, SampleType.TISSUE,
            ],
            "prerequisites": [
                "RNA extraction", "library preparation kit",
                "sequencer access", "bioinformatics pipeline",
            ],
            "throughput": "millions of reads per sample",
            "sensitivity": "low abundance transcripts",
        },
        ExperimentType.CRISPR: {
            "description": "CRISPR-Cas9 gene editing for targeted modifications",
            "cost_usd": 500.0,
            "time_hours": 168.0,  # ~1 week
            "success_probability": 0.70,
            "use_cases": [
                "gene knockout", "gene knock-in",
                "gene activation", "gene repression",
                "functional genomics",
            ],
            "compatible_samples": [
                SampleType.CELL_SUSPENSION, SampleType.DNA,
            ],
            "prerequisites": [
                "guide RNA design", "Cas9 protein or plasmid",
                "transfection reagents", "selection markers",
                "sequencing for validation",
            ],
            "throughput": "1-10 targets per experiment",
            "sensitivity": "N/A",
        },
        ExperimentType.CLONING: {
            "description": "Molecular cloning for construct generation",
            "cost_usd": 180.0,
            "time_hours": 48.0,
            "success_probability": 0.75,
            "use_cases": [
                "construct generation", "gene insertion",
                "vector construction", "library creation",
                "reporter gene assays",
            ],
            "compatible_samples": [
                SampleType.DNA,
            ],
            "prerequisites": [
                "restriction enzymes or assembly kit",
                "competent cells", "vector backbone",
                "sequencing for verification",
            ],
            "throughput": "1-10 constructs per round",
            "sensitivity": "N/A",
        },
        ExperimentType.PROTEIN_PURIFICATION: {
            "description": "Recombinant or native protein purification",
            "cost_usd": 350.0,
            "time_hours": 12.0,
            "success_probability": 0.80,
            "use_cases": [
                "recombinant protein", "native protein isolation",
                "structural studies", "functional assays",
                "antibody production",
            ],
            "compatible_samples": [
                SampleType.CELL_LYSATE, SampleType.PROTEIN,
            ],
            "prerequisites": [
                "chromatography column", "FPLC or gravity flow system",
                "purification buffers", "expression system",
            ],
            "throughput": "mg to g scale",
            "sensitivity": "N/A",
        },
    }

    # ── Research Goal Keywords ─────────────────────────────────────────

    GOAL_TO_EXPERIMENTS: Dict[str, List[ExperimentType]] = {
        "quantify protein": [ExperimentType.ELISA, ExperimentType.WESTERN_BLOT, ExperimentType.MASS_SPECTROMETRY],
        "detect protein": [ExperimentType.ELISA, ExperimentType.WESTERN_BLOT, ExperimentType.IMMUNOFLUORESCENCE],
        "gene expression": [ExperimentType.QPCR, ExperimentType.RNA_SEQ],
        "cell viability": [ExperimentType.CELL_CULTURE],
        "drug response": [ExperimentType.CELL_CULTURE, ExperimentType.FLOW_CYTOMETRY],
        "protein localization": [ExperimentType.IMMUNOFLUORESCENCE],
        "immune profiling": [ExperimentType.FLOW_CYTOMETRY, ExperimentType.ELISA],
        "gene knockout": [ExperimentType.CRISPR],
        "gene editing": [ExperimentType.CRISPR],
        "construct": [ExperimentType.CLONING],
        "plasmid": [ExperimentType.CLONING],
        "purify protein": [ExperimentType.PROTEIN_PURIFICATION],
        "biomarker": [ExperimentType.ELISA, ExperimentType.MASS_SPECTROMETRY, ExperimentType.RNA_SEQ],
        "transcriptome": [ExperimentType.RNA_SEQ],
        "proteomics": [ExperimentType.MASS_SPECTROMETRY],
        "signaling": [ExperimentType.WESTERN_BLOT, ExperimentType.FLOW_CYTOMETRY],
        "apoptosis": [ExperimentType.FLOW_CYTOMETRY, ExperimentType.WESTERN_BLOT],
        "cytokine": [ExperimentType.ELISA, ExperimentType.FLOW_CYTOMETRY],
        "antibody": [ExperimentType.ELISA, ExperimentType.WESTERN_BLOT, ExperimentType.IMMUNOFLUORESCENCE],
        "pathogen": [ExperimentType.QPCR, ExperimentType.ELISA],
        "viral": [ExperimentType.QPCR, ExperimentType.ELISA],
        "mutation": [ExperimentType.CRISPR, ExperimentType.QPCR],
    }

    def __init__(self) -> None:
        """Initialize the experiment recommender."""
        pass

    async def recommend(
        self,
        intake_result: IntakeResult,
        max_recommendations: int = 3,
        budget_limit_usd: Optional[float] = None,
        time_limit_hours: Optional[float] = None,
    ) -> List[ExperimentRecommendation]:
        """
        Recommend experiments based on intake analysis.

        Args:
            intake_result: Parsed intake result from NLP engine.
            max_recommendations: Maximum number of recommendations to return.
            budget_limit_usd: Optional budget constraint.
            time_limit_hours: Optional time constraint.

        Returns:
            List of ExperimentRecommendation sorted by relevance.
        """
        candidates = await self._score_candidates(intake_result)

        # Apply constraints
        if budget_limit_usd is not None:
            candidates = [
                (exp, score) for exp, score in candidates
                if self.EXPERIMENT_KNOWLEDGE_BASE[exp]["cost_usd"] <= budget_limit_usd
            ]

        if time_limit_hours is not None:
            candidates = [
                (exp, score) for exp, score in candidates
                if self.EXPERIMENT_KNOWLEDGE_BASE[exp]["time_hours"] <= time_limit_hours
            ]

        # Sort by score descending
        candidates.sort(key=lambda x: x[1], reverse=True)

        # Build recommendations
        recommendations: List[ExperimentRecommendation] = []
        for exp_type, score in candidates[:max_recommendations]:
            kb = self.EXPERIMENT_KNOWLEDGE_BASE[exp_type]

            # Adjust success probability based on sample compatibility
            success_prob = kb["success_probability"]
            if intake_result.sample_type != SampleType.UNKNOWN:
                if intake_result.sample_type in kb["compatible_samples"]:
                    success_prob = min(success_prob + 0.05, 0.99)
                else:
                    success_prob = max(success_prob - 0.15, 0.3)

            reasoning = self._generate_reasoning(
                exp_type, intake_result, score
            )

            recommendations.append(ExperimentRecommendation(
                experiment_type=exp_type,
                description=kb["description"],
                estimated_cost_usd=kb["cost_usd"],
                estimated_time_hours=kb["time_hours"],
                success_probability=round(success_prob, 2),
                reasoning=reasoning,
                prerequisites=kb["prerequisites"],
            ))

        return recommendations

    async def get_experiment_info(
        self, experiment_type: ExperimentType
    ) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific experiment type.

        Args:
            experiment_type: The experiment type to look up.

        Returns:
            Knowledge base entry or None if not found.
        """
        return self.EXPERIMENT_KNOWLEDGE_BASE.get(experiment_type)

    async def estimate_total_cost(
        self,
        experiment_types: List[ExperimentType],
        sample_count: int = 1,
    ) -> Dict[str, float]:
        """
        Estimate total cost for a set of experiments.

        Args:
            experiment_types: List of experiment types.
            sample_count: Number of samples to process.

        Returns:
            Dict with per-experiment and total cost estimates.
        """
        costs: Dict[str, float] = {}
        total = 0.0

        for exp_type in experiment_types:
            kb = self.EXPERIMENT_KNOWLEDGE_BASE.get(exp_type)
            if kb:
                # Scale cost with sample count (sub-linear for batch savings)
                base_cost = kb["cost_usd"]
                scaled_cost = base_cost * (1.0 + 0.3 * (sample_count - 1))
                costs[exp_type.value] = round(scaled_cost, 2)
                total += scaled_cost

        costs["total"] = round(total, 2)
        return costs

    # ── Private Methods ────────────────────────────────────────────────

    async def _score_candidates(
        self, intake_result: IntakeResult
    ) -> List[tuple]:
        """Score each experiment type for relevance to the intake."""
        scores: Dict[ExperimentType, float] = {
            exp: 0.0 for exp in self.EXPERIMENT_KNOWLEDGE_BASE
        }

        # Direct match from NLP
        if intake_result.experiment_type != ExperimentType.UNKNOWN:
            if intake_result.experiment_type in scores:
                scores[intake_result.experiment_type] += 5.0

        # Goal-based matching
        text_lower = intake_result.raw_text.lower()
        for goal_keyword, exp_types in self.GOAL_TO_EXPERIMENTS.items():
            if goal_keyword in text_lower:
                for exp_type in exp_types:
                    if exp_type in scores:
                        scores[exp_type] += 2.0

        # Sample compatibility bonus
        if intake_result.sample_type != SampleType.UNKNOWN:
            for exp_type, kb in self.EXPERIMENT_KNOWLEDGE_BASE.items():
                if intake_result.sample_type in kb["compatible_samples"]:
                    scores[exp_type] += 1.0

        # Use case keyword matching from raw text
        for exp_type, kb in self.EXPERIMENT_KNOWLEDGE_BASE.items():
            for use_case in kb["use_cases"]:
                if use_case in text_lower:
                    scores[exp_type] += 1.5

        # Filter out zero scores
        return [(exp, score) for exp, score in scores.items() if score > 0]

    def _generate_reasoning(
        self,
        exp_type: ExperimentType,
        intake: IntakeResult,
        score: float,
    ) -> str:
        """Generate human-readable reasoning for a recommendation."""
        kb = self.EXPERIMENT_KNOWLEDGE_BASE[exp_type]
        reasons: List[str] = []

        if intake.experiment_type == exp_type:
            reasons.append(f"Directly matches requested experiment type: {exp_type.value}")

        if intake.sample_type != SampleType.UNKNOWN:
            if intake.sample_type in kb["compatible_samples"]:
                reasons.append(f"Compatible with {intake.sample_type.value} samples")
            else:
                reasons.append(
                    f"Note: {intake.sample_type.value} is not a standard sample type for this assay"
                )

        if intake.target_protein:
            reasons.append(f"Can detect/analyze target: {intake.target_protein}")

        reasons.append(f"Relevance score: {score:.1f}")
        reasons.append(f"Throughput: {kb['throughput']}")

        return "; ".join(reasons)
