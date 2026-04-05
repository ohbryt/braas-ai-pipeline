"""
Digital Twin Simulator for BRaaS Pipeline
==========================================

Simulates experimental outcomes before physical execution:
- ELISA absorbance simulation using 4PL model
- qPCR Ct value and amplification curves
- Cell culture confluence over time
- Western blot band intensities
- Success probability estimation
"""

from dataclasses import dataclass
from typing import Any

import numpy as np

from braas.core.enums import ExperimentType
from braas.core.models import Experiment, Protocol, ProtocolStep


@dataclass
class PredictedOutcome:
    """Predicted experimental outcome from digital twin simulation."""
    raw_data: dict[str, float]
    signal_range: tuple[float, float]
    confidence: float  # 0-1


@dataclass
class SimulationStep:
    """A single step in the simulated experimental timeline."""
    time_min: float
    event: str
    duration_min: float
    expected_value: float


class DigitalTwinSimulator:
    """Digital twin simulator for predicting experiment outcomes.
    
    Uses mathematical models to simulate various experiment types:
    - 4PL model for ELISA
    - Exponential PCR amplification model
    - Logistic growth for cell culture
    """
    
    def __init__(self, random_seed: int | None = None):
        """Initialize simulator with optional random seed for reproducibility."""
        self._random_seed = random_seed
        if random_seed is not None:
            np.random.seed(random_seed)
    
    def simulate_elisa(self, params: dict[str, Any]) -> dict[str, float]:
        """Simulate ELISA absorbance values using 4PL model.
        
        4PL Model: y = d + (a-d)/(1+(x/c)^b)
        Where:
        - a: minimum asymptote (blank)
        - b: Hill slope
        - c: inflection point (EC50)
        - d: maximum asymptote (positive control)
        - x: analyte concentration
        - y: absorbance
        
        Args:
            params: Dict with keys:
                - concentrations: list of concentrations per well
                - plate_layout: dict mapping well -> concentration index
                - a: min asymptote (default 0.0)
                - b: Hill slope (default 1.0)
                - c: EC50 (default 1.0)
                - d: max asymptote (default 3.0)
                - noise_level: relative noise (default 0.05)
                
        Returns:
            Dict mapping well -> absorbance value
        """
        concentrations = params.get("concentrations", [0, 0.1, 0.5, 1.0, 5.0, 10.0, 50.0, 100.0])
        plate_layout = params.get("plate_layout", {})
        noise_level = params.get("noise_level", 0.05)
        
        # 4PL parameters
        a = params.get("a", 0.0)  # min asymptote
        b = params.get("b", 1.0)   # Hill slope
        c = params.get("c", 1.0)   # EC50
        d = params.get("d", 3.0)   # max asymptote
        
        results = {}
        
        for well, conc_idx in plate_layout.items():
            x = concentrations[conc_idx] if conc_idx < len(concentrations) else 0
            
            # 4PL equation
            if x > 0:
                y = d + (a - d) / (1 + (x / c) ** b)
            else:
                y = a  # blank
            
            # Add Gaussian noise
            noise = np.random.normal(0, noise_level * (d - a))
            y_noisy = max(0, y + noise)
            
            results[well] = round(y_noisy, 4)
        
        return results
    
    def simulate_qpcr(self, params: dict[str, Any]) -> dict[str, Any]:
        """Simulate qPCR Ct values and amplification curves.
        
        Exponential PCR model: N = N0 * 2^n
        Where:
        - N0: initial template amount
        - n: number of cycles
        - N: final amount after n cycles
        
        Args:
            params: Dict with keys:
                - targets: dict mapping sample -> initial copies
                - cycles: number of PCR cycles (default 40)
                - efficiency: PCR efficiency 0-1 (default 0.95)
                - threshold: fluorescence threshold (default 0.1)
                
        Returns:
            Dict with 'ct_values': dict sample -> Ct, 
                   'amplification_curves': dict sample -> list of fluorescence values
        """
        targets = params.get("targets", {"sample_1": 1000, "sample_2": 500})
        cycles = params.get("cycles", 40)
        efficiency = params.get("efficiency", 0.95)
        threshold = params.get("threshold", 0.1)
        
        ct_values = {}
        amplification_curves = {}
        
        for sample, n0 in targets.items():
            curve = []
            
            # Simulate amplification curve
            for cycle in range(1, cycles + 1):
                # N = N0 * (1 + efficiency)^cycle
                n = n0 * (1 + efficiency) ** cycle
                
                # Fluorescence proportional to log of amount (simplified)
                fluorescence = np.log10(max(1, n)) if n > 1 else 0
                
                # Add noise
                noise = np.random.normal(0, 0.05)
                fluorescence = max(0, fluorescence + noise)
                
                curve.append(round(fluorescence, 4))
            
            amplification_curves[sample] = curve
            
            # Find Ct (cycle at which fluorescence exceeds threshold)
            ct = None
            for i, fluo in enumerate(curve):
                if fluo >= threshold:
                    # Interpolate for more accurate Ct
                    if i > 0:
                        prev = curve[i - 1]
                        frac = (threshold - prev) / (fluo - prev) if fluo != prev else 0
                        ct = i + frac
                    else:
                        ct = i + 1
                    break
            
            if ct is None:
                ct = cycles  # No detection
            
            ct_values[sample] = round(ct, 2)
        
        return {
            "ct_values": ct_values,
            "amplification_curves": amplification_curves
        }
    
    def simulate_cell_culture(self, params: dict[str, Any]) -> dict[str, list[float]]:
        """Simulate cell culture confluence over time using logistic growth.
        
        Logistic growth model: P(t) = K / (1 + ((K - P0) / P0) * e^(-r*t))
        Where:
        - P0: initial cell count/density
        - K: carrying capacity (max density)
        - r: growth rate
        - t: time
        
        Args:
            params: Dict with keys:
                - initial_confluence: starting confluence % (default 20)
                - max_confluence: carrying capacity % (default 100)
                - growth_rate: growth rate constant (default 0.03)
                - time_points: list of time points in hours
                - seeding_density: initial cell density (default 0.2)
                
        Returns:
            Dict mapping 'confluence' -> list of confluence % per time point
        """
        time_points = params.get("time_points", [0, 4, 8, 12, 24, 48, 72, 96])
        initial_confluence = params.get("initial_confluence", 20.0)
        max_confluence = params.get("max_confluence", 100.0)
        growth_rate = params.get("growth_rate", 0.03)
        seeding_density = params.get("seeding_density", 0.2)
        
        # Convert to logistic model parameters
        p0 = initial_confluence / 100.0
        k = max_confluence / 100.0
        
        confluence_values = []
        
        for t in time_points:
            # Logistic growth equation
            if p0 > 0 and k > p0:
                p_t = k / (1 + ((k - p0) / p0) * np.exp(-growth_rate * t))
            else:
                p_t = k  # Already at capacity
            
            # Add some noise to simulate experimental variation
            noise = np.random.normal(0, 0.02)
            p_t = max(0, min(1, p_t + noise))
            
            confluence_values.append(round(p_t * 100, 2))
        
        return {"confluence": confluence_values, "time_points": time_points}
    
    def simulate_western_blot(self, params: dict[str, Any]) -> dict[str, float]:
        """Simulate western blot band intensities.
        
        Args:
            params: Dict with keys:
                - targets: dict mapping lane -> protein identifier
                - expected_bands: dict mapping protein -> expected intensity
                - background_noise: background noise level (default 0.1)
                - lane_load_factor: variation in loading (default 0.1)
                
        Returns:
            Dict mapping lane -> band intensity
        """
        targets = params.get("targets", {
            "lane_1": "GAPDH",
            "lane_2": "Target_Protein",
            "lane_3": "Target_Protein",
            "lane_4": "beta_actin"
        })
        expected_bands = params.get("expected_bands", {
            "GAPDH": 0.8,
            "Target_Protein": 0.6,
            "beta_actin": 0.9
        })
        background_noise = params.get("background_noise", 0.1)
        lane_load_factor = params.get("lane_load_factor", 0.1)
        
        results = {}
        
        for lane, protein in targets.items():
            expected = expected_bands.get(protein, 0.5)
            
            # Add loading variation
            load_variation = np.random.normal(1.0, lane_load_factor)
            intensity = expected * load_variation
            
            # Add background noise
            noise = np.random.normal(0, background_noise)
            intensity = max(0, intensity + noise)
            
            results[lane] = round(intensity, 4)
        
        return results
    
    def predict_outcome(self, experiment: Experiment) -> PredictedOutcome:
        """Predict experimental outcome based on experiment definition.
        
        Args:
            experiment: The experiment to predict
            
        Returns:
            PredictedOutcome with simulated data and confidence
        """
        protocol = experiment.protocol
        if not protocol:
            return PredictedOutcome(
                raw_data={},
                signal_range=(0, 0),
                confidence=0.0
            )
        
        exp_type = protocol.experiment_type
        
        if exp_type == ExperimentType.ELISA:
            params = self._build_elisa_params(experiment)
            raw_data = self.simulate_elisa(params)
            signal_range = (min(raw_data.values()), max(raw_data.values()))
            confidence = 0.85
            
        elif exp_type == ExperimentType.QPCR:
            params = self._build_qpcr_params(experiment)
            result = self.simulate_qpcr(params)
            raw_data = result["ct_values"]
            signal_range = (min(raw_data.values()), max(raw_data.values()))
            confidence = 0.80
            
        elif exp_type == ExperimentType.CELL_CULTURE:
            params = self._build_cell_culture_params(experiment)
            result = self.simulate_cell_culture(params)
            raw_data = {"confluence": result["confluence"]}
            signal_range = (min(result["confluence"]), max(result["confluence"]))
            confidence = 0.75
            
        elif exp_type == ExperimentType.WESTERN_BLOT:
            params = self._build_western_blot_params(experiment)
            raw_data = self.simulate_western_blot(params)
            signal_range = (min(raw_data.values()), max(raw_data.values()))
            confidence = 0.70
            
        else:
            raw_data = {}
            signal_range = (0, 0)
            confidence = 0.5
        
        return PredictedOutcome(
            raw_data=raw_data,
            signal_range=signal_range,
            confidence=confidence
        )
    
    def estimate_success_probability(self, experiment: Experiment) -> float:
        """Estimate probability that experiment will succeed.
        
        Based on protocol completeness, reagent availability signals,
        and historical success rates.
        
        Args:
            experiment: The experiment to evaluate
            
        Returns:
            Probability of success between 0 and 1
        """
        if not experiment.protocol:
            return 0.0
        
        # Base probability
        prob = 0.5
        
        # Protocol completeness factor
        if experiment.protocol.steps:
            prob += 0.1
        if experiment.protocol.required_equipment:
            prob += 0.05
        
        # Sample/reagent availability
        if experiment.samples:
            prob += 0.1
        if experiment.reagents:
            prob += 0.1
        
        # Protocol with checkpoints
        has_checkpoints = any(s.checkpoint for s in experiment.protocol.steps)
        if has_checkpoints:
            prob += 0.05
        
        # Safety level appropriate
        if experiment.safety_level:
            prob += 0.05
        
        # Cap at 0.95
        return min(0.95, prob)
    
    def simulate_timeline(self, protocol: Protocol) -> list[SimulationStep]:
        """Generate simulated timeline of protocol execution.
        
        Args:
            protocol: The protocol to simulate
            
        Returns:
            List of SimulationStep objects representing expected timeline
        """
        if not protocol:
            return []
        
        timeline = []
        current_time = 0.0
        
        for step in protocol.steps:
            duration_min = step.duration_seconds / 60.0
            
            # Determine expected value based on step type
            expected_value = self._estimate_step_value(step)
            
            timeline.append(SimulationStep(
                time_min=current_time,
                event=step.name,
                duration_min=duration_min,
                expected_value=expected_value
            ))
            
            current_time += duration_min
        
        return timeline
    
    def _build_elisa_params(self, experiment: Experiment) -> dict[str, Any]:
        """Build ELISA simulation parameters from experiment."""
        protocol = experiment.protocol
        params = {
            "concentrations": [0, 0.1, 0.5, 1.0, 5.0, 10.0, 50.0, 100.0],
            "plate_layout": {},
            "noise_level": 0.05
        }
        
        # Build plate layout from samples
        well_idx = 0
        for row in 'ABCDEFGH':
            for col in range(1, 13):
                if well_idx < len(experiment.samples):
                    params["plate_layout"][f"{row}{col}"] = well_idx % 8
                    well_idx += 1
        
        # Extract any protocol-specific parameters
        for step in protocol.steps:
            if 'concentrations' in step.parameters:
                params['concentrations'] = step.parameters['concentrations']
            if 'noise_level' in step.parameters:
                params['noise_level'] = step.parameters['noise_level']
        
        return params
    
    def _build_qpcr_params(self, experiment: Experiment) -> dict[str, Any]:
        """Build qPCR simulation parameters from experiment."""
        params = {
            "targets": {},
            "cycles": 40,
            "efficiency": 0.95,
            "threshold": 0.1
        }
        
        # Build targets from samples
        for i, sample in enumerate(experiment.samples[:8]):
            n0 = 1000 / (2 ** i)  # Serial dilution
            params["targets"][f"sample_{i+1}"] = n0
        
        return params
    
    def _build_cell_culture_params(self, experiment: Experiment) -> dict[str, Any]:
        """Build cell culture simulation parameters from experiment."""
        params = {
            "time_points": [0, 4, 8, 12, 24, 48, 72, 96],
            "initial_confluence": 20.0,
            "growth_rate": 0.03
        }
        
        # Extract parameters from protocol
        protocol = experiment.protocol
        if protocol:
            for step in protocol.steps:
                if 'initial_confluence' in step.parameters:
                    params['initial_confluence'] = step.parameters['initial_confluence']
                if 'growth_rate' in step.parameters:
                    params['growth_rate'] = step.parameters['growth_rate']
        
        return params
    
    def _build_western_blot_params(self, experiment: Experiment) -> dict[str, Any]:
        """Build western blot simulation parameters from experiment."""
        params = {
            "targets": {},
            "expected_bands": {},
            "background_noise": 0.1
        }
        
        # Build lane layout
        lanes = ['lane_1', 'lane_2', 'lane_3', 'lane_4', 'lane_5', 'lane_6']
        proteins = ['GAPDH', 'Target_Protein', 'Target_Protein', 
                    'beta_actin', 'Target_Protein', 'GAPDH']
        
        for lane, protein in zip(lanes, proteins):
            params["targets"][lane] = protein
        
        return params
    
    def _estimate_step_value(self, step: ProtocolStep) -> float:
        """Estimate expected value for a protocol step."""
        step_name = step.name.lower()
        
        if 'incubat' in step_name:
            return step.temperature_celsius or 37.0
        elif 'wash' in step_name:
            return 1.0
        elif 'centrifug' in step_name:
            return step.parameters.get('speed_rpm', 1000)
        elif 'aspirat' in step_name or 'dispense' in step_name:
            return step.parameters.get('volume_ul', 100)
        else:
            return 1.0
