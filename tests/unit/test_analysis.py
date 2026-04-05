"""
Unit tests for the Data Analysis Engine.

These tests verify the data analysis and processing capabilities of the
braas.pipeline.analysis.processor.DataAnalysisEngine class, which handles
experimental data processing, curve fitting, statistical analysis, and
outlier detection.
"""

import pytest
import numpy as np
from unittest.mock import AsyncMock, MagicMock, patch

from braas.pipeline.analysis.processor import (
    DataAnalysisEngine,
    AnalysisResult,
)


class TestDataAnalysisEngine:
    """Test suite for DataAnalysisEngine."""

    @pytest.fixture
    def engine(self) -> DataAnalysisEngine:
        """Create a DataAnalysisEngine instance for testing."""
        return DataAnalysisEngine()

    @pytest.fixture
    def mock_elisa_plate_data(self) -> dict:
        """Create realistic 96-well ELISA plate data."""
        concentrations = [0, 7.8125, 15.625, 31.25, 62.5, 125, 250, 500]

        std_wells = {
            "A1": 0.05, "A2": 0.048,
            "B1": 0.092, "B2": 0.095,
            "C1": 0.185, "C2": 0.188,
            "D1": 0.342, "D2": 0.345,
            "E1": 0.612, "E2": 0.608,
            "F1": 0.895, "F2": 0.902,
            "G1": 1.085, "G2": 1.092,
            "H1": 1.205, "H2": 1.198,
        }

        sample_wells = {}
        row_letters = "ABCDEFGH"
        col_numbers = range(1, 13)
        sample_idx = 0

        for row in row_letters:
            for col in col_numbers:
                well_id = f"{row}{col}"
                if well_id not in std_wells:
                    base_signal = 0.3 + (sample_idx % 8) * 0.12
                    noise = np.random.normal(0, 0.02)
                    sample_wells[well_id] = max(0.05, base_signal + noise)
                    sample_idx += 1

        return {
            "std_curve": {"wells": std_wells, "concentrations": concentrations},
            "samples": sample_wells,
        }

    @pytest.mark.asyncio
    async def test_analyze_elisa_with_realistic_data(
        self, engine: DataAnalysisEngine, mock_elisa_plate_data: dict
    ) -> None:
        """Test ELISA analysis with 96-well plate data and check concentrations."""
        with patch.object(
            engine, "load_plate_data", new_callable=AsyncMock
        ) as mock_load:
            mock_load.return_value = mock_elisa_plate_data

            result = await engine.analyze_elisa(mock_elisa_plate_data)

            assert isinstance(result, AnalysisResult)
            assert result.experiment_type == "ELISA"
            assert result.concentrations is not None
            assert len(result.concentrations) > 0

    @pytest.mark.asyncio
    async def test_4pl_curve_fitting(self, engine: DataAnalysisEngine) -> None:
        """Test 4-parameter logistic curve fitting produces r_squared > 0.95."""
        concentrations = np.array([0, 7.8125, 15.625, 31.25, 62.5, 125, 250, 500])
        signals = np.array([0.05, 0.09, 0.18, 0.34, 0.61, 0.90, 1.09, 1.20])

        fit_result = await engine.fit_4pl_curve(concentrations, signals)

        assert fit_result is not None
        assert fit_result.r_squared > 0.95
        assert fit_result.a is not None
        assert fit_result.b is not None
        assert fit_result.c is not None
        assert fit_result.d is not None

    @pytest.mark.asyncio
    async def test_run_statistical_tests(self, engine: DataAnalysisEngine) -> None:
        """Test statistical analysis on grouped data returns p_value."""
        group_a = np.array([1.2, 1.5, 1.3, 1.4, 1.6, 1.3, 1.4, 1.5])
        group_b = np.array([2.1, 2.3, 2.0, 2.2, 2.4, 2.1, 2.3, 2.2])
        group_c = np.array([1.8, 1.9, 1.7, 1.8, 2.0, 1.8, 1.9, 1.7])

        result = await engine.run_statistical_tests(
            {"Control": group_a, "Treatment1": group_b, "Treatment2": group_c},
            test_type="anova",
        )

        assert result is not None
        assert result.p_value is not None
        assert 0 <= result.p_value <= 1

    @pytest.mark.asyncio
    async def test_preprocess_removes_outliers(self, engine: DataAnalysisEngine) -> None:
        """Test that preprocessing removes outliers from data."""
        raw_data = np.array([
            1.0, 1.1, 1.2, 1.3, 1.0, 1.1,
            5.0,
            1.2, 1.1, 1.3, 1.0, 1.2,
        ])

        cleaned = await engine.preprocess_data(raw_data, remove_outliers=True)

        assert len(cleaned) < len(raw_data)
        assert 5.0 not in cleaned
        assert np.allclose(np.std(cleaned), 0.12, atol=0.05)
