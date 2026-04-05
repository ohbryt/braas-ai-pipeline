"""
BRaaS Core Enumerations.

Defines all enums used throughout the BRaaS AI pipeline system.
"""

from enum import Enum, auto


class ExperimentType(str, Enum):
    """Supported experiment types."""
    ELISA = "elisa"
    QPCR = "qpcr"
    WESTERN_BLOT = "western_blot"
    CELL_CULTURE = "cell_culture"
    FLOW_CYTOMETRY = "flow_cytometry"
    IMMUNOFLUORESCENCE = "immunofluorescence"
    MASS_SPECTROMETRY = "mass_spectrometry"
    RNA_SEQ = "rna_seq"
    CRISPR = "crispr"
    CLONING = "cloning"
    PROTEIN_PURIFICATION = "protein_purification"
    UNKNOWN = "unknown"


class ExperimentStatus(str, Enum):
    """Status of an experiment through the pipeline."""
    DRAFT = "draft"
    INTAKE_COMPLETE = "intake_complete"
    PROTOCOL_DESIGNED = "protocol_designed"
    VALIDATED = "validated"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SampleType(str, Enum):
    """Types of biological samples."""
    SERUM = "serum"
    PLASMA = "plasma"
    WHOLE_BLOOD = "whole_blood"
    TISSUE = "tissue"
    CELL_LYSATE = "cell_lysate"
    CELL_SUSPENSION = "cell_suspension"
    RNA = "rna"
    DNA = "dna"
    PROTEIN = "protein"
    SUPERNATANT = "supernatant"
    URINE = "urine"
    CSF = "csf"
    UNKNOWN = "unknown"


class Organism(str, Enum):
    """Model organisms and species."""
    HUMAN = "human"
    MOUSE = "mouse"
    RAT = "rat"
    RABBIT = "rabbit"
    E_COLI = "e_coli"
    YEAST = "yeast"
    DROSOPHILA = "drosophila"
    ZEBRAFISH = "zebrafish"
    C_ELEGANS = "c_elegans"
    UNKNOWN = "unknown"


class BiosafetLevel(str, Enum):
    """Biosafety levels."""
    BSL1 = "BSL-1"
    BSL2 = "BSL-2"
    BSL3 = "BSL-3"
    BSL4 = "BSL-4"


class HazardCategory(str, Enum):
    """Chemical/biological hazard categories."""
    FLAMMABLE = "flammable"
    CORROSIVE = "corrosive"
    TOXIC = "toxic"
    CARCINOGEN = "carcinogen"
    MUTAGEN = "mutagen"
    OXIDIZER = "oxidizer"
    BIOHAZARD = "biohazard"
    RADIOACTIVE = "radioactive"
    IRRITANT = "irritant"
    ENVIRONMENTAL = "environmental"


class ValidationStatus(str, Enum):
    """Validation check result status."""
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


class PipelineStage(str, Enum):
    """Stages of the BRaaS pipeline."""
    INTAKE = "intake"
    PROTOCOL_DESIGN = "protocol_design"
    VALIDATION = "validation"
    SCHEDULING = "scheduling"
    EXECUTION = "execution"
    MONITORING = "monitoring"
    ANALYSIS = "analysis"
    REPORTING = "reporting"
    LEARNING = "learning"


class IntentType(str, Enum):
    """Classified intent types from NLP intake."""
    NEW_EXPERIMENT = "new_experiment"
    REPEAT_EXPERIMENT = "repeat_experiment"
    OPTIMIZATION = "optimization"
    TROUBLESHOOTING = "troubleshooting"
    COMPARISON = "comparison"
    SCREENING = "screening"
    UNKNOWN = "unknown"


class RobotAction(str, Enum):
    """Robot instruction action types."""
    ASPIRATE = "aspirate"
    DISPENSE = "dispense"
    MIX = "mix"
    TRANSFER = "transfer"
    INCUBATE = "incubate"
    WASH = "wash"
    CENTRIFUGE = "centrifuge"
    HEAT = "heat"
    COOL = "cool"
    SHAKE = "shake"
    READ_PLATE = "read_plate"
    PAUSE = "pause"
    COMMENT = "comment"
