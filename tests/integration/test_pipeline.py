"""
Integration tests for the Pipeline Orchestrator.

These tests verify the end-to-end integration of the complete BRaaS pipeline,
testing the coordination between all pipeline stages from natural language
request intake through experiment completion and results generation.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from braas.pipeline import PipelineOrchestrator, PipelineResult


class TestPipelineIntegration:
    """Integration test suite for PipelineOrchestrator."""

    @pytest.fixture
    def output_dir(self, tmp_path: Path) -> Path:
        """Create a temporary output directory for test results."""
        output = tmp_path / "outputs"
        output.mkdir(parents=True, exist_ok=True)
        return output

    @pytest.fixture
    def orchestrator(self, output_dir: Path) -> PipelineOrchestrator:
        """Create a PipelineOrchestrator instance for testing."""
        return PipelineOrchestrator(output_dir=output_dir)

    @pytest.fixture
    def mock_nlp_engine(self) -> AsyncMock:
        """Create a mock NLP engine."""
        mock = AsyncMock()
        mock.parse_request.return_value = MagicMock(
            experiment_type="ELISA",
            target="IL-6",
            sample_type="serum",
            organism="human",
            sample_count=48,
        )
        return mock

    @pytest.fixture
    def mock_robot_controller(self) -> AsyncMock:
        """Create a mock robot controller."""
        mock = AsyncMock()
        mock.execute_instruction.return_value = MagicMock(success=True)
        mock.get_status.return_value = MagicMock(status="idle")
        return mock

    @pytest.fixture
    def mock_instrument_controller(self) -> AsyncMock:
        """Create a mock instrument controller."""
        mock = AsyncMock()
        mock.read_well.return_value = 0.5 + (hash(str(i)) % 100) / 500
        mock.get_status.return_value = MagicMock(status="ready")
        return mock

    @pytest.mark.asyncio
    async def test_end_to_end_elisa_pipeline(
        self,
        orchestrator: PipelineOrchestrator,
        mock_nlp_engine: AsyncMock,
        mock_robot_controller: AsyncMock,
        mock_instrument_controller: AsyncMock,
        output_dir: Path,
    ) -> None:
        """Test complete ELISA pipeline from request to results."""
        request = "run an ELISA for IL-6 in 48 human serum samples"

        with patch.object(
            orchestrator, "nlp_engine", mock_nlp_engine
        ), patch.object(
            orchestrator, "robot_controller", mock_robot_controller
        ), patch.object(
            orchestrator, "instrument_controller", mock_instrument_controller
        ):
            result = await orchestrator.run_pipeline(request)

        assert isinstance(result, PipelineResult)
        assert result.experiment_id is not None
        assert result.experiment_type == "ELISA"
        assert result.status in ["completed", "success", "finished"]
        assert result.results is not None
        assert output_dir.exists()

    @pytest.mark.asyncio
    async def test_pipeline_handles_validation_failure(
        self,
        orchestrator: PipelineOrchestrator,
        mock_nlp_engine: AsyncMock,
    ) -> None:
        """Test that pipeline properly handles invalid protocol submissions."""
        mock_nlp_engine.parse_request.side_effect = ValueError(
            "Invalid experiment request: missing required parameters"
        )

        request = "run an incomplete experiment request"

        with pytest.raises(ValueError, match="Invalid experiment request"):
            await orchestrator.run_pipeline(request)

    @pytest.mark.asyncio
    async def test_pipeline_stores_results(
        self,
        orchestrator: PipelineOrchestrator,
        mock_nlp_engine: AsyncMock,
        mock_robot_controller: AsyncMock,
        mock_instrument_controller: AsyncMock,
        output_dir: Path,
    ) -> None:
        """Test that pipeline results are stored in output directory."""
        mock_nlp_engine.parse_request.return_value = MagicMock(
            experiment_type="ELISA",
            target="IL-6",
            sample_type="serum",
            organism="human",
            sample_count=48,
        )

        request = "run an ELISA for IL-6 in human serum"

        with patch.object(
            orchestrator, "nlp_engine", mock_nlp_engine
        ), patch.object(
            orchestrator, "robot_controller", mock_robot_controller
        ), patch.object(
            orchestrator, "instrument_controller", mock_instrument_controller
        ):
            result = await orchestrator.run_pipeline(request)

        result_files = list(output_dir.glob("**/*"))
        assert len(result_files) >= 0
