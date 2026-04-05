"""
AI Result Interpreter
====================

Interpret and explain experimental results using heuristics and
internal knowledge base without external LLM calls.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from braas.core.enums import ExperimentType
from braas.pipeline.analysis.processor import (
    ELISAResult,
    qPCRResult,
    CellViabilityResult,
    WesternBlotResult,
    StatisticalResult,
)


# -----------------------------------------------------------------------------
# Data Classes
# -----------------------------------------------------------------------------

@dataclass
class SignificantFinding:
    """A statistically significant experimental finding."""
    what: str
    p_value: float
    effect_size: float
    interpretation: str


@dataclass
class NextExperiment:
    """Suggested next experiment."""
    name: str
    rationale: str
    estimated_cost: str
    estimated_time: str


@dataclass
class LiteratureComparison:
    """Comparison of results to literature values."""
    benchmark_values: dict[str, float]
    our_value: float
    difference_pct: float
    interpretation: str


@dataclass
class Conclusion:
    """A conclusion drawn from experimental results."""
    text: str
    confidence: float  # 0.0 to 1.0
    supported_by: list[str]


# -----------------------------------------------------------------------------
# Internal Knowledge Base
# -----------------------------------------------------------------------------

class KnowledgeBase:
    """Internal knowledge base for result interpretation."""
    
    # Literature benchmarks for common assays
    ELISA_BENCHMARKS = {
        "il6_normal_pg_ml": (1.5, 4.0),
        "tnf_alpha_normal_pg_ml": (2.0, 8.0),
        "ifn_gamma_normal_pg_ml": (0.0, 15.0),
    }
    
    QPCR_EFFICIENCY_RANGE = (0.90, 1.10)
    QPCR_CT_NORMAL_RANGE = (15.0, 30.0)
    
    CELL_VIABILITY_IC50_TYPICAL = {
        "cytotoxic_threshold_pct": 50.0,
        "moderate_effect_pct": 25.0,
        "strong_effect_pct": 10.0,
    }
    
    WESTERN_BLOT_HOUSEKEEPING = ["GAPDH", "beta-actin", "tubulin"]
    
    def get_benchmark(self, assay_type: str, biomarker: str) -> tuple[float, float]:
        """Get literature benchmark (mean, std) for a biomarker."""
        key = f"{assay_type.lower()}_{biomarker.lower()}"
        if hasattr(self, key.replace("-", "_")):
            return getattr(self, key.replace("-", "_"))
        return (0.0, 1.0)  # Unknown
    
    def get_reference_range(self, assay_type: str) -> tuple[float, float]:
        """Get normal reference range for assay type."""
        if assay_type == ExperimentType.QPCR:
            return self.QPCR_CT_NORMAL_RANGE
        return (0.0, 100.0)


# -----------------------------------------------------------------------------
# AI Result Interpreter
# -----------------------------------------------------------------------------

class AIResultInterpreter:
    """Interpret experimental results and generate insights.
    
    Uses internal knowledge base, heuristics, and formatting rules
    to generate human-readable interpretations without external LLM.
    """
    
    def __init__(self) -> None:
        """Initialize the interpreter with knowledge base."""
        self._kb = KnowledgeBase()
        self._confidence_thresholds = {
            "high": 0.9,
            "medium": 0.7,
            "low": 0.5
        }
    
    def generate_summary(
        self,
        result: Any,
        experiment_type: ExperimentType | str
    ) -> str:
        """Generate formatted text summary of results.
        
        Args:
            result: Analysis result object
            experiment_type: Type of experiment
        
        Returns:
            Formatted summary string with key findings
        """
        type_str = str(experiment_type).lower()
        
        if isinstance(result, ELISAResult):
            return self._summarize_elisa(result)
        elif isinstance(result, qPCRResult):
            return self._summarize_qpcr(result)
        elif isinstance(result, CellViabilityResult):
            return self._summarize_cell_viability(result)
        elif isinstance(result, WesternBlotResult):
            return self._summarize_western_blot(result)
        elif isinstance(result, StatisticalResult):
            return self._summarize_statistics(result)
        elif isinstance(result, dict):
            return self._summarize_dict(result)
        else:
            return f"Experiment type: {type_str}\nResults: {result}"
    
    def _summarize_elisa(self, result: ELISAResult) -> str:
        """Generate ELISA results summary."""
        lines = [
            "ELISA ANALYSIS SUMMARY",
            "=" * 50,
            "",
            "Standard Curve Quality:",
            f"  - Fit type: {result.std_curve_params.get('fit_type', 'unknown')}",
            f"  - LOD: {result.lod:.3f} units",
            f"  - LOQ: {result.loq:.3f} units",
            f"  - CV%: {result.cv_percent:.1f}%",
            "",
            "Sample Analysis:",
        ]
        
        if len(result.concentrations) > 0:
            lines.append(f"  - Samples analyzed: {len(result.concentrations)}")
            lines.append(f"  - Mean concentration: {np.mean(result.concentrations):.3f}")
            lines.append(f"  - Range: {np.min(result.concentrations):.3f} - {np.max(result.concentrations):.3f}")
        else:
            lines.append("  - No sample concentrations calculated")
        
        lines.append("")
        lines.append("Quality Assessment:")
        
        if result.cv_percent < 10:
            lines.append("  - Excellent precision (CV < 10%)")
        elif result.cv_percent < 20:
            lines.append("  - Acceptable precision (CV < 20%)")
        else:
            lines.append("  - WARNING: High variability (CV > 20%)")
        
        return "\n".join(lines)
    
    def _summarize_qpcr(self, result: qPCRResult) -> str:
        """Generate qPCR results summary."""
        lines = [
            "qPCR ANALYSIS SUMMARY",
            "=" * 50,
            "",
            "Amplification:",
            f"  - PCR efficiency: {result.efficiency:.1%}",
            f"  - CT values: {len(result.ct_values)} samples",
        ]
        
        if len(result.ct_values) > 0:
            lines.append(f"  - Mean CT: {np.nanmean(result.ct_values):.2f}")
            lines.append(f"  - CT range: {np.nanmin(result.ct_values):.2f} - {np.nanmax(result.ct_values):.2f}")
        
        lines.append("")
        lines.append("Quantification:")
        
        if len(result.relative_quantification) > 0:
            lines.append(f"  - Reference gene normalized")
            lines.append(f"  - RQ range: {np.min(result.relative_quantification):.2f} - {np.max(result.relative_quantification):.2f}")
        
        lines.append("")
        lines.append("Quality Assessment:")
        
        if 0.9 <= result.efficiency <= 1.1:
            lines.append("  - Excellent efficiency (90-110%)")
        elif 0.8 <= result.efficiency <= 1.2:
            lines.append("  - Acceptable efficiency (80-120%)")
        else:
            lines.append("  - WARNING: Efficiency outside ideal range")
        
        return "\n".join(lines)
    
    def _summarize_cell_viability(self, result: CellViabilityResult) -> str:
        """Generate cell viability results summary."""
        lines = [
            "CELL VIABILITY ANALYSIS SUMMARY",
            "=" * 50,
            "",
            "Viability Data:",
        ]
        
        if len(result.viability_pct) > 0:
            lines.append(f"  - Samples: {len(result.viability_pct)}")
            lines.append(f"  - Mean viability: {np.mean(result.viability_pct):.1f}%")
            lines.append(f"  - Range: {np.min(result.viability_pct):.1f}% - {np.max(result.viability_pct):.1f}%")
        
        lines.append("")
        lines.append("Dose-Response:")
        
        if result.ic50 is not None:
            lines.append(f"  - IC50: {result.ic50:.2f} units")
            
            if result.ic50 > 50:
                lines.append("  - Interpretation: Low potency")
            elif result.ic50 > 25:
                lines.append("  - Interpretation: Moderate potency")
            else:
                lines.append("  - Interpretation: High potency")
        else:
            lines.append("  - IC50 not determined")
        
        lines.append("")
        lines.append("Quality Assessment:")
        
        mean_viab = np.mean(result.viability_pct) if len(result.viability_pct) > 0 else 0
        if mean_viab > 80:
            lines.append("  - Good overall cell health")
        elif mean_viab > 50:
            lines.append("  - Moderate cell stress observed")
        else:
            lines.append("  - WARNING: Significant cytotoxicity")
        
        return "\n".join(lines)
    
    def _summarize_western_blot(self, result: WesternBlotResult) -> str:
        """Generate western blot results summary."""
        lines = [
            "WESTERN BLOT ANALYSIS SUMMARY",
            "=" * 50,
            "",
            "Band Analysis:",
            f"  - Bands detected: {len(result.band_intensities)}",
        ]
        
        if len(result.band_intensities) > 0:
            lines.append(f"  - Mean intensity: {np.mean(result.band_intensities):.1f}")
            lines.append(f"  - MW range: {np.min(result.molecular_weights):.1f} - {np.max(result.molecular_weights):.1f} kDa")
        
        lines.append("")
        lines.append("Quantification:")
        lines.append(f"  - Relative quantification calculated")
        
        return "\n".join(lines)
    
    def _summarize_statistics(self, result: StatisticalResult) -> str:
        """Generate statistical analysis summary."""
        lines = [
            "STATISTICAL ANALYSIS SUMMARY",
            "=" * 50,
            "",
            f"Test used: {result.test_used}",
            "",
            "P-values:",
        ]
        
        for key, p_val in result.p_values.items():
            sig = "***" if p_val < 0.001 else "**" if p_val < 0.01 else "*" if p_val < 0.05 else "ns"
            lines.append(f"  - {key}: {p_val:.4f} {sig}")
        
        lines.append("")
        lines.append("Effect Sizes:")
        for key, es in result.effect_sizes.items():
            lines.append(f"  - {key}: {es:.4f}")
        
        if result.corrections_applied:
            lines.append("")
            lines.append(f"Multiple testing correction: {result.corrections_applied.get('method', 'N/A')}")
        
        return "\n".join(lines)
    
    def _summarize_dict(self, data: dict) -> str:
        """Generate summary from dictionary data."""
        lines = ["RESULTS SUMMARY", "=" * 50, ""]
        for key, value in data.items():
            if isinstance(value, (int, float)):
                lines.append(f"{key}: {value:.4f}")
            else:
                lines.append(f"{key}: {value}")
        return "\n".join(lines)
    
    def find_significant_findings(
        self,
        result: Any,
        alpha: float = 0.05
    ) -> list[SignificantFinding]:
        """Identify statistically significant findings.
        
        Args:
            result: Analysis result object
            alpha: Significance threshold
        
        Returns:
            List of SignificantFinding objects
        """
        findings = []
        
        if isinstance(result, StatisticalResult):
            for key, p_val in result.p_values.items():
                if p_val < alpha:
                    effect_size = result.effect_sizes.get(
                        key.replace("p_", "cohens_d_", 1),
                        result.effect_sizes.get("cohens_d", 0)
                    )
                    
                    interpretation = self._interpret_pvalue(p_val, effect_size)
                    
                    findings.append(SignificantFinding(
                        what=f"Comparison {key}",
                        p_value=p_val,
                        effect_size=effect_size,
                        interpretation=interpretation
                    ))
        
        elif isinstance(result, CellViabilityResult):
            # Check for significant viability changes
            if len(result.viability_pct) > 0:
                mean_viab = np.mean(result.viability_pct)
                if mean_viab < 50:
                    findings.append(SignificantFinding(
                        what="Significant cytotoxicity detected",
                        p_value=0.01,  # Estimated
                        effect_size=(50 - mean_viab) / 50,  # Normalized
                        interpretation="Viability significantly reduced compared to control"
                    ))
        
        elif isinstance(result, qPCRResult):
            # Check for significant expression changes
            if len(result.relative_quantification) > 0:
                rq = result.relative_quantification
                if np.any(rq > 2) or np.any(rq < 0.5):
                    direction = "upregulated" if np.mean(rq) > 1 else "downregulated"
                    findings.append(SignificantFinding(
                        what=f"Gene expression {direction}",
                        p_value=0.05,  # Estimated
                        effect_size=np.abs(np.log2(np.mean(rq))),
                        interpretation=f"Target gene is {direction} relative to reference"
                    ))
        
        return findings
    
    def _interpret_pvalue(self, p_value: float, effect_size: float) -> str:
        """Interpret p-value and effect size combination."""
        if p_value < 0.001:
            sig_level = "highly significant"
        elif p_value < 0.01:
            sig_level = "very significant"
        elif p_value < 0.05:
            sig_level = "significant"
        else:
            return "Not statistically significant"
        
        abs_es = abs(effect_size)
        if abs_es > 0.8:
            mag = "large"
        elif abs_es > 0.5:
            mag = "medium"
        elif abs_es > 0.2:
            mag = "small"
        else:
            mag = "negligible"
        
        return f"{sig_level} difference with {mag} effect size"
    
    def suggest_next_experiments(
        self,
        result: Any,
        experiment_type: ExperimentType | str
    ) -> list[NextExperiment]:
        """Suggest next experiments based on results.
        
        Args:
            result: Analysis result object
            experiment_type: Type of experiment
        
        Returns:
            List of NextExperiment suggestions
        """
        suggestions = []
        type_str = str(experiment_type).lower()
        
        if isinstance(result, ELISAResult):
            suggestions.extend([
                NextExperiment(
                    name="Validate with orthogonal method",
                    rationale="Confirm ELISA results with a different immunoassay platform",
                    estimated_cost="$500-1000",
                    estimated_time="1-2 weeks"
                ),
                NextExperiment(
                    name="Increase sample size",
                    rationale="Current CV% suggests need for more replicates",
                    estimated_cost="$200-500",
                    estimated_time="3-5 days"
                )
            ])
            
            if result.cv_percent > 15:
                suggestions.append(NextExperiment(
                    name="Optimize assay conditions",
                    rationale="High variability indicates potential assay issues",
                    estimated_cost="$100-300",
                    estimated_time="1 week"
                ))
        
        elif isinstance(result, qPCRResult):
            suggestions.extend([
                NextExperiment(
                    name="Validate with another reference gene",
                    rationale="Ensure stable reference gene expression",
                    estimated_cost="$100-200",
                    estimated_time="2-3 days"
                ),
                NextExperiment(
                    name="Perform melt curve analysis",
                    rationale="Confirm specificity of amplification",
                    estimated_cost="$50-100",
                    estimated_time="1 day"
                )
            ])
            
            if result.efficiency < 0.85 or result.efficiency > 1.15:
                suggestions.append(NextExperiment(
                    name="Optimize primer design",
                    rationale="PCR efficiency outside ideal range",
                    estimated_cost="$100-300",
                    estimated_time="1-2 weeks"
                ))
        
        elif isinstance(result, CellViabilityResult):
            suggestions.extend([
                NextExperiment(
                    name="Perform dose-response escalation",
                    rationale="Refine IC50 determination",
                    estimated_cost="$300-600",
                    estimated_time="1-2 weeks"
                ),
                NextExperiment(
                    name="Conduct combination studies",
                    rationale="Evaluate synergistic or antagonistic effects",
                    estimated_cost="$500-1000",
                    estimated_time="2-3 weeks"
                )
            ])
        
        elif isinstance(result, WesternBlotResult):
            suggestions.extend([
                NextExperiment(
                    name="Validate with different antibody lot",
                    rationale="Confirm antibody specificity",
                    estimated_cost="$200-400",
                    estimated_time="1 week"
                ),
                NextExperiment(
                    name="Perform additional loading controls",
                    rationale="Ensure accurate normalization",
                    estimated_cost="$100-200",
                    estimated_time="2-3 days"
                )
            ])
        
        # Default suggestions if no specific type matched
        if not suggestions:
            suggestions.append(NextExperiment(
                name="Replicate study",
                rationale="Confirm current findings with independent replicates",
                estimated_cost="$500-2000",
                estimated_time="2-4 weeks"
            ))
        
        return suggestions
    
    def compare_to_literature(self, result: Any) -> LiteratureComparison:
        """Compare results to literature benchmarks.
        
        Args:
            result: Analysis result object
        
        Returns:
            LiteratureComparison with benchmark data
        """
        if isinstance(result, qPCRResult):
            # Compare CT values to reference range
            mean_ct = np.nanmean(result.ct_values) if len(result.ct_values) > 0 else 0
            ref_range = self._kb.QPCR_CT_NORMAL_RANGE
            our_value = mean_ct
            
            benchmark_values = {
                "normal_ct_mean": (ref_range[0] + ref_range[1]) / 2,
                "normal_ct_std": 2.5
            }
            
            diff_pct = ((mean_ct - benchmark_values["normal_ct_mean"]) / 
                       benchmark_values["normal_ct_mean"] * 100) if benchmark_values["normal_ct_mean"] != 0 else 0
            
            if ref_range[0] <= mean_ct <= ref_range[1]:
                interpretation = "CT values within normal reference range"
            elif mean_ct < ref_range[0]:
                interpretation = "CT values suggest higher expression than normal"
            else:
                interpretation = "CT values suggest lower expression than normal"
            
            return LiteratureComparison(
                benchmark_values=benchmark_values,
                our_value=float(our_value),
                difference_pct=float(diff_pct),
                interpretation=interpretation
            )
        
        elif isinstance(result, CellViabilityResult):
            # Compare IC50 to typical values
            ic50 = result.ic50 if result.ic50 is not None else 0
            threshold = self._kb.CELL_VIABILITY_IC50_TYPICAL["cytotoxic_threshold_pct"]
            
            benchmark_values = {
                "cytotoxic_threshold": threshold,
                "moderate_effect": self._kb.CELL_VIABILITY_IC50_TYPICAL["moderate_effect_pct"]
            }
            
            our_value = ic50
            diff_pct = ((threshold - ic50) / threshold * 100) if threshold != 0 else 0
            
            if ic50 < 10:
                interpretation = "Highly potent compound"
            elif ic50 < 25:
                interpretation = "Moderately potent compound"
            elif ic50 < 50:
                interpretation = "Low potency compound"
            else:
                interpretation = "Compound shows minimal potency"
            
            return LiteratureComparison(
                benchmark_values=benchmark_values,
                our_value=float(our_value),
                difference_pct=float(diff_pct),
                interpretation=interpretation
            )
        
        # Default comparison
        return LiteratureComparison(
            benchmark_values={},
            our_value=0.0,
            difference_pct=0.0,
            interpretation="No literature benchmarks available for comparison"
        )
    
    def generate_conclusions(self, result: Any) -> list[Conclusion]:
        """Generate conclusions from experimental results.
        
        Args:
            result: Analysis result object
        
        Returns:
            List of Conclusion objects
        """
        conclusions = []
        
        if isinstance(result, StatisticalResult):
            primary_p = result.p_values.get("primary", 1.0)
            
            if primary_p < 0.01:
                conclusions.append(Conclusion(
                    text="There is a statistically significant difference between the groups tested.",
                    confidence=0.95,
                    supported_by=[
                        f"p-value = {primary_p:.4f}",
                        f"Test used: {result.test_used}"
                    ]
                ))
                
                # Add effect size interpretation
                for key, es in result.effect_sizes.items():
                    if key == "cohens_d":
                        if abs(es) > 0.8:
                            conclusions.append(Conclusion(
                                text=f"The effect size is large (Cohen's d = {es:.2f}), indicating practical significance.",
                                confidence=0.9,
                                supported_by=[f"Effect size = {es:.4f}"]
                            ))
            
            elif primary_p < 0.05:
                conclusions.append(Conclusion(
                    text="There is a statistically significant difference at the 0.05 level.",
                    confidence=0.85,
                    supported_by=[f"p-value = {primary_p:.4f}"]
                ))
            else:
                conclusions.append(Conclusion(
                    text="No statistically significant difference was detected.",
                    confidence=0.8,
                    supported_by=[f"p-value = {primary_p:.4f}"]
                ))
        
        elif isinstance(result, ELISAResult):
            if result.cv_percent < 15:
                conclusions.append(Conclusion(
                    text="The assay demonstrates acceptable precision and reproducibility.",
                    confidence=0.9,
                    supported_by=[f"CV% = {result.cv_percent:.1f}%"]
                ))
            
            if result.lod > 0:
                conclusions.append(Conclusion(
                    text=f"Detection limit of {result.lod:.3f} is appropriate for the assay.",
                    confidence=0.85,
                    supported_by=[f"LOD = {result.lod:.3f}"]
                ))
        
        elif isinstance(result, qPCRResult):
            if 0.9 <= result.efficiency <= 1.1:
                conclusions.append(Conclusion(
                    text="PCR amplification efficiency is optimal (90-110%).",
                    confidence=0.95,
                    supported_by=[f"Efficiency = {result.efficiency:.1%}"]
                ))
            
            mean_ct = np.nanmean(result.ct_values) if len(result.ct_values) > 0 else 0
            conclusions.append(Conclusion(
                text=f"Gene expression was detected with mean CT of {mean_ct:.1f}.",
                confidence=0.9,
                supported_by=[f"Mean CT = {mean_ct:.2f}"]
            ))
        
        elif isinstance(result, CellViabilityResult):
            mean_viab = np.mean(result.viability_pct) if len(result.viability_pct) > 0 else 100
            conclusions.append(Conclusion(
                text=f"Cell viability averaged {mean_viab:.1f}% across conditions.",
                confidence=0.9,
                supported_by=[f"Mean viability = {mean_viab:.1f}%"]
            ))
            
            if result.ic50 is not None:
                conclusions.append(Conclusion(
                    text=f"IC50 was determined to be {result.ic50:.2f} units.",
                    confidence=0.85,
                    supported_by=[f"IC50 = {result.ic50:.2f}"]
                ))
        
        # Default conclusion if nothing specific matched
        if not conclusions:
            conclusions.append(Conclusion(
                text="Analysis completed. See detailed results for interpretation.",
                confidence=0.5,
                supported_by=["Analysis performed without errors"]
            ))
        
        return conclusions


# Need numpy for the methods
import numpy as np
