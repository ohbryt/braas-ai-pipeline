#!/usr/bin/env python3
"""
BRaaS Pipeline CLI Entry Point

This script provides a command-line interface to run the full BRaaS AI pipeline
for automated biological research experiments.

Usage:
    python scripts/run_pipeline.py "run an ELISA for IL-6 in 48 mouse serum samples" --output-dir outputs/
"""

import argparse
import asyncio
import sys
from pathlib import Path

import structlog

from braas.pipeline import PipelineOrchestrator

logger = structlog.get_logger()


async def run_pipeline(request: str, output_dir: Path) -> None:
    """
    Execute the full BRaaS pipeline for a given research request.

    Args:
        request: Natural language description of the experiment to run.
        output_dir: Directory to store pipeline outputs and results.
    """
    logger.info(
        "Starting BRaaS pipeline",
        request=request,
        output_dir=str(output_dir),
    )

    orchestrator = PipelineOrchestrator(output_dir=output_dir)

    try:
        result = await orchestrator.run_experiment(request)

        logger.info(
            "Pipeline completed successfully",
            experiment_id=result.experiment_id,
            experiment_type=result.experiment_type,
            status=result.status,
        )

        print("\n" + "=" * 60)
        print("PIPELINE EXECUTION COMPLETE")
        print("=" * 60)
        print(f"Experiment ID: {result.experiment_id}")
        print(f"Experiment Type: {result.experiment_type}")
        print(f"Status: {result.status}")
        print(f"Output Directory: {output_dir}")
        print("=" * 60)

        if result.results:
            print("\nResults Summary:")
            for key, value in result.results.items():
                print(f"  {key}: {value}")

    except Exception as e:
        logger.error("Pipeline execution failed", error=str(e))
        print(f"\nERROR: Pipeline execution failed: {e}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    """Main entry point for the pipeline CLI."""
    parser = argparse.ArgumentParser(
        description="BRaaS - Bio Research-as-a-Service AI Pipeline CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/run_pipeline.py "run an ELISA for IL-6 in 48 mouse serum samples"
  python scripts/run_pipeline.py "perform qPCR for GAPDH in human blood" --output-dir ./results
        """,
    )

    parser.add_argument(
        "request",
        type=str,
        help="Natural language description of the experiment to run",
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs"),
        help="Directory to store pipeline outputs (default: outputs/)",
    )

    args = parser.parse_args()

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    asyncio.run(run_pipeline(args.request, output_dir))


if __name__ == "__main__":
    main()
