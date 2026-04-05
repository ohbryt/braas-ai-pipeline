"""
BRaaS - Bio Research-as-a-Service AI Pipeline
===============================================

A comprehensive AI-driven platform for automating biological research workflows,
from experiment design through execution, monitoring, and analysis.

Modules:
    core: Data models, enums, events, and exceptions
    config: Application settings and configuration
    utils: Logging, metrics, and helper utilities
"""

__version__ = "0.1.0"
__author__ = "BRaaS Team"
__license__ = "Proprietary"

from braas.core.enums import ExperimentStatus, ExperimentType, Priority, SafetyLevel
from braas.core.exceptions import BRaaSError
from braas.core.models import Experiment, Protocol, Sample

__all__ = [
    "__version__",
    "Experiment",
    "Protocol",
    "Sample",
    "ExperimentType",
    "ExperimentStatus",
    "Priority",
    "SafetyLevel",
    "BRaaSError",
]
