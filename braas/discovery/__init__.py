"""BRaaS Drug Discovery Module.

This module provides tools for molecular compound generation, target analysis,
and drug candidate evaluation for the BRaaS platform. It focuses on TGF-beta
superfamily targets including myostatin, activin, and BMP receptors.
"""

from braas.discovery.engine import DrugDiscoveryEngine
from braas.discovery.generator import CompoundGenerator
from braas.discovery.target import TargetAnalyzer
from braas.discovery.docking import DockingSimulator
from braas.discovery.lead_optimizer import LeadOptimizer
from braas.discovery.models import (
    Compound,
    CompoundScore,
    DrugCandidate,
    TargetAnalysis,
    BindingSite,
    ADMETPrediction,
    DockingResult,
    SelectivityScore,
    Interaction,
    Mutation,
    Domain,
    DruggabilityScore,
    PathwayContext,
    CytotoxicityPrediction,
    Modification,
    SARAnalysis,
)

__all__ = [
    # Main engine
    "DrugDiscoveryEngine",
    # Sub-modules
    "CompoundGenerator",
    "TargetAnalyzer",
    "DockingSimulator",
    "LeadOptimizer",
    # Data models
    "Compound",
    "CompoundScore",
    "DrugCandidate",
    "TargetAnalysis",
    "BindingSite",
    "ADMETPrediction",
    "DockingResult",
    "SelectivityScore",
    "Interaction",
    "Mutation",
    "Domain",
    "DruggabilityScore",
    "PathwayContext",
    "CytotoxicityPrediction",
    "Modification",
    "SARAnalysis",
]

__version__ = "1.0.0"
