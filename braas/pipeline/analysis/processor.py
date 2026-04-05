"""
Data Analysis Processor
=======================

Core data analysis engine for processing and analyzing experimental data
from various assay types including ELISA, qPCR, cell viability, and western blot.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
from scipy.optimize import curve_fit
from scipy import stats

from braas.core.enums import ExperimentType
from braas.core.exceptions import AnalysisError


# -----------------------------------------------------------------------------
# Data Classes for Analysis Results
# -----------------------------------------------------------------------------


@dataclass
class ProcessedData:
    """Preprocessed experimental data."""
    cleaned_data: np.ndarray
    normalization_applied: str | None
    outliers_removed: list[int]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ELISAResult:
    """ELISA assay analysis results."""
    std_curve_params: dict[str, float]
    concentrations: np.ndarray
    lod: float
    loq: float
    cv_percent: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class qPCRResult:
    """qPCR assay analysis results."""
    ct_values: np.ndarray
    relative_quantification: np.ndarray
    melt_temps: np.ndarray | None
    efficiency: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CellViabilityResult:
    """Cell viability assay analysis results."""
    viability_pct: np.ndarray
    ic50: float | None
    ec50: float | None
    growth_rates: np.ndarray | None
    synergy_scores: dict[str, float] | None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class WesternBlotResult:
    """Western blot analysis results."""
    band_intensities: np.ndarray
    molecular_weights: np.ndarray
    relative_quantification: np.ndarray
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class StatisticalResult:
    """Statistical test results."""
    test_used: str
    p_values: dict[str, float]
    effect_sizes: dict[str, float]
    corrections_applied: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)


# -----------------------------------------------------------------------------
# 4PL (Four-Parameter Logistic) Fitting
# -----------------------------------------------------------------------------


def four_param_logistic(x: np.ndarray, a: float, b: float, c: float, d: float) -> np.ndarray:
    """Four-parameter logistic function for ELISA standard curves.
    
    Args:
        x: Concentration values
        a: Minimum asymptote (bottom)
        b: Hill slope
        c: Inflection point (EC50)
        d: Maximum asymptote (top)
    
    Returns:
        Expected absorbance values
    """
    return d + (a - d) / (1 + (x / c) ** b)


def calculate_lod_loq(
    std_residuals: np.ndarray,
    slope: float,
    blank_std: float
) -> tuple[float, float]:
    """Calculate limit of detection and limit of quantification.
    
    LOD = 3.3 * (sigma / slope)
    LOQ = 10 * (sigma / slope)
    """
    sigma = np.std(std_residuals)
    lod = 3.3 * (sigma / slope) if slope != 0 else 0.0
    loq = 10 * (sigma / slope) if slope != 0 else 0.0
    return lod, loq


# -----------------------------------------------------------------------------
# Data Analysis Engine
# -----------------------------------------------------------------------------


class DataAnalysisEngine:
    """Main data analysis engine for BRaaS pipeline.
    
    Provides methods for preprocessing, analyzing, and performing statistical
    tests on data from various assay types.
    """
    
    def __init__(self) -> None:
        """Initialize the data analysis engine."""
        self._normalization_methods = ["zscore", "minmax", "log2", "percentile"]
        self._outlier_z_threshold = 3.0
    
    def preprocess(
        self,
        raw_data: np.ndarray,
        experiment_type: ExperimentType | str
    ) -> ProcessedData:
        """Preprocess raw experimental data.
        
        Args:
            raw_data: Raw data array (2D for plate data, 1D for other)
            experiment_type: Type of experiment
        
        Returns:
            ProcessedData with cleaned data, normalization info, outliers
        
        Raises:
            AnalysisError: If preprocessing fails
        """
        try:
            # Handle 2D plate data (ELISA, etc.)
            if len(raw_data.shape) == 2:
                cleaned = self._preprocess_plate_data(raw_data)
            else:
                cleaned = raw_data.copy()
            
            # Remove outliers using z-score method
            outliers = self._detect_outliers(cleaned)
            cleaned = self._remove_outliers(cleaned, outliers)
            
            # Apply normalization based on experiment type
            norm_method = self._select_normalization(experiment_type)
            if norm_method:
                cleaned = self._apply_normalization(cleaned, norm_method)
            else:
                norm_method = None
            
            return ProcessedData(
                cleaned_data=cleaned,
                normalization_applied=norm_method,
                outliers_removed=outliers.tolist() if len(outliers) > 0 else [],
                metadata={"experiment_type": str(experiment_type)}
            )
            
        except Exception as e:
            raise AnalysisError(
                message=f"Preprocessing failed: {str(e)}",
                analysis_type="preprocessing",
                details={"experiment_type": str(experiment_type)}
            )
    
    def _preprocess_plate_data(self, plate_data: np.ndarray) -> np.ndarray:
        """Preprocess 2D plate data (background subtraction, drift correction)."""
        # Simple background subtraction using border wells
        if plate_data.shape[0] >= 3 and plate_data.shape[1] >= 3:
            border_mean = np.mean([
                np.mean(plate_data[0, :]),
                np.mean(plate_data[-1, :]),
                np.mean(plate_data[:, 0]),
                np.mean(plate_data[:, -1])
            ])
            corrected = plate_data - border_mean
            return np.clip(corrected, 0, None)  # Remove negative values
        return plate_data.copy()
    
    def _detect_outliers(self, data: np.ndarray) -> np.ndarray:
        """Detect outliers using z-score method."""
        z_scores = np.abs(stats.zscore(data.flatten()))
        outlier_indices = np.where(z_scores > self._outlier_z_threshold)[0]
        return outlier_indices
    
    def _remove_outliers(self, data: np.ndarray, outliers: np.ndarray) -> np.ndarray:
        """Remove outlier values by replacing with median."""
        flat_data = data.flatten().copy()
        for idx in outliers:
            if idx < len(flat_data):
                flat_data[idx] = np.median(flat_data)
        return flat_data.reshape(data.shape)
    
    def _select_normalization(self, experiment_type: ExperimentType | str) -> str | None:
        """Select appropriate normalization method based on experiment type."""
        type_str = str(experiment_type).lower()
        if "elisa" in type_str:
            return "zscore"
        elif "qpcr" in type_str or "pcr" in type_str:
            return "log2"
        elif "viability" in type_str or "cell" in type_str:
            return "percentile"
        return None
    
    def _apply_normalization(self, data: np.ndarray, method: str) -> np.ndarray:
        """Apply selected normalization method."""
        flat = data.flatten().astype(float)
        
        if method == "zscore":
            mean, std = np.mean(flat), np.std(flat)
            if std > 0:
                return (flat - mean) / std
        elif method == "minmax":
            min_val, max_val = np.min(flat), np.max(flat)
            if max_val > min_val:
                return (flat - min_val) / (max_val - min_val)
        elif method == "log2":
            return np.log2(flat + 1)  # Add 1 to avoid log(0)
        elif method == "percentile":
            p5, p95 = np.percentile(flat, [5, 95])
            return np.clip(flat, p5, p95)
        
        return flat.reshape(data.shape)
    
    def analyze_elisa(self, plate_data: np.ndarray) -> ELISAResult:
        """Analyze ELISA plate data with standard curve fitting.
        
        Args:
            plate_data: 2D array of absorbance values
        
        Returns:
            ELISAResult with concentrations, LOD, LOQ, CV%
        
        Raises:
            AnalysisError: If analysis fails
        """
        try:
            # Extract standard curve data (assuming first rows/columns are standards)
            # This is a simplified implementation
            std_curve = self._extract_standard_curve(plate_data)
            
            if std_curve is None or len(std_curve) < 4:
                raise AnalysisError(
                    message="Insufficient standard curve points",
                    analysis_type="elisa"
                )
            
            concentrations = std_curve["concentrations"]
            absorbances = std_curve["absorbances"]
            
            # Fit 4PL model
            try:
                popt, pcov = curve_fit(
                    four_param_logistic,
                    concentrations,
                    absorbances,
                    p0=[0, 1, np.median(concentrations), np.max(absorbances)],
                    maxfev=5000
                )
            except Exception:
                # Fallback to linear fit if 4PL fails
                popt = np.polyfit(concentrations, absorbances, 2)
                std_curve_params = {
                    "a": 0, "b": popt[0], "c": popt[1], "d": popt[2],
                    "fit_type": "quadratic"
                }
            else:
                std_curve_params = {
                    "a": float(popt[0]),
                    "b": float(popt[1]),
                    "c": float(popt[2]),
                    "d": float(popt[3]),
                    "fit_type": "4pl"
                }
            
            # Calculate sample concentrations
            sample_mask = std_curve.get("sample_mask", None)
            if sample_mask is not None:
                sample_absorbances = plate_data[sample_mask].flatten()
                concentrations = self._interpolate_concentrations(
                    sample_absorbances, concentrations, absorbances
                )
            else:
                concentrations = np.array([])
            
            # Calculate LOD/LOQ
            residuals = absorbances - four_param_logistic(concentrations, *popt)
            lod, loq = calculate_lod_loq(residuals, popt[1] if len(popt) > 1 else 1, np.std(absorbances))
            
            # Calculate CV% for quality control
            cv_percent = self._calculate_cv(plate_data)
            
            return ELISAResult(
                std_curve_params=std_curve_params,
                concentrations=concentrations,
                lod=float(lod),
                loq=float(loq),
                cv_percent=float(cv_percent)
            )
            
        except AnalysisError:
            raise
        except Exception as e:
            raise AnalysisError(
                message=f"ELISA analysis failed: {str(e)}",
                analysis_type="elisa"
            )
    
    def _extract_standard_curve(self, plate_data: np.ndarray) -> dict[str, Any] | None:
        """Extract standard curve data from plate. Override based on actual layout."""
        # Default: assume top 2 rows are standards, rest are samples
        if plate_data.shape[0] < 2:
            return None
        
        std_rows = plate_data[:2, :].flatten()
        sample_mask = np.zeros(plate_data.shape, dtype=bool)
        sample_mask[2:, :] = True
        
        # Standard concentrations (typically 2-fold dilutions)
        num_std = len(std_rows)
        concentrations = np.array([100.0 / (2 ** i) for i in range(num_std)])
        
        return {
            "concentrations": concentrations,
            "absorbances": std_rows,
            "sample_mask": sample_mask
        }
    
    def _interpolate_concentrations(
        self,
        absorbances: np.ndarray,
        std_conc: np.ndarray,
        std_abs: np.ndarray
    ) -> np.ndarray:
        """Interpolate sample concentrations from standard curve."""
        # Sort standards by concentration
        sort_idx = np.argsort(std_conc)
        sorted_conc = std_conc[sort_idx]
        sorted_abs = std_abs[sort_idx]
        
        concentrations = np.interp(absorbances, sorted_abs, sorted_conc)
        return concentrations
    
    def _calculate_cv(self, plate_data: np.ndarray) -> float:
        """Calculate coefficient of variation for replicate wells."""
        # Assume replicates are in columns
        if plate_data.shape[1] < 2:
            return 0.0
        
        means = np.mean(plate_data, axis=1)
        stds = np.std(plate_data, axis=1)
        
        # CV% = (std/mean) * 100
        cv_values = np.where(means > 0, (stds / means) * 100, 0)
        return float(np.mean(cv_values))
    
    def analyze_qpcr(self, amplification_data: np.ndarray) -> qPCRResult:
        """Analyze qPCR amplification data.
        
        Args:
            amplification_data: Array with columns [cycle, fluorescence, ...]
        
        Returns:
            qPCRResult with CT values, relative quantification, efficiency
        """
        try:
            # Extract amplification curves
            cycles = amplification_data[:, 0]
            fluorescence = amplification_data[:, 1]
            
            # Calculate CT values using threshold method
            threshold = self._calculate_threshold(fluorescence)
            ct_values = self._calculate_ct_values(cycles, fluorescence, threshold)
            
            # Relative quantification (delta-delta CT method)
            if len(ct_values) >= 2:
                reference_ct = np.min(ct_values)
                delta_ct = ct_values - reference_ct
                relative_quant = 2 ** (-delta_ct)
            else:
                relative_quant = np.array([1.0])
            
            # Calculate efficiency from log-linear phase
            efficiency = self._calculate_pcr_efficiency(cycles, fluorescence)
            
            # Melt temps if provided (assuming data format supports it)
            melt_temps = None
            
            return qPCRResult(
                ct_values=ct_values,
                relative_quantification=relative_quant,
                melt_temps=melt_temps,
                efficiency=float(efficiency)
            )
            
        except Exception as e:
            raise AnalysisError(
                message=f"qPCR analysis failed: {str(e)}",
                analysis_type="qpcr"
            )
    
    def _calculate_threshold(self, fluorescence: np.ndarray) -> float:
        """Calculate threshold for CT determination (typically 10x background)."""
        background = np.mean(fluorescence[:5])  # Early cycles as background
        threshold = background * 10
        return threshold
    
    def _calculate_ct_values(
        self,
        cycles: np.ndarray,
        fluorescence: np.ndarray,
        threshold: float
    ) -> np.ndarray:
        """Calculate CT values (cycle at which fluorescence exceeds threshold)."""
        ct_values = np.zeros(len(fluorescence)) if fluorescence.ndim > 1 else np.zeros(1)
        
        if fluorescence.ndim > 1:
            for i in range(fluorescence.shape[1]):
                trace = fluorescence[:, i]
                idx = np.where(trace >= threshold)[0]
                if len(idx) > 0:
                    ct_values[i] = cycles[idx[0]]
                else:
                    ct_values[i] = np.nan
        else:
            idx = np.where(fluorescence >= threshold)[0]
            ct_values[0] = cycles[idx[0]] if len(idx) > 0 else np.nan
        
        return ct_values
    
    def _calculate_pcr_efficiency(self, cycles: np.ndarray, fluorescence: np.ndarray) -> float:
        """Calculate PCR efficiency from log-linear phase."""
        # Simplified: use a window in exponential phase
        # In practice, would fit log(fluorescence) vs cycles in linear region
        try:
            log_fluo = np.log(fluorescence + 1)
            # Simple linear fit
            slope = np.polyfit(cycles, log_fluo, 1)[0]
            efficiency = (10 ** slope) - 1
            return float(np.clip(efficiency, 0.5, 2.0))  # Reasonable range
        except Exception:
            return 1.0  # Default 100% efficiency
    
    def analyze_cell_viability(self, cell_data: np.ndarray) -> CellViabilityResult:
        """Analyze cell viability assay data (MTS, WST, etc.).
        
        Args:
            cell_data: Array with [concentration, viability_signal, ...]
        
        Returns:
            CellViabilityResult with viability %, IC50, EC50, growth rates
        """
        try:
            concentrations = cell_data[:, 0]
            viability_signal = cell_data[:, 1]
            
            # Calculate viability as percentage of vehicle control
            vehicle_idx = np.argmin(concentrations)
            vehicle_signal = viability_signal[vehicle_idx]
            viability_pct = (viability_signal / vehicle_signal) * 100
            
            # Fit dose-response curve to find IC50/EC50
            ic50, ec50 = self._fit_dose_response(concentrations, viability_pct)
            
            # Calculate growth rates if time-course data available
            growth_rates = None
            if cell_data.shape[1] > 2:
                growth_rates = self._calculate_growth_rates(cell_data)
            
            # Synergy scores (placeholder - would require combination data)
            synergy_scores = None
            
            return CellViabilityResult(
                viability_pct=viability_pct,
                ic50=ic50,
                ec50=ec50,
                growth_rates=growth_rates,
                synergy_scores=synergy_scores
            )
            
        except Exception as e:
            raise AnalysisError(
                message=f"Cell viability analysis failed: {str(e)}",
                analysis_type="cell_viability"
            )
    
    def _fit_dose_response(
        self,
        concentrations: np.ndarray,
        viability: np.ndarray
    ) -> tuple[float | None, float | None]:
        """Fit dose-response curve to find IC50/EC50."""
        try:
            # Use 4PL model for dose-response
            popt, _ = curve_fit(
                four_param_logistic,
                concentrations,
                viability,
                p0=[100, 1, np.median(concentrations), 0],
                bounds=([0, 0, 0, 0], [100, 10, 1e6, 100]),
                maxfev=5000
            )
            ic50 = float(popt[2])  # Inflection point is IC50
            return ic50, ic50
        except Exception:
            return None, None
    
    def _calculate_growth_rates(self, cell_data: np.ndarray) -> np.ndarray | None:
        """Calculate growth rates from time-course viability data."""
        if cell_data.shape[1] < 3:
            return None
        
        # Simplified: calculate rate of change between timepoints
        time_col = 2
        growth_rates = np.diff(cell_data[:, time_col]) / np.diff(cell_data[:, 0])
        return growth_rates
    
    def analyze_western_blot(self, band_data: np.ndarray) -> WesternBlotResult:
        """Analyze western blot band intensity data.
        
        Args:
            band_data: Array with [molecular_weight, intensity, ...]
        
        Returns:
            WesternBlotResult with band intensities and relative quantification
        """
        try:
            molecular_weights = band_data[:, 0]
            intensities = band_data[:, 1]
            
            # Normalize to loading control (housekeeping protein)
            if band_data.shape[1] > 2:
                loading_control = band_data[:, 2]
                # Use first band as reference if no specific control indicated
                ref_intensity = loading_control[0] if loading_control[0] > 0 else 1
                normalized = intensities / ref_intensity
            else:
                # Normalize to total signal
                total = np.sum(intensities)
                normalized = intensities / total if total > 0 else intensities
            
            relative_quant = normalized * 100
            
            return WesternBlotResult(
                band_intensities=intensities,
                molecular_weights=molecular_weights,
                relative_quantification=relative_quant
            )
            
        except Exception as e:
            raise AnalysisError(
                message=f"Western blot analysis failed: {str(e)}",
                analysis_type="western_blot"
            )
    
    def run_statistical_tests(
        self,
        data: np.ndarray,
        groups: list[int]
    ) -> StatisticalResult:
        """Run statistical tests on grouped data.
        
        Args:
            data: Array of values to compare
            groups: Group assignments for each data point
        
        Returns:
            StatisticalResult with test used, p-values, effect sizes
        """
        try:
            unique_groups = np.unique(groups)
            
            if len(unique_groups) < 2:
                return StatisticalResult(
                    test_used="none",
                    p_values={},
                    effect_sizes={},
                    corrections_applied={}
                )
            
            # Prepare grouped data
            grouped_data = [
                data[np.array(groups) == g]
                for g in unique_groups
            ]
            
            # Shapiro-Wilk test for normality
            normality_results = {}
            for i, group in enumerate(grouped_data):
                if len(group) >= 3:
                    stat, p = stats.shapiro(group)
                    normality_results[f"group_{i}"] = {"statistic": stat, "p_value": p}
            
            # Select appropriate test
            all_normal = all(
                r["p_value"] > 0.05 for r in normality_results.values()
            ) if normality_results else False
            
            p_values = {}
            effect_sizes = {}
            
            if all_normal and len(unique_groups) == 2:
                # Parametric: t-test
                stat, p = stats.ttest_ind(grouped_data[0], grouped_data[1])
                test_used = "t-test"
                p_values["primary"] = float(p)
                
                # Cohen's d effect size
                mean_diff = np.mean(grouped_data[0]) - np.mean(grouped_data[1])
                pooled_std = np.sqrt(
                    (np.var(grouped_data[0]) + np.var(grouped_data[1])) / 2
                )
                effect_sizes["cohens_d"] = float(mean_diff / pooled_std) if pooled_std > 0 else 0
                
            elif all_normal and len(unique_groups) > 2:
                # One-way ANOVA
                stat, p = stats.f_oneway(*grouped_data)
                test_used = "one-way ANOVA"
                p_values["primary"] = float(p)
                
                # Eta-squared effect size
                ss_between = sum(
                    len(g) * (np.mean(g) - np.mean(data)) ** 2
                    for g in grouped_data
                )
                ss_total = np.sum((data - np.mean(data)) ** 2)
                effect_sizes["eta_squared"] = float(ss_between / ss_total) if ss_total > 0 else 0
                
            else:
                # Non-parametric: Mann-Whitney or Kruskal-Wallis
                if len(unique_groups) == 2:
                    stat, p = stats.mannwhitneyu(grouped_data[0], grouped_data[1])
                    test_used = "Mann-Whitney U"
                else:
                    stat, p = stats.kruskal(*grouped_data)
                    test_used = "Kruskal-Wallis"
                
                p_values["primary"] = float(p)
                effect_sizes["rank_biserial"] = float(stat / (len(data) * (len(data) - 1) / 2))
            
            # Multiple testing correction (Bonferroni)
            n_tests = len(p_values)
            corrections = {}
            if n_tests > 1:
                for key, p_val in p_values.items():
                    corrected = min(p_val * n_tests, 1.0)
                    corrections[f"{key}_bonferroni"] = corrected
                corrections["method"] = "Bonferroni"
            
            return StatisticalResult(
                test_used=test_used,
                p_values=p_values,
                effect_sizes=effect_sizes,
                corrections_applied=corrections
            )
            
        except Exception as e:
            raise AnalysisError(
                message=f"Statistical testing failed: {str(e)}",
                analysis_type="statistics"
            )
    
    def auto_detect_assay_type(self, data: np.ndarray) -> ExperimentType:
        """Auto-detect experiment type from data characteristics.
        
        Args:
            data: Raw data array to classify
        
        Returns:
            Detected ExperimentType
        """
        # Heuristic-based detection
        shape = data.shape
        value_range = np.ptp(data)  # Peak-to-peak
        mean_val = np.mean(data)
        
        # ELISA typically has 2D plate format with moderate values
        if len(shape) == 2 and shape[0] >= 8 and shape[1] >= 12:
            if 0 <= mean_val <= 4 and value_range < 4:
                return ExperimentType.ELISA
        
        # qPCR has amplification curves with exponential growth
        if len(shape) == 2 and shape[1] >= 2:
            if self._has_exponential_growth(data[:, 1] if shape[1] > 1 else data.flatten()):
                return ExperimentType.QPCR
        
        # Cell viability has dose-response format
        if len(shape) == 2 and shape[1] >= 2:
            if self._has_dose_response(data):
                return ExperimentType.CELL_CULTURE
        
        # Western blot has molecular weights
        if len(shape) == 2 and shape[1] >= 2:
            if 10 < np.max(data[:, 0]) < 250:  # MW in kDa range
                return ExperimentType.WESTERN_BLOT
        
        return ExperimentType.UNKNOWN
    
    def _has_exponential_growth(self, values: np.ndarray) -> bool:
        """Check if values show exponential growth pattern."""
        if len(values) < 10:
            return False
        
        # Check log-linear region
        try:
            log_vals = np.log(values + 1)
            slopes = np.diff(log_vals)
            # Exponential growth has positive, increasing slopes
            return np.mean(slopes[-5:]) > np.mean(slopes[:5])
        except Exception:
            return False
    
    def _has_dose_response(self, data: np.ndarray) -> bool:
        """Check if data follows dose-response pattern."""
        if data.shape[1] < 2:
            return False
        
        conc = data[:, 0]
        response = data[:, 1]
        
        # Sort by concentration
        sort_idx = np.argsort(conc)
        sorted_response = response[sort_idx]
        
        # Dose-response typically saturates at high conc
        early_mean = np.mean(sorted_response[:3])
        late_mean = np.mean(sorted_response[-3:])
        
        # Sigmoidal: high at low conc (agonist) or low at low conc (antagonist)
        return abs(early_mean - late_mean) > 0.2 * np.ptp(sorted_response)
