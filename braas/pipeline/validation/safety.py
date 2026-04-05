"""
Safety Checker for BRaaS Pipeline
===================================

Validates experiment safety before execution:
- Hazard identification and assessment
- BSL requirement verification
- Chemical incompatibility checks
- PPE and waste disposal requirements
"""

from dataclasses import dataclass, field
from typing import Any

from braas.core.enums import SafetyLevel, ValidationStatus
from braas.core.models import Experiment, Protocol, Reagent, Sample


@dataclass
class HazardInfo:
    """Hazard information for a reagent."""
    bsl_level: SafetyLevel
    hazards: list[str]
    incompatibilities: list[str]
    ppe_requirements: list[str]
    waste_disposal: str


@dataclass
class SafetyIssue:
    """A safety issue found during validation."""
    reagent: str
    issue_type: str
    description: str
    severity: str  # CRITICAL, WARNING, INFO


@dataclass
class SafetyReport:
    """Complete safety validation report."""
    status: ValidationStatus
    hazards: list[str]
    ppe: list[str]
    waste_methods: list[str]
    emergency_protocols: list[str]


class SafetyChecker:
    """Validates safety compliance for experiments.
    
    Performs hazard analysis, BSL verification, incompatibility
    checks, and generates comprehensive safety reports.
    """
    
    # Class-level hazard database
    HazardDatabase: dict[str, HazardInfo] = {
        "ethanol": HazardInfo(
            bsl_level=SafetyLevel.BSL1,
            hazards=["flammable"],
            incompatibilities=["strong_oxidizers", "acids"],
            ppe_requirements=["safety_glasses", "gloves", "lab_coat"],
            waste_disposal="hazardous_wasteorganic"
        ),
        "tris": HazardInfo(
            bsl_level=SafetyLevel.BSL1,
            hazards=["irritant"],
            incompatibilities=["strong_acids", "strong_bases"],
            ppe_requirements=["safety_glasses", "gloves"],
            waste_disposal="aqueous_waste"
        ),
        "dmso": HazardInfo(
            bsl_level=SafetyLevel.BSL1,
            hazards=["flammable", "irritant"],
            incompatibilities=["strong_acids", "strong_oxidizers"],
            ppe_requirements=["safety_glasses", "gloves", "lab_coat", "fume_hood"],
            waste_disposal="hazardous_wasteorganic"
        ),
        "paraformaldehyde": HazardInfo(
            bsl_level=SafetyLevel.BSL2,
            hazards=["toxic", "carcinogen"],
            incompatibilities=["amines", "ammonia"],
            ppe_requirements=["safety_glasses", "gloves", "lab_coat", "fume_hood", "respirator"],
            waste_disposal="formaldehyde_waste"
        ),
        "propidium_iodide": HazardInfo(
            bsl_level=SafetyLevel.BSL2,
            hazards=["toxic", "carcinogen"],
            incompatibilities=["strong_oxidizers"],
            ppe_requirements=["safety_glasses", "gloves", "lab_coat"],
            waste_disposal="hazardous_wasteorganic"
        ),
        "acrylamide": HazardInfo(
            bsl_level=SafetyLevel.BSL1,
            hazards=["toxic", "carcinogen"],
            incompatibilities=["strong_acids", "strong_bases", "strong_oxidizers"],
            ppe_requirements=["safety_glasses", "gloves", "lab_coat"],
            waste_disposal="acrylamide_waste"
        ),
        "beta_mercaptoethanol": HazardInfo(
            bsl_level=SafetyLevel.BSL1,
            hazards=["toxic", "irritant"],
            incompatibilities=["acids", "oxidizers", "bases"],
            ppe_requirements=["safety_glasses", "gloves", "lab_coat", "fume_hood"],
            waste_disposal="organosulfur_waste"
        ),
        "lipofectamine": HazardInfo(
            bsl_level=SafetyLevel.BSL1,
            hazards=["irritant"],
            incompatibilities=["strong_acids", "strong_bases"],
            ppe_requirements=["safety_glasses", "gloves"],
            waste_disposal="aqueous_waste"
        ),
        "penicillin_streptomycin": HazardInfo(
            bsl_level=SafetyLevel.BSL1,
            hazards=["toxic"],
            incompatibilities=["strong_acids", "strong_bases"],
            ppe_requirements=["safety_glasses", "gloves"],
            waste_disposal="biohazard_waste"
        ),
        "fetal_bovine_serum": HazardInfo(
            bsl_level=SafetyLevel.BSL1,
            hazards=["biohazard"],
            incompatibilities=[],
            ppe_requirements=["safety_glasses", "gloves", "lab_coat"],
            waste_disposal="biohazard_waste"
        ),
        "triton_x_100": HazardInfo(
            bsl_level=SafetyLevel.BSL1,
            hazards=["irritant"],
            incompatibilities=["strong_acids", "strong_bases", "oxidizers"],
            ppe_requirements=["safety_glasses", "gloves"],
            waste_disposal="aqueous_waste"
        ),
        "sds": HazardInfo(
            bsl_level=SafetyLevel.BSL1,
            hazards=["irritant"],
            incompatibilities=["strong_acids", "strong_bases", "oxidizers"],
            ppe_requirements=["safety_glasses", "gloves", "lab_coat"],
            waste_disposal="aqueous_waste"
        ),
        "lod": HazardInfo(
            bsl_level=SafetyLevel.BSL2,
            hazards=["biohazard"],
            incompatibilities=["disinfectants", "alcohol"],
            ppe_requirements=["safety_glasses", "gloves", "lab_coat", "face_shield"],
            waste_disposal="biohazard_waste"
        ),
        "chloroform": HazardInfo(
            bsl_level=SafetyLevel.BSL1,
            hazards=["toxic", "carcinogen"],
            incompatibilities=["strong_bases", "amines", "acetone"],
            ppe_requirements=["safety_glasses", "gloves", "lab_coat", "fume_hood"],
            waste_disposal="halogenated_waste"
        ),
        "phenol": HazardInfo(
            bsl_level=SafetyLevel.BSL1,
            hazards=["toxic", "corrosive", "carcinogen"],
            incompatibilities=["strong_oxidizers", "bases"],
            ppe_requirements=["safety_glasses", "gloves", "lab_coat", "fume_hood"],
            waste_disposal="phenolic_waste"
        ),
    }
    
    # Default hazard info for unknown reagents
    _default_hazard = HazardInfo(
        bsl_level=SafetyLevel.BSL1,
        hazards=["unknown"],
        incompatibilities=[],
        ppe_requirements=["safety_glasses", "gloves", "lab_coat"],
        waste_disposal="standard_waste"
    )
    
    def __init__(self):
        self._custom_hazards: dict[str, HazardInfo] = {}
    
    def check_hazards(self, protocol: Protocol) -> list[SafetyIssue]:
        """Identify and assess hazards for all reagents in protocol.
        
        Args:
            protocol: The experimental protocol
            
        Returns:
            List of safety issues related to hazards
        """
        issues = []
        
        if not protocol:
            return issues
        
        reagents = self._extract_reagents(protocol)
        
        for reagent_name in reagents:
            hazard_info = self._get_hazard_info(reagent_name)
            
            # Check for high-hazard reagents
            high_hazard_categories = {"toxic", "carcinogen", "mutagen", "biohazard"}
            
            for hazard in hazard_info.hazards:
                if hazard in high_hazard_categories:
                    issues.append(SafetyIssue(
                        reagent=reagent_name,
                        issue_type="hazard",
                        description=f"Reagent '{reagent_name}' is classified as {hazard}",
                        severity="WARNING"
                    ))
            
            # Check for BSL2+ requirements
            if hazard_info.bsl_level in [SafetyLevel.BSL3, SafetyLevel.BSL4]:
                issues.append(SafetyIssue(
                    reagent=reagent_name,
                    issue_type="bsl_requirement",
                    description=f"Reagent '{reagent_name}' requires BSL {hazard_info.bsl_level.value}",
                    severity="CRITICAL"
                ))
        
        return issues
    
    def check_bsl_requirements(self, sample_type: Any) -> SafetyLevel:
        """Determine required BSL for a given sample type.
        
        Args:
            sample_type: The type of biological sample
            
        Returns:
            Required biosafety level
        """
        if sample_type is None:
            return SafetyLevel.BSL1
        
        # Convert to string value for comparison
        if hasattr(sample_type, 'value'):
            type_value = sample_type.value
        else:
            type_value = str(sample_type)
        
        # BSL requirements based on sample type
        bsl_map = {
            "serum": SafetyLevel.BSL1,
            "plasma": SafetyLevel.BSL1,
            "whole_blood": SafetyLevel.BSL2,
            "tissue": SafetyLevel.BSL2,
            "cell_lysate": SafetyLevel.BSL2,
            "cell_suspension": SafetyLevel.BSL2,
            "rna": SafetyLevel.BSL1,
            "dna": SafetyLevel.BSL1,
            "protein": SafetyLevel.BSL1,
            "supernatant": SafetyLevel.BSL2,
            "urine": SafetyLevel.BSL1,
            "csf": SafetyLevel.BSL2,
        }
        
        return bsl_map.get(type_value, SafetyLevel.BSL1)
    
    def check_incompatibilities(self, protocol: Protocol) -> list[SafetyIssue]:
        """Check for chemical incompatibilities between reagents.
        
        Args:
            protocol: The experimental protocol
            
        Returns:
            List of safety issues for incompatible reagents
        """
        issues = []
        
        if not protocol:
            return issues
        
        reagents = self._extract_reagents(protocol)
        
        # Check each pair of reagents for incompatibilities
        for i, reagent1 in enumerate(reagents):
            hazard1 = self._get_hazard_info(reagent1)
            
            for reagent2 in reagents[i + 1:]:
                hazard2 = self._get_hazard_info(reagent2)
                
                # Check if any incompatibilities match
                for incompat1 in hazard1.incompatibilities:
                    if incompat1 in hazard2.hazards:
                        issues.append(SafetyIssue(
                            reagent=f"{reagent1} + {reagent2}",
                            issue_type="incompatibility",
                            description=f"'{reagent1}' is incompatible with '{reagent2}' (reagent2 has {incompat1})",
                            severity="CRITICAL"
                        ))
                
                for incompat2 in hazard2.incompatibilities:
                    if incompat2 in hazard1.hazards:
                        issues.append(SafetyIssue(
                            reagent=f"{reagent1} + {reagent2}",
                            issue_type="incompatibility",
                            description=f"'{reagent2}' is incompatible with '{reagent1}' (reagent1 has {incompat2})",
                            severity="CRITICAL"
                        ))
        
        return issues
    
    def generate_safety_report(self, experiment: Experiment) -> SafetyReport:
        """Generate comprehensive safety report for an experiment.
        
        Args:
            experiment: The experiment to assess
            
        Returns:
            SafetyReport with all safety information
        """
        protocol = experiment.protocol
        
        if not protocol:
            return SafetyReport(
                status=ValidationStatus.FAIL,
                hazards=["No protocol defined"],
                ppe=["Unknown - protocol required"],
                waste_methods=["Unknown - protocol required"],
                emergency_protocols=["Contact safety officer"]
            )
        
        # Collect all reagents from protocol and experiment
        protocol_reagents = self._extract_reagents(protocol)
        experiment_reagents = [r.name.lower() for r in experiment.reagents]
        all_reagents = list(set(protocol_reagents + experiment_reagents))
        
        # Collect hazards, PPE, and waste methods
        all_hazards: set[str] = set()
        all_ppe: set[str] = set()
        all_waste_methods: set[str] = set()
        
        for reagent_name in all_reagents:
            hazard_info = self._get_hazard_info(reagent_name)
            all_hazards.update(hazard_info.hazards)
            all_ppe.update(hazard_info.ppe_requirements)
            if hazard_info.waste_disposal:
                all_waste_methods.add(hazard_info.waste_disposal)
        
        # Run all safety checks
        hazard_issues = self.check_hazards(protocol)
        incompat_issues = self.check_incompatibilities(protocol)
        
        all_issues = hazard_issues + incompat_issues
        
        # Check BSL requirements for sample types
        required_bsl = SafetyLevel.BSL1
        for sample in experiment.samples or []:
            sample_bsl = self.check_bsl_requirements(sample.sample_type)
            if sample_bsl.value > required_bsl.value:
                required_bsl = sample_bsl
        
        # Check if experiment's safety level is sufficient
        experiment_bsl = experiment.safety_level
        if required_bsl.value > experiment_bsl.value:
            all_issues.append(SafetyIssue(
                reagent="experiment",
                issue_type="bsl_insufficient",
                description=f"Experiment BSL ({experiment_bsl.value}) insufficient for samples (requires {required_bsl.value})",
                severity="CRITICAL"
            ))
        
        # Determine status
        has_critical = any(i.severity == "CRITICAL" for i in all_issues)
        
        if has_critical:
            status = ValidationStatus.FAIL
        elif all_issues:
            status = ValidationStatus.WARN
        else:
            status = ValidationStatus.PASS
        
        # Generate emergency protocols based on hazards
        emergency_protocols = self._generate_emergency_protocols(all_hazards)
        
        return SafetyReport(
            status=status,
            hazards=list(all_hazards),
            ppe=list(all_ppe),
            waste_methods=list(all_waste_methods),
            emergency_protocols=emergency_protocols
        )
    
    def _get_hazard_info(self, reagent_name: str) -> HazardInfo:
        """Get hazard info for a reagent, checking custom database first."""
        name_lower = reagent_name.lower()
        
        if name_lower in self._custom_hazards:
            return self._custom_hazards[name_lower]
        
        if name_lower in self.HazardDatabase:
            return self.HazardDatabase[name_lower]
        
        return self._default_hazard
    
    def _extract_reagents(self, protocol: Protocol) -> list[str]:
        """Extract reagent names from protocol."""
        reagents: list[str] = []
        
        for step in protocol.steps or []:
            params = step.parameters or {}
            
            if 'reagents' in params:
                if isinstance(params['reagents'], dict):
                    reagents.extend(params['reagents'].keys())
                elif isinstance(params['reagents'], list):
                    reagents.extend(params['reagents'])
            
            if 'reagent_list' in params:
                for item in params['reagent_list']:
                    if isinstance(item, dict):
                        if 'name' in item:
                            reagents.append(item['name'])
            
            if 'reagent' in params:
                reagent = params['reagent']
                if isinstance(reagent, str):
                    reagents.append(reagent)
                elif isinstance(reagent, list):
                    reagents.extend(reagent)
        
        return list(set(reagents))
    
    def _generate_emergency_protocols(self, hazards: set[str]) -> list[str]:
        """Generate emergency protocols based on hazard types."""
        protocols = []
        
        if "flammable" in hazards:
            protocols.append("Fire: Evacuate, pull fire alarm, use CO2 extinguisher")
        
        if "toxic" in hazards:
            protocols.append("Toxic exposure: Immediately wash affected area, seek medical attention")
        
        if "biohazard" in hazards:
            protocols.append("Biohazard spill: Evacuate area, notify biosafety officer, use spill kit")
        
        if "corrosive" in hazards:
            protocols.append("Corrosive exposure: Rinse with water for 15 minutes, seek medical attention")
        
        if "carcinogen" in hazards:
            protocols.append("Carcinogen exposure: Follow carcinogen safety protocol, seek medical attention")
        
        if not protocols:
            protocols.append("General lab emergency: Follow standard lab safety procedures")
        
        return protocols
