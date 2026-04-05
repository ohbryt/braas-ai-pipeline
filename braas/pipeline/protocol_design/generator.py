"""
BRaaS Pipeline Stage 2 - Protocol Generator.

Generates full experiment protocols from experiment specifications
using a built-in template library. Supports ELISA, qPCR, Western Blot,
and Cell Culture with detailed steps, reagent lists, and robot instructions.
"""

from __future__ import annotations

import copy
import uuid
from typing import Any, Dict, List, Optional

from braas.core.enums import ExperimentType, RobotAction
from braas.core.models import (
    IntakeResult,
    Protocol,
    ProtocolStep,
    RobotInstruction,
    RobotProgram,
)


class ProtocolGenerator:
    """
    Generates detailed experiment protocols from experiment specifications.

    Includes a template library for common bioassays and compiles
    human-readable protocols into robot-executable instructions.
    """

    # ── Protocol Template Library ──────────────────────────────────────

    PROTOCOL_TEMPLATES: Dict[ExperimentType, Dict[str, Any]] = {
        ExperimentType.ELISA: {
            "name": "Sandwich ELISA Protocol",
            "steps": [
                {
                    "description": "Coat plate with capture antibody: Dilute capture antibody to working concentration (1-10 µg/mL) in coating buffer (0.1M sodium carbonate, pH 9.6). Add 100 µL per well to 96-well MaxiSorp plate.",
                    "duration_minutes": 5.0,
                    "temperature_celsius": 22.0,
                    "reagents": ["capture antibody", "coating buffer"],
                    "volumes_ul": {"capture_antibody_solution": 100.0},
                    "equipment": ["multichannel pipette", "96-well MaxiSorp plate"],
                    "is_critical": True,
                },
                {
                    "description": "Incubate plate overnight at 4°C to allow antibody adsorption. Seal plate with adhesive film.",
                    "duration_minutes": 960.0,
                    "temperature_celsius": 4.0,
                    "reagents": [],
                    "volumes_ul": {},
                    "equipment": ["4°C refrigerator", "plate sealer"],
                    "is_critical": True,
                },
                {
                    "description": "Wash plate 3x with wash buffer (PBS + 0.05% Tween-20). Dispense 300 µL per well, aspirate completely between washes.",
                    "duration_minutes": 5.0,
                    "temperature_celsius": 22.0,
                    "reagents": ["PBST wash buffer"],
                    "volumes_ul": {"wash_buffer": 300.0},
                    "equipment": ["plate washer"],
                    "is_critical": False,
                },
                {
                    "description": "Block plate with 200 µL blocking buffer (1% BSA in PBS) per well. Incubate 1 hour at room temperature.",
                    "duration_minutes": 60.0,
                    "temperature_celsius": 22.0,
                    "reagents": ["blocking buffer (1% BSA/PBS)"],
                    "volumes_ul": {"blocking_buffer": 200.0},
                    "equipment": [],
                    "is_critical": False,
                },
                {
                    "description": "Wash plate 3x with PBST as before.",
                    "duration_minutes": 5.0,
                    "temperature_celsius": 22.0,
                    "reagents": ["PBST wash buffer"],
                    "volumes_ul": {"wash_buffer": 300.0},
                    "equipment": ["plate washer"],
                    "is_critical": False,
                },
                {
                    "description": "Add 100 µL of standards and samples to designated wells. Include blank wells. Prepare 7-point standard curve with 2-fold serial dilutions.",
                    "duration_minutes": 15.0,
                    "temperature_celsius": 22.0,
                    "reagents": ["protein standard", "sample diluent"],
                    "volumes_ul": {"sample_or_standard": 100.0},
                    "equipment": ["multichannel pipette"],
                    "is_critical": True,
                },
                {
                    "description": "Incubate 2 hours at room temperature on an orbital shaker at 400 rpm.",
                    "duration_minutes": 120.0,
                    "temperature_celsius": 22.0,
                    "reagents": [],
                    "volumes_ul": {},
                    "equipment": ["orbital shaker"],
                    "is_critical": True,
                },
                {
                    "description": "Wash plate 5x with PBST.",
                    "duration_minutes": 8.0,
                    "temperature_celsius": 22.0,
                    "reagents": ["PBST wash buffer"],
                    "volumes_ul": {"wash_buffer": 300.0},
                    "equipment": ["plate washer"],
                    "is_critical": False,
                },
                {
                    "description": "Add 100 µL biotinylated detection antibody diluted in blocking buffer. Incubate 1 hour at room temperature.",
                    "duration_minutes": 60.0,
                    "temperature_celsius": 22.0,
                    "reagents": ["detection antibody (biotinylated)", "blocking buffer"],
                    "volumes_ul": {"detection_antibody_solution": 100.0},
                    "equipment": ["multichannel pipette"],
                    "is_critical": True,
                },
                {
                    "description": "Wash plate 5x with PBST.",
                    "duration_minutes": 8.0,
                    "temperature_celsius": 22.0,
                    "reagents": ["PBST wash buffer"],
                    "volumes_ul": {"wash_buffer": 300.0},
                    "equipment": ["plate washer"],
                    "is_critical": False,
                },
                {
                    "description": "Add 100 µL streptavidin-HRP conjugate diluted per manufacturer. Incubate 30 minutes at room temperature.",
                    "duration_minutes": 30.0,
                    "temperature_celsius": 22.0,
                    "reagents": ["streptavidin-HRP"],
                    "volumes_ul": {"streptavidin_hrp_solution": 100.0},
                    "equipment": [],
                    "is_critical": False,
                },
                {
                    "description": "Wash plate 7x with PBST. Ensure complete removal of unbound conjugate.",
                    "duration_minutes": 12.0,
                    "temperature_celsius": 22.0,
                    "reagents": ["PBST wash buffer"],
                    "volumes_ul": {"wash_buffer": 300.0},
                    "equipment": ["plate washer"],
                    "is_critical": True,
                },
                {
                    "description": "Add 100 µL TMB substrate per well. Incubate 15-30 minutes at room temperature in the dark until color develops.",
                    "duration_minutes": 20.0,
                    "temperature_celsius": 22.0,
                    "reagents": ["TMB substrate"],
                    "volumes_ul": {"tmb_substrate": 100.0},
                    "equipment": [],
                    "notes": "Protect from light. Monitor color development.",
                    "is_critical": True,
                },
                {
                    "description": "Add 50 µL stop solution (2N H2SO4) per well. Read absorbance at 450 nm within 30 minutes. Optionally read at 570 nm for correction.",
                    "duration_minutes": 10.0,
                    "temperature_celsius": 22.0,
                    "reagents": ["stop solution (2N H2SO4)"],
                    "volumes_ul": {"stop_solution": 50.0},
                    "equipment": ["plate reader"],
                    "is_critical": True,
                },
            ],
            "parameters": {
                "capture_antibody_concentration_ug_ml": 2.0,
                "detection_antibody_dilution": "1:1000",
                "standard_top_concentration_ng_ml": 10.0,
                "standard_dilution_factor": 2,
                "standard_points": 7,
                "sample_dilution": "1:10",
                "substrate_incubation_minutes": 20,
                "read_wavelength_nm": 450,
                "reference_wavelength_nm": 570,
            },
        },

        ExperimentType.QPCR: {
            "name": "SYBR Green qPCR Protocol",
            "steps": [
                {
                    "description": "Extract RNA from samples using column-based RNA extraction kit. Assess RNA quality (A260/A280 > 1.8) and quantify using spectrophotometer.",
                    "duration_minutes": 45.0,
                    "temperature_celsius": 22.0,
                    "reagents": ["RNA extraction kit", "ethanol", "nuclease-free water"],
                    "volumes_ul": {},
                    "equipment": ["microcentrifuge", "spectrophotometer"],
                    "is_critical": True,
                },
                {
                    "description": "Perform reverse transcription: combine 1 µg total RNA with RT master mix. Incubate: 25°C 10 min → 42°C 60 min → 85°C 5 min.",
                    "duration_minutes": 80.0,
                    "temperature_celsius": 42.0,
                    "reagents": ["reverse transcriptase", "random hexamers", "dNTPs", "RT buffer", "RNase inhibitor"],
                    "volumes_ul": {"rna_template": 8.0, "rt_master_mix": 12.0},
                    "equipment": ["thermal cycler"],
                    "is_critical": True,
                },
                {
                    "description": "Prepare qPCR master mix: 10 µL SYBR Green 2x mix, 0.5 µL forward primer (10 µM), 0.5 µL reverse primer (10 µM), 7 µL nuclease-free water per reaction.",
                    "duration_minutes": 10.0,
                    "temperature_celsius": 4.0,
                    "reagents": ["SYBR Green 2x master mix", "forward primer", "reverse primer", "nuclease-free water"],
                    "volumes_ul": {"sybr_mix": 10.0, "forward_primer": 0.5, "reverse_primer": 0.5, "water": 7.0},
                    "equipment": ["ice bucket", "PCR plate"],
                    "notes": "Keep on ice. Prepare 10% excess to account for pipetting losses.",
                    "is_critical": True,
                },
                {
                    "description": "Dispense 18 µL master mix into each well of 96-well qPCR plate. Add 2 µL cDNA template (diluted 1:5). Include no-template controls (NTC).",
                    "duration_minutes": 15.0,
                    "temperature_celsius": 4.0,
                    "reagents": ["cDNA template"],
                    "volumes_ul": {"master_mix": 18.0, "cdna_template": 2.0},
                    "equipment": ["multichannel pipette", "qPCR plate", "optical adhesive film"],
                    "is_critical": True,
                },
                {
                    "description": "Seal plate with optical adhesive film. Centrifuge briefly (1000g, 1 min) to collect contents.",
                    "duration_minutes": 3.0,
                    "temperature_celsius": 22.0,
                    "reagents": [],
                    "volumes_ul": {},
                    "equipment": ["plate centrifuge", "optical adhesive film"],
                    "is_critical": False,
                },
                {
                    "description": "Run qPCR program: Initial denaturation 95°C 10 min → 40 cycles of [95°C 15 sec → 60°C 60 sec] → Melt curve analysis 65°C→95°C.",
                    "duration_minutes": 90.0,
                    "temperature_celsius": 95.0,
                    "reagents": [],
                    "volumes_ul": {},
                    "equipment": ["qPCR instrument"],
                    "is_critical": True,
                },
                {
                    "description": "Analyze results: verify single melt curve peak, check NTC (Ct > 35 or undetected), calculate ΔΔCt relative to reference gene.",
                    "duration_minutes": 30.0,
                    "temperature_celsius": 22.0,
                    "reagents": [],
                    "volumes_ul": {},
                    "equipment": ["analysis software"],
                    "is_critical": True,
                },
            ],
            "parameters": {
                "rna_input_ug": 1.0,
                "cdna_dilution": "1:5",
                "primer_concentration_um": 0.25,
                "annealing_temperature_celsius": 60.0,
                "extension_time_seconds": 60,
                "denaturation_time_seconds": 15,
                "number_of_cycles": 40,
                "reference_gene": "GAPDH",
                "technical_replicates": 3,
            },
        },

        ExperimentType.WESTERN_BLOT: {
            "name": "Western Blot Protocol",
            "steps": [
                {
                    "description": "Prepare cell lysates: aspirate medium, wash cells with cold PBS, add RIPA lysis buffer (150 mM NaCl, 1% NP-40, 0.5% DOC, 0.1% SDS, 50 mM Tris pH 8.0) supplemented with protease/phosphatase inhibitors. Incubate on ice 30 min.",
                    "duration_minutes": 40.0,
                    "temperature_celsius": 4.0,
                    "reagents": ["RIPA buffer", "protease inhibitor cocktail", "phosphatase inhibitor", "cold PBS"],
                    "volumes_ul": {"ripa_buffer": 200.0},
                    "equipment": ["ice bucket", "cell scraper"],
                    "is_critical": True,
                },
                {
                    "description": "Clarify lysates by centrifugation at 14,000g for 15 min at 4°C. Transfer supernatant to fresh tubes. Quantify protein by BCA assay.",
                    "duration_minutes": 45.0,
                    "temperature_celsius": 4.0,
                    "reagents": ["BCA assay kit"],
                    "volumes_ul": {},
                    "equipment": ["refrigerated centrifuge", "plate reader"],
                    "is_critical": True,
                },
                {
                    "description": "Prepare samples: normalize to equal protein loading (20-50 µg). Mix with 4x Laemmli sample buffer, heat at 95°C for 5 min. Quick-spin to collect.",
                    "duration_minutes": 15.0,
                    "temperature_celsius": 95.0,
                    "reagents": ["4x Laemmli buffer", "β-mercaptoethanol"],
                    "volumes_ul": {"sample_buffer_4x": 5.0},
                    "equipment": ["heat block", "microcentrifuge"],
                    "is_critical": True,
                },
                {
                    "description": "Load samples onto precast SDS-PAGE gel (4-15% gradient). Include molecular weight marker. Run at 80V through stacking gel, then 120V through resolving gel.",
                    "duration_minutes": 75.0,
                    "temperature_celsius": 22.0,
                    "reagents": ["running buffer (Tris-Glycine-SDS)", "molecular weight marker"],
                    "volumes_ul": {"sample": 20.0, "marker": 5.0},
                    "equipment": ["electrophoresis system", "power supply", "precast gel"],
                    "is_critical": True,
                },
                {
                    "description": "Transfer proteins to PVDF membrane: activate PVDF in methanol (1 min), assemble transfer sandwich. Transfer at 100V for 1 hour in cold transfer buffer (25 mM Tris, 192 mM glycine, 20% methanol).",
                    "duration_minutes": 70.0,
                    "temperature_celsius": 4.0,
                    "reagents": ["transfer buffer", "methanol", "PVDF membrane"],
                    "volumes_ul": {},
                    "equipment": ["transfer apparatus", "ice pack", "power supply"],
                    "is_critical": True,
                },
                {
                    "description": "Block membrane with 5% non-fat dry milk in TBST for 1 hour at room temperature on a rocker.",
                    "duration_minutes": 60.0,
                    "temperature_celsius": 22.0,
                    "reagents": ["5% milk/TBST blocking solution"],
                    "volumes_ul": {},
                    "equipment": ["rocker/shaker"],
                    "is_critical": False,
                },
                {
                    "description": "Incubate with primary antibody diluted in 5% BSA/TBST overnight at 4°C on a rocker.",
                    "duration_minutes": 960.0,
                    "temperature_celsius": 4.0,
                    "reagents": ["primary antibody", "5% BSA/TBST"],
                    "volumes_ul": {},
                    "equipment": ["4°C rocker"],
                    "is_critical": True,
                },
                {
                    "description": "Wash membrane 3x 10 min each with TBST.",
                    "duration_minutes": 30.0,
                    "temperature_celsius": 22.0,
                    "reagents": ["TBST"],
                    "volumes_ul": {},
                    "equipment": ["rocker/shaker"],
                    "is_critical": False,
                },
                {
                    "description": "Incubate with HRP-conjugated secondary antibody (1:5000-1:10000 in 5% milk/TBST) for 1 hour at RT.",
                    "duration_minutes": 60.0,
                    "temperature_celsius": 22.0,
                    "reagents": ["HRP-secondary antibody", "5% milk/TBST"],
                    "volumes_ul": {},
                    "equipment": ["rocker/shaker"],
                    "is_critical": True,
                },
                {
                    "description": "Wash membrane 3x 10 min each with TBST.",
                    "duration_minutes": 30.0,
                    "temperature_celsius": 22.0,
                    "reagents": ["TBST"],
                    "volumes_ul": {},
                    "equipment": ["rocker/shaker"],
                    "is_critical": False,
                },
                {
                    "description": "Develop with ECL substrate: mix equal volumes of detection reagents, incubate membrane 1-2 min. Image using chemiluminescence imager.",
                    "duration_minutes": 10.0,
                    "temperature_celsius": 22.0,
                    "reagents": ["ECL substrate kit"],
                    "volumes_ul": {},
                    "equipment": ["chemiluminescence imager"],
                    "is_critical": True,
                },
            ],
            "parameters": {
                "protein_loading_ug": 30,
                "gel_percentage": "4-15% gradient",
                "running_voltage_stacking": 80,
                "running_voltage_resolving": 120,
                "transfer_voltage": 100,
                "transfer_time_minutes": 60,
                "primary_antibody_dilution": "1:1000",
                "secondary_antibody_dilution": "1:5000",
                "membrane_type": "PVDF",
            },
        },

        ExperimentType.CELL_CULTURE: {
            "name": "Adherent Cell Culture Protocol",
            "steps": [
                {
                    "description": "Thaw frozen cell vial rapidly in 37°C water bath (~2 min). Transfer cells to 15 mL tube with 10 mL pre-warmed complete medium.",
                    "duration_minutes": 5.0,
                    "temperature_celsius": 37.0,
                    "reagents": ["complete culture medium", "FBS"],
                    "volumes_ul": {},
                    "equipment": ["water bath", "biosafety cabinet", "15 mL tube"],
                    "is_critical": True,
                },
                {
                    "description": "Centrifuge at 300g for 5 min. Aspirate supernatant carefully. Resuspend pellet in 5 mL fresh complete medium.",
                    "duration_minutes": 10.0,
                    "temperature_celsius": 22.0,
                    "reagents": ["complete culture medium"],
                    "volumes_ul": {},
                    "equipment": ["centrifuge", "aspirator"],
                    "is_critical": False,
                },
                {
                    "description": "Transfer cell suspension to T-25 flask. Add complete medium to 5 mL total. Place in 37°C, 5% CO2 humidified incubator.",
                    "duration_minutes": 5.0,
                    "temperature_celsius": 37.0,
                    "reagents": ["complete culture medium"],
                    "volumes_ul": {},
                    "equipment": ["T-25 flask", "CO2 incubator"],
                    "is_critical": True,
                },
                {
                    "description": "Monitor cell attachment and growth daily using inverted microscope. Change medium every 2-3 days.",
                    "duration_minutes": 15.0,
                    "temperature_celsius": 37.0,
                    "reagents": ["complete culture medium"],
                    "volumes_ul": {},
                    "equipment": ["inverted microscope", "CO2 incubator"],
                    "is_critical": False,
                },
                {
                    "description": "When cells reach 80-90% confluency, passage: aspirate medium, wash with PBS, add 0.25% trypsin-EDTA (1 mL per 25 cm²). Incubate 3-5 min at 37°C.",
                    "duration_minutes": 10.0,
                    "temperature_celsius": 37.0,
                    "reagents": ["PBS", "0.25% trypsin-EDTA"],
                    "volumes_ul": {"trypsin": 1000.0},
                    "equipment": ["biosafety cabinet", "incubator"],
                    "is_critical": True,
                },
                {
                    "description": "Neutralize trypsin with 2x volume of complete medium. Collect cells, count using hemocytometer or automated counter. Assess viability (>90% expected).",
                    "duration_minutes": 10.0,
                    "temperature_celsius": 22.0,
                    "reagents": ["complete culture medium", "trypan blue"],
                    "volumes_ul": {},
                    "equipment": ["hemocytometer or cell counter"],
                    "is_critical": True,
                },
                {
                    "description": "Seed cells at desired density (e.g., 2-5 × 10⁴ cells/cm²) into new flask or experimental plates. Return to incubator.",
                    "duration_minutes": 10.0,
                    "temperature_celsius": 37.0,
                    "reagents": ["complete culture medium"],
                    "volumes_ul": {},
                    "equipment": ["culture vessels", "CO2 incubator"],
                    "is_critical": True,
                },
                {
                    "description": "For experiments: seed into appropriate format (96-well, 24-well, 6-well). Allow cells to adhere overnight before treatment.",
                    "duration_minutes": 15.0,
                    "temperature_celsius": 37.0,
                    "reagents": ["complete culture medium"],
                    "volumes_ul": {},
                    "equipment": ["multi-well plates", "multichannel pipette"],
                    "is_critical": False,
                },
            ],
            "parameters": {
                "cell_line": "HEK293",
                "medium": "DMEM + 10% FBS + 1% Pen/Strep",
                "seeding_density_cells_per_cm2": 30000,
                "passage_confluency_percent": 85,
                "incubation_temperature_celsius": 37.0,
                "co2_percent": 5.0,
                "trypsin_concentration": "0.25%",
                "passage_ratio": "1:4",
            },
        },
    }

    def __init__(self) -> None:
        """Initialize the protocol generator."""
        self._custom_templates: Dict[str, Dict[str, Any]] = {}

    async def generate_protocol(
        self,
        intake_result: IntakeResult,
        custom_parameters: Optional[Dict[str, Any]] = None,
    ) -> Protocol:
        """
        Generate a full protocol from intake results.

        Args:
            intake_result: Parsed intake result specifying the experiment.
            custom_parameters: Optional parameter overrides.

        Returns:
            A Protocol object with detailed steps.
        """
        exp_type = intake_result.experiment_type

        template = self.PROTOCOL_TEMPLATES.get(exp_type)
        if template is None:
            # Return a minimal placeholder protocol
            return Protocol(
                name=f"Custom Protocol for {exp_type.value}",
                experiment_type=exp_type,
                steps=[
                    ProtocolStep(
                        step_number=1,
                        description=f"Custom protocol for {exp_type.value} - template not yet available. "
                        "Please provide detailed steps or contact protocol team.",
                        duration_minutes=0.0,
                    )
                ],
                notes="Auto-generated placeholder. No template available for this experiment type.",
            )

        # Deep copy template to avoid mutation
        template = copy.deepcopy(template)

        # Build protocol steps
        steps: List[ProtocolStep] = []
        for i, step_data in enumerate(template["steps"], start=1):
            steps.append(ProtocolStep(
                step_number=i,
                description=step_data["description"],
                duration_minutes=step_data.get("duration_minutes", 0.0),
                temperature_celsius=step_data.get("temperature_celsius"),
                reagents=step_data.get("reagents", []),
                volumes_ul=step_data.get("volumes_ul", {}),
                equipment=step_data.get("equipment", []),
                notes=step_data.get("notes", ""),
                is_critical=step_data.get("is_critical", False),
            ))

        # Merge parameters
        parameters = dict(template.get("parameters", {}))
        if custom_parameters:
            parameters.update(custom_parameters)

        # Apply intake-specific customizations
        parameters = await self.optimize_parameters(
            exp_type, parameters, intake_result
        )

        # Calculate totals
        total_duration = sum(s.duration_minutes for s in steps) / 60.0
        reagents_needed = self._aggregate_reagents(steps, intake_result.sample_count)
        equipment_needed = list({eq for s in steps for eq in s.equipment})

        # Generate protocol name incorporating target
        name = template["name"]
        if intake_result.target_protein:
            name = f"{intake_result.target_protein} {name}"
        if intake_result.organism.value != "unknown":
            name = f"{name} ({intake_result.organism.value})"

        protocol = Protocol(
            name=name,
            experiment_type=exp_type,
            steps=steps,
            total_duration_hours=round(total_duration, 2),
            reagents_needed=reagents_needed,
            equipment_needed=equipment_needed,
            parameters=parameters,
            notes=f"Generated for: {intake_result.raw_text[:200]}",
        )

        return protocol

    async def optimize_parameters(
        self,
        experiment_type: ExperimentType,
        parameters: Dict[str, Any],
        intake_result: IntakeResult,
    ) -> Dict[str, Any]:
        """
        Optimize protocol parameters based on experiment context.

        Applies heuristic rules to adjust default parameters for the
        specific experimental context (organism, sample type, etc.).

        Args:
            experiment_type: The type of experiment.
            parameters: Current parameter set.
            intake_result: Parsed intake for context.

        Returns:
            Optimized parameters dict.
        """
        params = dict(parameters)

        if experiment_type == ExperimentType.ELISA:
            # Adjust dilution for different sample types
            from braas.core.enums import SampleType
            if intake_result.sample_type == SampleType.SERUM:
                params["sample_dilution"] = "1:50"
            elif intake_result.sample_type == SampleType.SUPERNATANT:
                params["sample_dilution"] = "1:2"
            elif intake_result.sample_type == SampleType.CELL_LYSATE:
                params["sample_dilution"] = "1:10"

            # Adjust for special requirements
            if "high throughput" in intake_result.special_requirements:
                params["plate_format"] = 384
            if "low volume" in intake_result.special_requirements:
                params["well_volume_ul"] = 50

        elif experiment_type == ExperimentType.QPCR:
            if "time course" in intake_result.special_requirements:
                params["include_time_points"] = True
            if intake_result.target_protein:
                params["target_gene"] = intake_result.target_protein

        elif experiment_type == ExperimentType.WESTERN_BLOT:
            # Adjust for phospho-proteins
            if intake_result.target_protein and intake_result.target_protein.startswith("p"):
                params["blocking_agent"] = "5% BSA/TBST (phospho-specific)"
                params["include_phosphatase_inhibitor"] = True

        elif experiment_type == ExperimentType.CELL_CULTURE:
            if "serum-free" in intake_result.special_requirements:
                params["medium"] = "Serum-free medium"
            if "hypoxia" in intake_result.special_requirements:
                params["oxygen_percent"] = 1.0

        # Add sample count to parameters
        params["sample_count"] = intake_result.sample_count

        return params

    async def compile_to_robot_instructions(
        self,
        protocol: Protocol,
    ) -> RobotProgram:
        """
        Compile a human-readable protocol into robot-executable instructions.

        Translates protocol steps into a sequence of atomic robot actions
        (aspirate, dispense, mix, incubate, etc.).

        Args:
            protocol: The protocol to compile.

        Returns:
            RobotProgram with executable instructions and deck layout.
        """
        instructions: List[RobotInstruction] = []
        tip_count = 0
        total_time = 0.0

        # Define deck layout based on experiment type
        deck_layout = self._get_deck_layout(protocol.experiment_type)

        for step in protocol.steps:
            # Convert each protocol step to robot instructions
            step_instructions = self._step_to_robot_instructions(step, deck_layout)
            instructions.extend(step_instructions)

            # Count tips (new tip for each transfer)
            tip_count += sum(
                1 for inst in step_instructions
                if inst.action in (RobotAction.ASPIRATE, RobotAction.TRANSFER)
            )

            total_time += step.duration_minutes

        # Multiply tip count by sample count
        sample_count = protocol.parameters.get("sample_count", 1)
        tip_count *= sample_count

        return RobotProgram(
            protocol_id=protocol.id,
            instructions=instructions,
            estimated_runtime_minutes=total_time,
            deck_layout=deck_layout,
            tip_count=tip_count,
        )

    def register_template(
        self, name: str, template: Dict[str, Any]
    ) -> None:
        """
        Register a custom protocol template.

        Args:
            name: Template name/key.
            template: Template dict following the same structure as built-in templates.
        """
        self._custom_templates[name] = template

    # ── Private Methods ────────────────────────────────────────────────

    def _aggregate_reagents(
        self,
        steps: List[ProtocolStep],
        sample_count: int,
    ) -> Dict[str, float]:
        """Aggregate total reagent volumes across all steps."""
        totals: Dict[str, float] = {}
        for step in steps:
            for reagent_key, volume in step.volumes_ul.items():
                if reagent_key not in totals:
                    totals[reagent_key] = 0.0
                totals[reagent_key] += volume * sample_count

        # Add 15% overhead for dead volume and pipetting loss
        return {k: round(v * 1.15, 1) for k, v in totals.items()}

    def _get_deck_layout(self, exp_type: ExperimentType) -> Dict[str, str]:
        """Get robot deck layout for an experiment type."""
        layouts: Dict[ExperimentType, Dict[str, str]] = {
            ExperimentType.ELISA: {
                "1": "96-well MaxiSorp plate",
                "2": "reagent reservoir (wash buffer)",
                "3": "reagent reservoir (substrates)",
                "4": "sample rack (tubes)",
                "5": "standard dilution plate",
                "6": "tip rack 200 µL",
                "7": "tip rack 200 µL",
                "8": "waste container",
            },
            ExperimentType.QPCR: {
                "1": "96-well qPCR plate",
                "2": "reagent reservoir (master mix)",
                "3": "sample rack (cDNA tubes)",
                "4": "tip rack 20 µL",
                "5": "tip rack 20 µL",
                "6": "tip rack 200 µL",
                "7": "cold block (4°C)",
                "8": "waste container",
            },
            ExperimentType.WESTERN_BLOT: {
                "1": "sample preparation plate",
                "2": "reagent rack (buffers)",
                "3": "tip rack 200 µL",
                "4": "tip rack 20 µL",
                "5": "heat block position",
                "6": "waste container",
            },
            ExperimentType.CELL_CULTURE: {
                "1": "cell culture plate",
                "2": "reagent reservoir (medium)",
                "3": "reagent reservoir (PBS)",
                "4": "reagent reservoir (trypsin)",
                "5": "collection plate/tubes",
                "6": "tip rack 1000 µL",
                "7": "tip rack 200 µL",
                "8": "waste container",
            },
        }
        return layouts.get(exp_type, {"1": "working plate", "2": "reagent rack", "3": "tip rack"})

    def _step_to_robot_instructions(
        self,
        step: ProtocolStep,
        deck_layout: Dict[str, str],
    ) -> List[RobotInstruction]:
        """Convert a protocol step into a list of robot instructions."""
        instructions: List[RobotInstruction] = []

        # Add a comment instruction for the step
        instructions.append(RobotInstruction(
            action=RobotAction.COMMENT,
            comment=f"Step {step.step_number}: {step.description[:100]}...",
        ))

        # Convert volume operations to aspirate/dispense pairs
        for reagent, volume in step.volumes_ul.items():
            instructions.append(RobotInstruction(
                action=RobotAction.ASPIRATE,
                volume_ul=volume,
                comment=f"Aspirate {reagent}",
                parameters={"reagent": reagent},
            ))
            instructions.append(RobotInstruction(
                action=RobotAction.DISPENSE,
                volume_ul=volume,
                comment=f"Dispense {reagent}",
                parameters={"reagent": reagent},
            ))

        # Check for wash steps
        if "wash" in step.description.lower():
            wash_count = 3
            for match in __import__("re").finditer(r"(\d+)x", step.description):
                wash_count = int(match.group(1))
                break
            instructions.append(RobotInstruction(
                action=RobotAction.WASH,
                parameters={"cycles": wash_count, "volume_ul": 300.0},
                volume_ul=300.0,
                comment=f"Wash {wash_count}x",
            ))

        # Check for mixing steps
        if "mix" in step.description.lower() or "resuspend" in step.description.lower():
            instructions.append(RobotInstruction(
                action=RobotAction.MIX,
                parameters={"cycles": 5},
                volume_ul=step.volumes_ul.get(
                    list(step.volumes_ul.keys())[0], 100.0
                ) if step.volumes_ul else 100.0,
                comment="Mix well",
            ))

        # Check for incubation steps
        if step.duration_minutes > 5.0 and step.temperature_celsius is not None:
            instructions.append(RobotInstruction(
                action=RobotAction.INCUBATE,
                duration_seconds=step.duration_minutes * 60,
                temperature_celsius=step.temperature_celsius,
                comment=f"Incubate {step.duration_minutes} min at {step.temperature_celsius}°C",
            ))

        # Check for heating
        if step.temperature_celsius and step.temperature_celsius > 60:
            instructions.append(RobotInstruction(
                action=RobotAction.HEAT,
                temperature_celsius=step.temperature_celsius,
                duration_seconds=step.duration_minutes * 60,
                comment=f"Heat to {step.temperature_celsius}°C",
            ))

        # Check for centrifugation
        if "centrifug" in step.description.lower():
            instructions.append(RobotInstruction(
                action=RobotAction.CENTRIFUGE,
                parameters={"speed_g": 1000, "time_seconds": 60},
                duration_seconds=60,
                comment="Centrifuge",
            ))

        # Check for plate reading
        if "read" in step.description.lower() and ("absorbance" in step.description.lower() or "plate reader" in str(step.equipment)):
            instructions.append(RobotInstruction(
                action=RobotAction.READ_PLATE,
                parameters={"wavelength_nm": 450, "type": "absorbance"},
                comment="Read plate",
            ))

        # Check for shaking
        if "shak" in step.description.lower() or "rocker" in step.description.lower():
            instructions.append(RobotInstruction(
                action=RobotAction.SHAKE,
                parameters={"speed_rpm": 400},
                duration_seconds=step.duration_minutes * 60,
                comment="Shake/rock",
            ))

        return instructions
