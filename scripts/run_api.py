#!/usr/bin/env python3
"""
BRaaS API Server CLI Entry Point

This script starts the FastAPI server for the BRaaS Bio Research-as-a-Service
platform, enabling REST API access to the pipeline capabilities.

Usage:
    python scripts/run_api.py --host 0.0.0.0 --port 8000
"""

import argparse
import uvicorn


def main() -> None:
    """Main entry point for the API server."""
    parser = argparse.ArgumentParser(
        description="BRaaS - Bio Research-as-a-Service API Server",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host address to bind the server to",
    )

    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port number to bind the server to",
    )

    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable automatic code reloading during development",
    )

    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of worker processes",
    )

    parser.add_argument(
        "--log-level",
        type=str,
        default="info",
        choices=["debug", "info", "warning", "error", "critical"],
        help="Logging level",
    )

    args = parser.parse_args()

    uvicorn.run(
        "braas.api.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers,
        log_level=args.log_level,
    )


if __name__ == "__main__":
    main()
