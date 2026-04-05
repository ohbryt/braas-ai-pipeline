"""
BRaaS Utility Helpers
======================

Laboratory-focused utility functions for plate layouts, dilution
calculations, cost estimation, formatting, and validation.
"""

from __future__ import annotations

import string
from typing import Any


def generate_plate_layout(
    rows: int = 8,
    columns: int = 12,
    sample_names: list[str] | None = None,
    blanks: list[str] | None = None,
    controls_positive: list[str] | None = None,
    controls_negative: list[str] | None = None,
    replicates: int = 1,
) -> dict[str, dict[str, Any]]:
    """Generate a microplate well layout with sample assignments.

    Creates a well-map for standard plate formats (96-well, 384-well, etc.)
    with automatic placement of samples, blanks, and controls.

    Args:
        rows: Number of plate rows (default 8 for 96-well: A-H).
        columns: Number of plate columns (default 12 for 96-well).
        sample_names: List of sample names to assign to wells.
        blanks: Well positions for blank wells (e.g., ["A1", "A2"]).
        controls_positive: Well positions for positive controls.
        controls_negative: Well positions for negative controls.
        replicates: Number of replicates per sample.

    Returns:
        Dict mapping well IDs (e.g. "A1") to well info dicts with keys:
        'row', 'column', 'well_type', 'sample_name', 'replicate'.

    Raises:
        ValueError: If samples exceed available wells or rows > 26.

    Example:
        >>> layout = generate_plate_layout(sample_names=["S1", "S2"])
        >>> layout["A1"]["sample_name"]
        'S1'
    """
    if rows > 26:
        raise ValueError(f"Maximum 26 rows (A-Z) supported, got {rows}")
    if rows < 1 or columns < 1:
        raise ValueError("Rows and columns must be positive integers")

    blanks = blanks or []
    controls_positive = controls_positive or []
    controls_negative = controls_negative or []
    sample_names = sample_names or []

    row_labels = list(string.ascii_uppercase[:rows])
    layout: dict[str, dict[str, Any]] = {}

    # Initialize all wells as empty
    for r in row_labels:
        for c in range(1, columns + 1):
            well_id = f"{r}{c}"
            layout[well_id] = {
                "row": r,
                "column": c,
                "well_type": "empty",
                "sample_name": "",
                "replicate": 0,
            }

    # Assign special wells
    for well_id in blanks:
        if well_id in layout:
            layout[well_id]["well_type"] = "blank"
            layout[well_id]["sample_name"] = "BLANK"

    for well_id in controls_positive:
        if well_id in layout:
            layout[well_id]["well_type"] = "positive_control"
            layout[well_id]["sample_name"] = "POS_CTRL"

    for well_id in controls_negative:
        if well_id in layout:
            layout[well_id]["well_type"] = "negative_control"
            layout[well_id]["sample_name"] = "NEG_CTRL"

    # Assign samples to remaining empty wells
    reserved_wells = set(blanks) | set(controls_positive) | set(controls_negative)
    available_wells = [
        f"{r}{c}"
        for r in row_labels
        for c in range(1, columns + 1)
        if f"{r}{c}" not in reserved_wells
    ]

    total_needed = len(sample_names) * replicates
    if total_needed > len(available_wells):
        raise ValueError(
            f"Need {total_needed} wells for {len(sample_names)} samples × "
            f"{replicates} replicates, but only {len(available_wells)} wells available"
        )

    well_idx = 0
    for sample_name in sample_names:
        for rep in range(1, replicates + 1):
            well_id = available_wells[well_idx]
            layout[well_id]["well_type"] = "sample"
            layout[well_id]["sample_name"] = sample_name
            layout[well_id]["replicate"] = rep
            well_idx += 1

    return layout


def calculate_dilution_series(
    initial_concentration: float,
    dilution_factor: float,
    num_dilutions: int,
    final_volume_ul: float = 100.0,
) -> list[dict[str, float]]:
    """Calculate a serial dilution series.

    Computes the concentrations and volumes needed for each step
    of a serial dilution.

    Args:
        initial_concentration: Starting concentration (any unit).
        dilution_factor: Fold-dilution at each step (e.g. 2 for 1:2).
        num_dilutions: Number of dilution steps to perform.
        final_volume_ul: Desired final volume per tube in µL.

    Returns:
        List of dicts, each containing:
            - 'step': 1-based step index
            - 'concentration': resulting concentration
            - 'dilution': cumulative dilution fold
            - 'sample_volume_ul': volume of sample to transfer
            - 'diluent_volume_ul': volume of diluent to add
            - 'final_volume_ul': total volume after mixing

    Raises:
        ValueError: If inputs are invalid.

    Example:
        >>> series = calculate_dilution_series(1000, 2, 5, 200)
        >>> [s["concentration"] for s in series]
        [1000.0, 500.0, 250.0, 125.0, 62.5]
    """
    if initial_concentration <= 0:
        raise ValueError(f"Initial concentration must be positive, got {initial_concentration}")
    if dilution_factor <= 1:
        raise ValueError(f"Dilution factor must be > 1, got {dilution_factor}")
    if num_dilutions < 1:
        raise ValueError(f"Number of dilutions must be >= 1, got {num_dilutions}")
    if final_volume_ul <= 0:
        raise ValueError(f"Final volume must be positive, got {final_volume_ul}")

    series: list[dict[str, float]] = []
    sample_volume = final_volume_ul / dilution_factor
    diluent_volume = final_volume_ul - sample_volume

    for step in range(num_dilutions):
        cumulative_dilution = dilution_factor ** step
        concentration = initial_concentration / cumulative_dilution
        series.append({
            "step": float(step + 1),
            "concentration": round(concentration, 6),
            "dilution": cumulative_dilution,
            "sample_volume_ul": round(sample_volume, 2),
            "diluent_volume_ul": round(diluent_volume, 2),
            "final_volume_ul": final_volume_ul,
        })

    return series


def estimate_experiment_cost(
    experiment_type: str,
    num_samples: int,
    num_replicates: int = 3,
    reagent_costs: dict[str, float] | None = None,
    equipment_hourly_rate: float = 25.0,
    estimated_hours: float | None = None,
    labor_hourly_rate: float = 50.0,
) -> dict[str, float]:
    """Estimate the total cost of running an experiment.

    Provides a breakdown of reagent, equipment, labor, and overhead costs.

    Args:
        experiment_type: Type of experiment (matches ExperimentType values).
        num_samples: Number of samples to process.
        num_replicates: Technical replicates per sample.
        reagent_costs: Optional dict of reagent_name -> cost_per_sample.
                       If None, uses built-in estimates.
        equipment_hourly_rate: Equipment usage cost per hour (USD).
        estimated_hours: Manual override for duration. If None, uses
                        built-in estimates per experiment type.
        labor_hourly_rate: Labor cost per hour (USD).

    Returns:
        Cost breakdown dict with keys: 'reagent_cost', 'equipment_cost',
        'labor_cost', 'overhead_cost', 'total_cost', 'cost_per_sample'.
    """
    # Default reagent cost per sample by experiment type (USD)
    default_reagent_costs: dict[str, float] = {
        "elisa": 8.50,
        "qpcr": 5.00,
        "western_blot": 15.00,
        "cell_culture": 12.00,
        "cloning": 25.00,
        "sequencing": 50.00,
        "flow_cytometry": 10.00,
    }

    # Default durations in hours
    default_durations: dict[str, float] = {
        "elisa": 6.0,
        "qpcr": 3.0,
        "western_blot": 10.0,
        "cell_culture": 72.0,
        "cloning": 168.0,
        "sequencing": 24.0,
        "flow_cytometry": 4.0,
    }

    total_reactions = num_samples * num_replicates

    # Reagent cost
    if reagent_costs:
        per_sample_reagent = sum(reagent_costs.values())
    else:
        per_sample_reagent = default_reagent_costs.get(experiment_type, 10.0)
    reagent_cost = per_sample_reagent * total_reactions

    # Duration
    hours = estimated_hours or default_durations.get(experiment_type, 8.0)

    # Equipment cost
    equipment_cost = hours * equipment_hourly_rate

    # Labor cost (assume 30% of time requires active attention)
    active_fraction = min(1.0, 0.3 + (0.1 if experiment_type in ("cloning", "cell_culture") else 0))
    labor_cost = hours * active_fraction * labor_hourly_rate

    # Overhead (15% of direct costs)
    direct_costs = reagent_cost + equipment_cost + labor_cost
    overhead_cost = direct_costs * 0.15

    total_cost = direct_costs + overhead_cost

    return {
        "reagent_cost": round(reagent_cost, 2),
        "equipment_cost": round(equipment_cost, 2),
        "labor_cost": round(labor_cost, 2),
        "overhead_cost": round(overhead_cost, 2),
        "total_cost": round(total_cost, 2),
        "cost_per_sample": round(total_cost / max(num_samples, 1), 2),
        "total_reactions": float(total_reactions),
        "estimated_hours": hours,
    }


def format_duration(seconds: float) -> str:
    """Format a duration in seconds to a human-readable string.

    Args:
        seconds: Duration in seconds.

    Returns:
        Formatted string like '2h 30m 15s', '5d 3h 10m', etc.

    Examples:
        >>> format_duration(90)
        '1m 30s'
        >>> format_duration(3661)
        '1h 1m 1s'
        >>> format_duration(90061)
        '1d 1h 1m'
    """
    if seconds < 0:
        return f"-{format_duration(abs(seconds))}"
    if seconds < 1:
        return f"{seconds:.1f}s"

    days = int(seconds // 86400)
    remaining = seconds % 86400
    hours = int(remaining // 3600)
    remaining = remaining % 3600
    minutes = int(remaining // 60)
    secs = int(remaining % 60)

    parts: list[str] = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")

    # Only show seconds if duration < 1 hour or if no larger units
    if days == 0 and hours == 0 and secs > 0:
        parts.append(f"{secs}s")
    elif not parts:
        parts.append(f"{secs}s")

    return " ".join(parts)


def validate_concentration(
    value: float,
    unit: str,
    min_value: float | None = None,
    max_value: float | None = None,
    sample_type: str | None = None,
) -> dict[str, Any]:
    """Validate a concentration value against expected ranges.

    Checks that a concentration is within acceptable bounds for
    the given unit and optional sample type. Returns a validation
    result dict with status, warnings, and normalized value.

    Args:
        value: The concentration value to validate.
        unit: Concentration unit (e.g. 'ng/uL', 'nM', 'cells/mL', 'mg/mL').
        min_value: Optional minimum allowed value.
        max_value: Optional maximum allowed value.
        sample_type: Optional sample type for type-specific validation.

    Returns:
        Dict with keys:
            - 'valid' (bool): Whether the concentration is acceptable.
            - 'value' (float): The input value.
            - 'unit' (str): The unit.
            - 'warnings' (list[str]): Any warning messages.
            - 'errors' (list[str]): Any error messages.
            - 'suggested_range' (dict): Min/max for the given context.

    Example:
        >>> result = validate_concentration(500, "ng/uL", sample_type="dna")
        >>> result["valid"]
        True
    """
    errors: list[str] = []
    warnings: list[str] = []

    if value < 0:
        errors.append("Concentration cannot be negative")

    # Default ranges by unit and sample type
    default_ranges: dict[str, dict[str, tuple[float, float]]] = {
        "ng/uL": {
            "dna": (1.0, 5000.0),
            "rna": (0.1, 10000.0),
            "protein": (0.01, 50000.0),
            "default": (0.001, 100000.0),
        },
        "nM": {
            "primer": (100.0, 100000.0),
            "probe": (50.0, 50000.0),
            "default": (0.001, 1000000.0),
        },
        "cells/mL": {
            "cell_suspension": (1e3, 1e8),
            "default": (1.0, 1e10),
        },
        "mg/mL": {
            "protein": (0.001, 100.0),
            "antibody": (0.01, 20.0),
            "default": (0.0001, 1000.0),
        },
        "uM": {
            "default": (0.001, 100000.0),
        },
        "M": {
            "default": (1e-12, 10.0),
        },
    }

    # Determine applicable range
    unit_ranges = default_ranges.get(unit, {"default": (0.0, float("inf"))})
    type_key = sample_type if sample_type and sample_type in unit_ranges else "default"
    default_min, default_max = unit_ranges.get(type_key, unit_ranges["default"])

    effective_min = min_value if min_value is not None else default_min
    effective_max = max_value if max_value is not None else default_max

    if value < effective_min:
        errors.append(
            f"Concentration {value} {unit} below minimum {effective_min} {unit}"
        )
    elif value > effective_max:
        errors.append(
            f"Concentration {value} {unit} above maximum {effective_max} {unit}"
        )

    # Warn on edge cases
    if value == 0 and not errors:
        warnings.append("Concentration is zero — verify this is intentional")
    elif 0 < value < effective_min * 10 and not errors:
        warnings.append(
            f"Concentration {value} {unit} is near the lower limit — "
            "measurement may be unreliable"
        )

    return {
        "valid": len(errors) == 0,
        "value": value,
        "unit": unit,
        "warnings": warnings,
        "errors": errors,
        "suggested_range": {
            "min": effective_min,
            "max": effective_max,
            "unit": unit,
        },
    }
