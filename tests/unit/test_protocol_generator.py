"""
Unit tests for the Protocol Generator.

These tests verify the protocol design and generation capabilities of the
braas.pipeline.protocol_design.generator.ProtocolGenerator class, which
creates detailed experimental protocols from structured experiment definitions.
"""

import pytest

from braas.pipeline.protocol_design.generator import (
    ProtocolGenerator,
    Protocol,
    RobotInstruction,
)


class TestProtocolGenerator:
    """Test suite for ProtocolGenerator."""

    @pytest.fixture
    def generator(self) -> ProtocolGenerator:
        """Create a ProtocolGenerator instance for testing."""
        return ProtocolGenerator()

    @pytest.mark.asyncio
    async def test_generate_elisa_protocol(
        self, generator: ProtocolGenerator
    ) -> None:
        """Test that ELISA protocol generation returns a Protocol with steps."""
        experiment_config = {
            "experiment_type": "ELISA",
            "target": "IL-6",
            "sample_count": 48,
            "sample_type": "serum",
            "organism": "human",
        }

        protocol = await generator.generate_protocol(experiment_config)

        assert isinstance(protocol, Protocol)
        assert protocol.experiment_type == "ELISA"
        assert len(protocol.steps) > 0
        assert any("coat" in step.description.lower() for step in protocol.steps)

    @pytest.mark.asyncio
    async def test_protocol_has_required_sections(
        self, generator: ProtocolGenerator
    ) -> None:
        """Test that generated protocols contain all required sections."""
        experiment_config = {
            "experiment_type": "ELISA",
            "target": "IL-6",
            "sample_count": 96,
            "sample_type": "plasma",
            "organism": "mouse",
        }

        protocol = await generator.generate_protocol(experiment_config)

        assert protocol.title is not None
        assert protocol.version is not None
        assert protocol.steps is not None
        assert len(protocol.steps) > 0
        assert protocol.materials is not None
        assert protocol.safety_notes is not None
        assert protocol.quality_control is not None

    @pytest.mark.asyncio
    async def test_optimize_parameters(
        self, generator: ProtocolGenerator
    ) -> None:
        """Test that parameter optimization returns optimized values."""
        base_config = {
            "experiment_type": "ELISA",
            "target": "IL-6",
            "sample_count": 48,
        }

        optimized = await generator.optimize_parameters(base_config)

        assert optimized is not None
        assert "incubation_time" in optimized
        assert "temperature" in optimized
        assert " antibody_dilution" in optimized

    @pytest.mark.asyncio
    async def test_compile_to_robot_instructions(
        self, generator: ProtocolGenerator
    ) -> None:
        """Test that protocols can be compiled to robot instructions."""
        experiment_config = {
            "experiment_type": "ELISA",
            "target": "IL-6",
            "sample_count": 48,
            "sample_type": "serum",
            "organism": "human",
        }

        protocol = await generator.generate_protocol(experiment_config)
        instructions = await generator.compile_to_robot_instructions(protocol)

        assert isinstance(instructions, list)
        assert len(instructions) > 0
        assert all(
            isinstance(inst, RobotInstruction) for inst in instructions
        )
        assert all(inst.step_number is not None for inst in instructions)
