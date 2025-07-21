"""
This module handles command-line argument parsing and logging setup for the email checker tool.

Features:
- Parses arguments for:
    • Input file containing emails to check
    • Number of concurrent worker threads
    • Number of emails each worker processes per session before rotating
    • Logging verbosity level
    • Optional output JSON file path for saving results

- Configures logging with timestamp, thread name, and log level for consistent and informative output.
"""

import argparse
import logging
from pathlib import Path


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Check GitHub email registration using rotating proxies"
    )
    ap.add_argument("file", type=Path, help="Path to file with email addresses")
    ap.add_argument(
        "-w",
        "--workers",
        type=int,
        default=10,
        help="Maximum concurrent worker threads (default: 10)",
    )
    ap.add_argument(
        "-n",
        "--emails-per-worker",
        type=int,
        default=3,
        help="How many POST checks each worker performs before recycling (default: 3)",
    )
    ap.add_argument(
        "-v",
        "--verbosity",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level (default: INFO)",
    )
    ap.add_argument(
        "-o", "--output",
        nargs="?",                     # makes it optional but still accepts a value
        const="results.json",          # default if -o is passed without value
        type=Path,
        help="Optional path to save JSON results (default: results.json if -o is passed)"
    )

    return ap.parse_args()


def setup_logging(level_str: str) -> None:
    level = getattr(logging, level_str.upper(), logging.INFO)
    logging.basicConfig(
        level=level, format="%(asctime)s - %(threadName)s - %(levelname)s - %(message)s"
    )