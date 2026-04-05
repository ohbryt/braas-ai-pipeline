"""
Feasibility Checker for BRaaS Pipeline
========================================

Validates experiment feasibility before execution:
- Reagent availability and inventory checks
- Equipment availability and status
- Protocol timing validation
- Volume calculations
- Sample type compatibility
"""

from dataclasses import dataclass
from typing import Any

from braas.core.enums import SampleType, ValidationStatus
from braas.core.models import Experiment, Protocol, Reagent, Sample


@dataclass
class FeasibilityIssue:
    """A single feasibility issue found during validation."""
    code: str
    severity: str  # CRITICAL or WARNING
    message: str
    field: str


@dataclass
class FeasibilityReport:
    """Complete feasibility validation report."""
    status: ValidationStatus
    issues: list[FeasibilityIssue]


class FeasibilityChecker:
    """Validates that an experiment can be feasibly executed.
    
    Performs pre-flight checks on reagents, equipment, timing,
    volumes, and sample types before experiment execution.
    """
    
    def __init__(self):
        self._issue_count = 0
    
    def check_reagents(
        self, protocol: Protocol, inventory: dict[str, Any]
    ) -> list[FeasibilityIssue]:
        """Check if required reagents are available in inventory.
        
        Args:
            protocol: The experimental protocol
            inventory: Dict mapping reagent names to available quantities
            
        Returns:
            List of feasibility issues for reagent problems
        """
        issues = []
        
        if not protocol:
            return issues
        
        # Extract required reagents from protocol parameters
        required_reagents = self._extract_required_reagents(protocol)
        
        for reagent_name, required_amount in required_reagents.items():
            if reagent_name not in inventory:
                self._issue_count += 1
                issues.append(FeasibilityIssue(
                    code=f"REAGENT_MISSING_{self._issue_count}",
                    severity="CRITICAL",
                    message=f"Required reagent '{reagent_name}' not found in inventory",
                    field="reagents"
                ))
            else:
                available = inventory.get(reagent_name, 0)
                if available < required_amount:
                    self._issue_count += 1
                    issues.append(FeasibilityIssue(
                        code=f"REAGENT_INSUFFICIENT_{self._issue_count}",
                        severity="CRITICAL",
                        message=f"Insufficient '{reagent_name}': need {required_amount}, have {available}",
                        field="reagents"
                    ))
        
        return issues
    
    def check_equipment(
        self, protocol: Protocol, equipment_status: dict[str, Any]
    ) -> list[FeasibilityIssue]:
        """Check if required equipment is available and operational.
        
        Args:
            protocol: The experimental protocol
            equipment_status: Dict mapping equipment types to status dicts
            
        Returns:
            List of feasibility issues for equipment problems
        """
        issues = []
        
        if not protocol:
            return issues
        
        required_equipment = protocol.required_equipment or []
        
        for equip_type in required_equipment:
            equip_key = str(equip_type.value) if hasattr(equip_type, 'value') else str(equip_type)
            
            if equip_key not in equipment_status:
                self._issue_count += 1
                issues.append(FeasibilityIssue(
                    code=f"EQ_UNAVAILABLE_{self._issue_count}",
                    severity="CRITICAL",
                    message=f"Equipment type '{equip_key}' not available",
                    field="equipment"
                ))
            else:
                status = equipment_status[equip_key]
                if not status.get("available", False):
                    self._issue_count += 1
                    issues.append(FeasibilityIssue(
                        code=f"EQ_IN_USE_{self._issue_count}",
                        severity="WARNING",
                        message=f"Equipment '{equip_key}' currently in use",
                        field="equipment"
                    ))
                if not status.get("operational", True):
                    self._issue_count += 1
                    issues.append(FeasibilityIssue(
                        code=f"EQ_BROKEN_{self._issue_count}",
                        severity="CRITICAL",
                        message=f"Equipment '{equip_key}' not operational: {status.get('reason', 'unknown')}",
                        field="equipment"
                    ))
        
        return issues
    
    def check_timing(self, protocol: Protocol) -> list[FeasibilityIssue]:
        """Validate protocol timing constraints.
        
        Args:
            protocol: The experimental protocol
            
        Returns:
            List of feasibility issues for timing problems
        """
        issues = []
        
        if not protocol:
            return issues
        
        total_duration = protocol.estimated_duration_seconds or 0
        
        # Check for extremely long protocols (>24 hours)
        if total_duration > 86400:  # 24 hours in seconds
            self._issue_count += 1
            issues.append(FeasibilityIssue(
                code=f"TIME_EXCEEDS_24H_{self._issue_count}",
                severity="WARNING",
                message=f"Protocol duration ({total_duration/3600:.1f}h) exceeds 24 hours",
                field="timing"
            ))
        
        # Check for zero or negative durations
        if total_duration <= 0:
            self._issue_count += 1
            issues.append(FeasibilityIssue(
                code=f"TIME_INVALID_{self._issue_count}",
                severity="CRITICAL",
                message="Protocol has no defined duration",
                field="timing"
            ))
        
        # Check individual step durations
        for step in protocol.steps or []:
            if step.duration_seconds <= 0:
                self._issue_count += 1
                issues.append(FeasibilityIssue(
                    code=f"STEP_TIME_INVALID_{self._issue_count}",
                    severity="CRITICAL",
                    message=f"Step '{step.name}' has invalid duration",
                    field="timing"
                ))
            
            # Check for temperature requirements that seem wrong
            if step.temperature_celsius is not None:
                if step.temperature_celsius < -200 or step.temperature_celsius > 200:
                    self._issue_count += 1
                    issues.append(FeasibilityIssue(
                        code=f"TEMP_UNREALISTIC_{self._issue_count}",
                        severity="WARNING",
                        message=f"Step '{step.name}' has unrealistic temperature: {step.temperature_celsius}°C",
                        field="timing"
                    ))
        
        return issues
    
    def check_volumes(self, protocol: Protocol) -> list[FeasibilityIssue]:
        """Validate reagent and sample volumes.
        
        Args:
            protocol: The experimental protocol
            
        Returns:
            List of feasibility issues for volume problems
        """
        issues = []
        
        if not protocol:
            return issues
        
        for step in protocol.steps or []:
            params = step.parameters or {}
            
            # Check for volume-related parameters
            volume_keys = ['volume_ul', 'volume_ml', 'aspirate_volume', 'dispense_volume']
            
            for key in volume_keys:
                if key in params:
                    volume = params[key]
                    try:
                        vol = float(volume)
                        if vol <= 0:
                            self._issue_count += 1
                            issues.append(FeasibilityIssue(
                                code=f"VOL_INVALID_{self._issue_count}",
                                severity="CRITICAL",
                                message=f"Step '{step.name}' has invalid {key}: {vol}",
                                field="volumes"
                            ))
                        elif vol > 10000:
                            self._issue_count += 1
                            issues.append(FeasibilityIssue(
                                code=f"VOL_EXCEEDS_MAX_{self._issue_count}",
                                severity="WARNING",
                                message=f"Step '{step.name}' has unusually large {key}: {vol}µL",
                                field="volumes"
                            ))
                    except (TypeError, ValueError):
                        self._issue_count += 1
                        issues.append(FeasibilityIssue(
                            code=f"VOL_TYPE_ERROR_{self._issue_count}",
                            severity="CRITICAL",
                            message=f"Step '{step.name}' has non-numeric {key}",
                            field="volumes"
                        ))
            
            # Check for dilution factors
            if 'dilution_factor' in params:
                df = params['dilution_factor']
                try:
                    dilution = float(df)
                    if dilution <= 0 or dilution > 10000:
                        self._issue_count += 1
                        issues.append(FeasibilityIssue(
                            code=f"DILUTION_UNUSUAL_{self._issue_count}",
                            severity="WARNING",
                            message=f"Step '{step.name}' has unusual dilution factor: {dilution}",
                            field="volumes"
                        ))
                except (TypeError, ValueError):
                    pass
            
            # Check for sample input volumes
            if 'input_volume_ul' in params:
                iv = float(params['input_volume_ul'])
                if iv > 500:
                    self._issue_count += 1
                    issues.append(FeasibilityIssue(
                        code=f"INPUT_VOL_LARGE_{self._issue_count}",
                        severity="WARNING",
                        message=f"Step '{step.name}' input volume {iv}µL exceeds typical limit",
                        field="volumes"
                    ))
        
        return issues
    
    def check_sample_type(self, protocol: Protocol) -> list[FeasibilityIssue]:
        """Validate sample type compatibility with protocol.
        
        Args:
            protocol: The experimental protocol
            
        Returns:
            List of feasibility issues for sample type problems
        """
        issues = []
        
        if not protocol:
            return issues
        
        experiment_type = protocol.experiment_type
        
        # Define compatible sample types for each experiment type
        compatibility_map = {
            "elisa": [SampleType.SERUM, SampleType.PLASMA, SampleType.CELL_LYSATE, 
                      SampleType.SUPERNATANT, SampleType.UNKNOWN],
            "qpcr": [SampleType.DNA, SampleType.RNA, SampleType.CELL_LYSATE, 
                     SampleType.TISSUE, SampleType.UNKNOWN],
            "western_blot": [SampleType.PROTEIN, SampleType.CELL_LYSATE, 
                             SampleType.TISSUE, SampleType.UNKNOWN],
            "cell_culture": [SampleType.CELL_SUSPENSION, SampleType.TISSUE, 
                             SampleType.UNKNOWN],
            "flow_cytometry": [SampleType.CELL_SUSPENSION, SampleType.WHOLE_BLOOD, 
                               SampleType.SUPERNATANT, SampleType.UNKNOWN],
            "immunofluorescence": [SampleType.TISSUE, SampleType.CELL_SUSPENSION, 
                                   SampleType.UNKNOWN],
            "mass_spectrometry": [SampleType.PROTEIN, SampleType.PEPTIDE, 
                                  SampleType.CELL_LYSATE, SampleType.UNKNOWN],
            "rna_seq": [SampleType.RNA, SampleType.TISSUE, SampleType.CELL_LYSATE, 
                        SampleType.UNKNOWN],
            "crispr": [SampleType.DNA, SampleType.CELL_SUSPENSION, SampleType.UNKNOWN],
            "cloning": [SampleType.DNA, SampleType.CELL_LYSATE, SampleType.UNKNOWN],
            "protein_purification": [SampleType.CELL_LYSATE, SampleType.SUPERNATANT, 
                                      SampleType.UNKNOWN],
        }
        
        exp_type_value = experiment_type.value if hasattr(experiment_type, 'value') else str(experiment_type)
        compatible_types = compatibility_map.get(exp_type_value, [SampleType.UNKNOWN])
        
        # Check if protocol has sample type requirements
        if hasattr(protocol, 'parameters') and protocol.parameters:
            required_sample_type = protocol.parameters.get('required_sample_type')
            if required_sample_type:
                req_type = SampleType(required_sample_type) if isinstance(required_sample_type, str) else required_sample_type
                if req_type not in compatible_types:
                    self._issue_count += 1
                    issues.append(FeasibilityIssue(
                        code=f"SAMPLE_INCOMPAT_{self._issue_count}",
                        severity="CRITICAL",
                        message=f"Sample type '{req_type.value}' may not be compatible with {exp_type_value}",
                        field="sample_type"
                    ))
        
        return issues
    
    def check_all(self, experiment: Experiment) -> FeasibilityReport:
        """Run all feasibility checks on an experiment.
        
        Args:
            experiment: The experiment to validate
            
        Returns:
            FeasibilityReport with overall status and all issues found
        """
        issues = []
        
        protocol = experiment.protocol
        if not protocol:
            issues.append(FeasibilityIssue(
                code="NO_PROTOCOL",
                severity="CRITICAL",
                message="Experiment has no protocol defined",
                field="protocol"
            ))
            return FeasibilityReport(
                status=ValidationStatus.FAIL,
                issues=issues
            )
        
        # Run all checks - use empty dicts as defaults if not provided
        inventory = getattr(experiment, 'inventory', {})
        equipment_status = getattr(experiment, 'equipment_status', {})
        
        issues.extend(self.check_reagents(protocol, inventory))
        issues.extend(self.check_equipment(protocol, equipment_status))
        issues.extend(self.check_timing(protocol))
        issues.extend(self.check_volumes(protocol))
        issues.extend(self.check_sample_type(protocol))
        
        # Determine overall status
        has_critical = any(i.severity == "CRITICAL" for i in issues)
        
        if has_critical:
            status = ValidationStatus.FAIL
        elif issues:
            status = ValidationStatus.WARN
        else:
            status = ValidationStatus.PASS
        
        return FeasibilityReport(status=status, issues=issues)
    
    def _extract_required_reagents(self, protocol: Protocol) -> dict[str, float]:
        """Extract required reagents and amounts from protocol."""
        reagents = {}
        
        for step in protocol.steps or []:
            params = step.parameters or {}
            
            # Look for reagent-related parameters
            if 'reagents' in params:
                for reagent_name, amount in params['reagents'].items():
                    reagents[reagent_name] = reagents.get(reagent_name, 0) + float(amount)
            
            if 'reagent_list' in params:
                for item in params['reagent_list']:
                    if isinstance(item, dict):
                        name = item.get('name', '')
                        amount = item.get('amount', item.get('volume_ul', 0))
                        reagents[name] = reagents.get(name, 0) + float(amount)
            
            # Check standard volume parameters as proxy for reagent usage
            for vol_key in ['volume_ul', 'reagent_volume_ul']:
                if vol_key in params:
                    # Use step name as reagent identifier if not specified
                    reagents[f"reagent_{step.name}"] = reagents.get(f"reagent_{step.name}", 0) + float(params[vol_key])
        
        return reagents
