"""
Unit tests for the NLP Intake Engine.

These tests verify the natural language processing capabilities of the
braas.pipeline.intake.nlp_engine.NLPIntakeEngine class, which parses
natural language experiment requests into structured experiment definitions.
"""

import pytest

from braas.pipeline.intake.nlp_engine import NLPIntakeEngine, ExperimentType


class TestNLPIntakeEngine:
    """Test suite for NLPIntakeEngine."""

    @pytest.fixture
    def engine(self) -> NLPIntakeEngine:
        """Create an NLPIntakeEngine instance for testing."""
        return NLPIntakeEngine()

    @pytest.mark.asyncio
    async def test_parse_elisa_request(self, engine: NLPIntakeEngine) -> None:
        """Test parsing of ELISA experiment requests."""
        request = "run an ELISA for IL-6 in human serum samples"

        result = await engine.parse_request(request)

        assert result.experiment_type == ExperimentType.ELISA
        assert result.target == "IL-6"
        assert "human" in result.organism.lower()
        assert "serum" in result.sample_type.lower()

    @pytest.mark.asyncio
    async def test_parse_qpcr_request(self, engine: NLPIntakeEngine) -> None:
        """Test parsing of qPCR experiment requests."""
        request = "perform qPCR for GAPDH gene expression in mouse liver tissue"

        result = await engine.parse_request(request)

        assert result.experiment_type == ExperimentType.QPCR
        assert result.target == "GAPDH"
        assert "mouse" in result.organism.lower()

    @pytest.mark.asyncio
    async def test_parse_cell_culture(self, engine: NLPIntakeEngine) -> None:
        """Test parsing of cell culture experiment requests."""
        request = "culture HEK293 cells in DMEM medium for 48 hours"

        result = await engine.parse_request(request)

        assert result.experiment_type == ExperimentType.CELL_CULTURE
        assert "HEK293" in result.target

    @pytest.mark.asyncio
    async def test_parse_with_organism(self, engine: NLPIntakeEngine) -> None:
        """Test that organism information is correctly extracted."""
        request = "run an ELISA for TNF-alpha in rat plasma samples"

        result = await engine.parse_request(request)

        assert result.organism == "rat"
        assert result.sample_type == "plasma"

    @pytest.mark.asyncio
    async def test_extract_entities_basic(self, engine: NLPIntakeEngine) -> None:
        """Test basic protein and gene entity extraction."""
        request = "measure IL-6 and TNF-alpha levels in human serum"

        entities = await engine.extract_entities(request)

        assert "IL-6" in entities.proteins
        assert "TNF-alpha" in entities.proteins
        assert entities.sample_type == "serum"
        assert entities.organism == "human"
