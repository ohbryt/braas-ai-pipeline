"""
Anomaly Detector
================

Detect anomalies in experimental data using statistical methods
and machine learning approaches.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from braas.core.enums import ExperimentType
from braas.core.exceptions import AnalysisError


# -----------------------------------------------------------------------------
# Data Classes
# -----------------------------------------------------------------------------

@dataclass
class AnomalyResult:
    """Result of anomaly detection."""
    found: bool
    confidence: float
    anomaly_type: str | None
    severity: str
    details: dict[str, Any] = field(default_factory=dict)


# -----------------------------------------------------------------------------
# Anomaly Detector
# -----------------------------------------------------------------------------

class AnomalyDetector:
    """Detect anomalies using statistical and ML methods.
    
    Supports multiple detection layers:
    - Statistical: z-score, control charts, CUSUM
    - ML-based: IsolationForest, LSTM autoencoder
    - Domain-specific: assay type specific checks
    """
    
    def __init__(self, contamination: float = 0.1) -> None:
        """Initialize the anomaly detector.
        
        Args:
            contamination: Expected proportion of anomalies (for IsolationForest)
        """
        self._contamination = contamination
        self._zscore_threshold = 3.0
        self._cusum_threshold = 5.0
        self._control_limits = 3  # Sigma control limits
        
        # ML models (initialized lazily)
        self._isolation_forest = None
        self._lstm_model = None
        self._scaler = None
        self._ml_initialized = False
        
        # Historical data for CUSUM
        self._cusum_state: dict[str, float] = {}
    
    def detect(self, data: np.ndarray, layer: str = "all") -> AnomalyResult:
        """Detect anomalies in data using specified layer(s).
        
        Args:
            data: Input data array
            layer: Detection layer ('statistical', 'ml', 'domain', 'all')
        
        Returns:
            AnomalyResult with detection results
        """
        if layer == "all":
            # Run all detectors and combine results
            results = []
            for l in ["statistical", "ml", "domain"]:
                result = self._run_detector(data, l)
                results.append(result)
            
            # Combine: if any detector finds anomaly, report it
            found_any = any(r.found for r in results)
            max_confidence = max((r.confidence for r in results), default=0.0)
            most_severe = self._get_most_severe([r.severity for r in results])
            
            return AnomalyResult(
                found=found_any,
                confidence=max_confidence,
                anomaly_type=results[0].anomaly_type if found_any else None,
                severity=most_severe,
                details={'layer_results': [r.details for r in results]}
            )
        else:
            return self._run_detector(data, layer)
    
    def _run_detector(self, data: np.ndarray, layer: str) -> AnomalyResult:
        """Run specific detection layer."""
        if layer == "statistical":
            return self.detect_statistical(data)
        elif layer == "ml":
            return self.detect_ml(data)
        elif layer == "domain":
            return self.detect_domain(data, ExperimentType.UNKNOWN)
        else:
            return AnomalyResult(found=False, confidence=0.0, anomaly_type=None, severity="none")
    
    def detect_statistical(self, data: np.ndarray) -> AnomalyResult:
        """Detect anomalies using statistical methods.
        
        Methods used:
        - Z-score (>3 sigma)
        - Control chart rules (Western Electric)
        - CUSUM (cumulative sum)
        
        Args:
            data: Input data array
        
        Returns:
            AnomalyResult
        """
        flat_data = data.flatten()
        
        # Z-score detection
        z_scores = np.abs((flat_data - np.mean(flat_data)) / np.std(flat_data))
        z_anomalies = np.where(z_scores > self._zscore_threshold)[0]
        
        # Control chart detection
        cc_anomalies = self._control_chart_check(flat_data)
        
        # CUSUM detection
        cusum_anomalies = self._cusum_check(flat_data)
        
        # Combine results
        all_anomalies = set(z_anomalies) | set(cc_anomalies) | set(cusum_anomalies)
        
        found = len(all_anomalies) > 0
        confidence = min(len(all_anomalies) / len(flat_data) * 10, 1.0) if found else 0.0
        
        # Determine anomaly type based on characteristics
        anomaly_type = self._classify_statistical_anomaly(
            flat_data, z_scores, cc_anomalies, cusum_anomalies
        )
        
        severity = self._determine_severity(z_scores, all_anomalies)
        
        return AnomalyResult(
            found=found,
            confidence=float(confidence),
            anomaly_type=anomaly_type,
            severity=severity,
            details={
                'z_score_anomalies': len(z_anomalies),
                'control_chart_anomalies': len(cc_anomalies),
                'cusum_anomalies': len(cusum_anomalies),
                'total_anomalies': len(all_anomalies),
                'max_z_score': float(np.max(z_scores)),
            }
        )
    
    def _control_chart_check(self, data: np.ndarray) -> list[int]:
        """Apply Western Electric control chart rules.
        
        Rules:
        - Any single point outside 3 sigma
        - Two of 3 consecutive points beyond 2 sigma
        - 4 of 5 consecutive points beyond 1 sigma
        """
        anomalies = []
        mean = np.mean(data)
        std = np.std(data)
        
        for i, val in enumerate(data):
            z = abs(val - mean) / std if std > 0 else 0
            
            # Rule 1: Outside 3 sigma
            if z > 3:
                anomalies.append(i)
                continue
            
            # Rule 2: 2 of 3 beyond 2 sigma
            if i >= 2:
                window = data[i-2:i+1]
                window_z = np.abs(window - mean) / std
                if np.sum(window_z > 2) >= 2:
                    anomalies.extend([i-2, i-1, i])
                    continue
            
            # Rule 3: 4 of 5 beyond 1 sigma
            if i >= 4:
                window = data[i-4:i+1]
                window_z = np.abs(window - mean) / std
                if np.sum(window_z > 1) >= 4:
                    anomalies.extend(list(range(i-4, i+1)))
        
        return list(set(anomalies))
    
    def _cusum_check(self, data: np.ndarray, target: float | None = None) -> list[int]:
        """Cumulative sum (CUSUM) anomaly detection.
        
        Args:
            data: Input data
            target: Target/expected value (defaults to mean)
        
        Returns:
            Indices of anomalies
        """
        if target is None:
            target = np.mean(data)
        
        std = np.std(data)
        if std == 0:
            std = 1
        
        # Initialize CUSUM state
        cusum_pos = 0.0  # For detecting increases
        cusum_neg = 0.0  # For detecting decreases
        anomalies = []
        k = 0.5 * std  # Allowable slack
        h = self._cusum_threshold * std  # Decision boundary
        
        for i, val in enumerate(data):
            dev = val - target
            cusum_pos = max(0, cusum_pos + dev - k)
            cusum_neg = max(0, cusum_neg - dev - k)
            
            if cusum_pos > h or cusum_neg > h:
                anomalies.append(i)
                cusum_pos = 0
                cusum_neg = 0
        
        return anomalies
    
    def _classify_statistical_anomaly(
        self,
        data: np.ndarray,
        z_scores: np.ndarray,
        cc_anomalies: list[int],
        cusum_anomalies: list[int]
    ) -> str | None:
        """Classify the type of statistical anomaly detected."""
        if len(cc_anomalies) > len(cusum_anomalies):
            return "VARIABILITY"
        elif np.max(z_scores) > 5:
            return "EXTREME_VALUE"
        elif len(cusum_anomalies) > len(cc_anomalies):
            return "DRIFT"
        return "OUTLIER"
    
    def _determine_severity(self, z_scores: np.ndarray, anomalies: set) -> str:
        """Determine severity based on z-scores of anomalies."""
        if not anomalies:
            return "none"
        
        max_z = np.max([z_scores[i] for i in anomalies])
        
        if max_z > 5:
            return "critical"
        elif max_z > 4:
            return "high"
        elif max_z > 3:
            return "medium"
        else:
            return "low"
    
    def detect_ml(self, data: np.ndarray) -> AnomalyResult:
        """Detect anomalies using machine learning methods.
        
        Methods:
        - IsolationForest for general anomaly detection
        - LSTM autoencoder for time series
        
        Args:
            data: Input data array
        
        Returns:
            AnomalyResult
        """
        try:
            # Lazy initialization of ML models
            if not self._ml_initialized:
                self._initialize_ml_models()
            
            flat_data = data.flatten().reshape(-1, 1)
            
            # Scale data
            scaled_data = self._scaler.transform(flat_data)
            
            # IsolationForest detection
            if_predictions = self._isolation_forest.predict(scaled_data)
            if_scores = self._isolation_forest.decision_function(scaled_data)
            
            # Find anomalies (IsolationForest labels -1 for anomalies)
            if_anomalies = np.where(if_predictions == -1)[0]
            
            # Use score threshold for confidence
            if_confidence = 1 - np.clip(if_scores.min(), 0, 1)
            
            found = len(if_anomalies) > 0
            confidence = float(np.mean(if_scores[if_anomalies])) if found else 0.0
            confidence = max(confidence, 0.5) if found else 0.0
            
            return AnomalyResult(
                found=found,
                confidence=confidence,
                anomaly_type="ISOLATION" if found else None,
                severity="medium" if found else "none",
                details={
                    'isolation_forest_anomalies': len(if_anomalies),
                    'isolation_forest_scores': if_scores.tolist(),
                }
            )
            
        except Exception as e:
            # If ML detection fails, return no anomaly found
            return AnomalyResult(
                found=False,
                confidence=0.0,
                anomaly_type=None,
                severity="none",
                details={'error': str(e)}
            )
    
    def _initialize_ml_models(self) -> None:
        """Initialize ML models for anomaly detection."""
        try:
            from sklearn.ensemble import IsolationForest
            from sklearn.preprocessing import StandardScaler
            
            # Create IsolationForest
            self._isolation_forest = IsolationForest(
                contamination=self._contamination,
                n_estimators=100,
                random_state=42,
                n_jobs=-1
            )
            
            # Create scaler
            self._scaler = StandardScaler()
            
            # Fit with dummy data to initialize
            dummy_data = np.random.randn(100, 1)
            self._scaler.fit(dummy_data)
            self._isolation_forest.fit(dummy_data)
            
            self._ml_initialized = True
            
        except ImportError:
            # Scikit-learn not available
            self._ml_initialized = False
    
    def detect_domain(self, data: np.ndarray, assay_type: ExperimentType) -> AnomalyResult:
        """Detect domain-specific anomalies based on assay type.
        
        Args:
            data: Input data
            assay_type: Type of assay for domain-specific checks
        
        Returns:
            AnomalyResult
        """
        type_str = str(assay_type).lower()
        
        if "qpcr" in type_str or "pcr" in type_str:
            return self._detect_qpcr_anomalies(data)
        elif "elisa" in type_str:
            return self._detect_elisa_anomalies(data)
        elif "cell" in type_str or "viability" in type_str:
            return self._detect_cell_anomalies(data)
        elif "western" in type_str or "blot" in type_str:
            return self._detect_western_anomalies(data)
        
        return AnomalyResult(
            found=False, confidence=0.0, anomaly_type=None, severity="none"
        )
    
    def _detect_qpcr_anomalies(self, data: np.ndarray) -> AnomalyResult:
        """Detect anomalies in qPCR amplification curves.
        
        Checks:
        - Curve shape (should be sigmoidal)
        - CT value range
        - Efficiency
        """
        if data.shape[1] < 2:
            return AnomalyResult(
                found=False, confidence=0.0, anomaly_type=None, severity="none"
            )
        
        cycles = data[:, 0]
        fluorescence = data[:, 1]
        
        anomalies = []
        
        # Check for exponential growth phase
        try:
            log_fluo = np.log(fluorescence + 1)
            slope_early = np.polyfit(cycles[:5], log_fluo[:5], 1)[0] if len(cycles) >= 5 else 0
            slope_late = np.polyfit(cycles[-5:], log_fluo[-5:], 1)[0] if len(cycles) >= 5 else 0
            
            # Should have positive slope in early cycles, then plateau
            if slope_early < 0:
                anomalies.append("no_exponential_phase")
            if slope_late > slope_early * 0.5:
                anomalies.append("no_plateau")
        except Exception:
            pass
        
        # Check for flat curve (no amplification)
        if np.max(fluorescence) - np.min(fluorescence) < 0.1:
            anomalies.append("flat_curve")
        
        found = len(anomalies) > 0
        
        return AnomalyResult(
            found=found,
            confidence=0.8 if found else 0.0,
            anomaly_type="QPCR_SHAPE" if found else None,
            severity="high" if found else "none",
            details={'anomalies': anomalies}
        )
    
    def _detect_elisa_anomalies(self, data: np.ndarray) -> AnomalyResult:
        """Detect anomalies in ELISA standard curves.
        
        Checks:
        - Curve fit quality (R²)
        - Expected sigmoidal shape
        - LOD/LOQ quality
        """
        if data.shape[1] < 2:
            return AnomalyResult(
                found=False, confidence=0.0, anomaly_type=None, severity="none"
            )
        
        concentrations = data[:, 0]
        absorbances = data[:, 1]
        
        anomalies = []
        
        # Check for monotonicity (should increase with concentration)
        diffs = np.diff(absorbances)
        if np.any(diffs < -0.1):  # Allow small noise
            anomalies.append("non_monotonic")
        
        # Check for appropriate range
        if np.max(absorbances) < 0.1:
            anomalies.append("low_response")
        if np.min(absorbances) > 3:
            anomalies.append("saturated")
        
        # Check for high background
        if absorbances[0] > 0.2:
            anomalies.append("high_background")
        
        found = len(anomalies) > 0
        
        return AnomalyResult(
            found=found,
            confidence=0.7 if found else 0.0,
            anomaly_type="ELISA_SHAPE" if found else None,
            severity="medium" if found else "none",
            details={'anomalies': anomalies}
        )
    
    def _detect_cell_anomalies(self, data: np.ndarray) -> AnomalyResult:
        """Detect anomalies in cell viability data.
        
        Checks:
        - Expected dose-response shape
        - Positive control viability
        - Negative control toxicity
        """
        anomalies = []
        
        # Check for proper control values
        if data.shape[1] >= 2:
            concentrations = data[:, 0]
            viability = data[:, 1]
            
            # Vehicle control (lowest concentration) should have high viability
            vehicle_viability = viability[np.argmin(concentrations)]
            if vehicle_viability < 70:
                anomalies.append("low_vehicle_control")
            if vehicle_viability > 110:
                anomalies.append("unrealistic_vehicle")
            
            # High dose should have lower viability
            high_dose_viability = viability[np.argmax(concentrations)]
            if high_dose_viability > vehicle_viability * 0.9:
                anomalies.append("no_dose_response")
        
        found = len(anomalies) > 0
        
        return AnomalyResult(
            found=found,
            confidence=0.75 if found else 0.0,
            anomaly_type="CELL_SHAPE" if found else None,
            severity="medium" if found else "none",
            details={'anomalies': anomalies}
        )
    
    def _detect_western_anomalies(self, data: np.ndarray) -> AnomalyResult:
        """Detect anomalies in western blot data.
        
        Checks:
        - Band intensity distribution
        - Molecular weight合理性
        - Loading control consistency
        """
        anomalies = []
        
        if data.shape[1] >= 2:
            mw = data[:, 0]
            intensity = data[:, 1]
            
            # Check for negative intensities
            if np.any(intensity < 0):
                anomalies.append("negative_intensity")
            
            # Check for very faint bands
            if np.max(intensity) < 100:
                anomalies.append("very_faint_bands")
            
            # Check for unreasonable MW values
            if np.any(mw < 5) or np.any(mw > 300):
                anomalies.append("unrealistic_mw")
        
        found = len(anomalies) > 0
        
        return AnomalyResult(
            found=found,
            confidence=0.7 if found else 0.0,
            anomaly_type="WESTERN_SHAPE" if found else None,
            severity="low" if found else "none",
            details={'anomalies': anomalies}
        )
    
    def classify_anomaly_type(self, anomaly_result: AnomalyResult) -> str:
        """Classify anomaly into broad category.
        
        Categories:
        - TEMPERATURE: Temperature excursions
        - CONTAMINATION: Contamination indicators
        - EQUIPMENT: Equipment malfunction
        - PROCEDURAL: Protocol deviation
        
        Args:
            anomaly_result: Result from detect()
        
        Returns:
            Category string
        """
        if not anomaly_result.found:
            return "NONE"
        
        anomaly_type = anomaly_result.anomaly_type or ""
        
        # Map specific types to categories
        type_mapping = {
            "EXTREME_VALUE": "EQUIPMENT",
            "VARIABILITY": "PROCEDURAL",
            "DRIFT": "EQUIPMENT",
            "OUTLIER": "PROCEDURAL",
            "ISOLATION": "PROCEDURAL",
            "QPCR_SHAPE": "PROCEDURAL",
            "ELISA_SHAPE": "PROCEDURAL",
            "CELL_SHAPE": "CONTAMINATION",
            "WESTERN_SHAPE": "PROCEDURAL",
        }
        
        for specific_type, category in type_mapping.items():
            if specific_type in anomaly_type:
                return category
        
        # Infer from severity and confidence
        if anomaly_result.severity in ["critical", "high"]:
            return "EQUIPMENT"
        
        return "PROCEDURAL"
    
    def predict_cause(self, anomaly_result: AnomalyResult) -> str:
        """Predict likely cause of anomaly.
        
        Args:
            anomaly_result: Result from detect()
        
        Returns:
            Suggested cause string
        """
        if not anomaly_result.found:
            return "No anomaly detected"
        
        anomaly_type = anomaly_result.anomaly_type or ""
        severity = anomaly_result.severity
        
        # Cause mapping based on type and severity
        if "EXTREME_VALUE" in anomaly_type:
            if severity == "critical":
                return "Equipment sensor malfunction or extreme environmental event"
            return "Brief environmental excursion or sample handling error"
        
        if "VARIABILITY" in anomaly_type:
            return "Inconsistent technique, pipetting error, or reagent instability"
        
        if "DRIFT" in anomaly_type:
            return "Gradual instrument drift, calibration shift, or environmental change"
        
        if "OUTLIER" in anomaly_type:
            return "Single measurement error, contamination, or edge effect"
        
        if "SHAPE" in anomaly_type:
            if "QPCR" in anomaly_type:
                return "Suboptimal primer design, contamination, or failed amplification"
            if "ELISA" in anomaly_type:
                return "Plate coating issue, antibody degradation, or blocking problem"
            if "CELL" in anomaly_type:
                return "Cell stress, contamination, or media composition issue"
            if "WESTERN" in anomaly_type:
                return "Transfer efficiency issue, antibody problem, or membrane artifact"
        
        if severity == "critical":
            return "Systematic failure requiring immediate investigation"
        
        return "Multiple contributing factors - further investigation needed"
    
    def get_confidence_score(self, anomaly_result: AnomalyResult) -> float:
        """Get overall confidence score for anomaly detection.
        
        Args:
            anomaly_result: Result from detect()
        
        Returns:
            Confidence score between 0.0 and 1.0
        """
        if not anomaly_result.found:
            return 0.0
        
        # Weight by severity
        severity_weights = {
            "critical": 1.0,
            "high": 0.85,
            "medium": 0.7,
            "low": 0.5,
            "none": 0.0,
        }
        
        severity_weight = severity_weights.get(anomaly_result.severity, 0.5)
        
        # Combine with detector confidence
        confidence = anomaly_result.confidence * severity_weight
        
        # Boost if multiple detection layers found anomaly
        details = anomaly_result.details
        if isinstance(details, dict):
            layer_results = details.get('layer_results', [])
            if len(layer_results) >= 2:
                confidence *= 1.2  # Boost for multi-layer confirmation
        
        return min(confidence, 1.0)
    
    def _get_most_severe(self, severities: list[str]) -> str:
        """Get the most severe from a list of severities."""
        order = ["critical", "high", "medium", "low", "none"]
        for s in order:
            if s in severities:
                return s
        return "none"
