"""Main command-line entry point for the NSE Market Data Downloader."""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

# Ensure src/ is accessible on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from nse_market_data.config import (
    DATASET_CONFIGS,
    get_all_dataset_configs,
    get_output_dir,
    get_valid_cli_choices,
    resolve_dataset_identifier,
)
from nse_market_data.models import DatasetIdentifier
from nse_market_data.orchestrator import NSEPipelineOrchestrator
from nse_market_data.storage.csv_storage import CSVStorage
from nse_market_data.utils.logger import setup_logger


def build_parser() -> argparse.ArgumentParser:
    """Builds and returns the command-line argument parser."""
    valid_choices = get_valid_cli_choices()
    parser = argparse.ArgumentParser(
        prog="python main.py",
        description="NSE Market Data Downloader — Automated retrieval, validation, and storage of NSE market data.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                                  # Download and store all 4 datasets
  python main.py --dataset top-gainers-losers     # Download individual dataset
  python main.py --dataset 52-week-high           # Download 52-week-high dataset
  python main.py --output-dir /path/to/data       # Store files in custom directory
  python main.py --list-datasets                  # List all available datasets and URLs
        """,
    )
    parser.add_argument(
        "--dataset",
        "-d",
        type=str,
        default=None,
        metavar="DATASET",
        help=f"Specific dataset to download. Valid choices: {', '.join(valid_choices)}",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        type=Path,
        default=None,
        metavar="PATH",
        help="Custom root directory where CSV datasets will be organized (defaults to data/output).",
    )
    parser.add_argument(
        "--list-datasets",
        action="store_true",
        help="Display all configured datasets, target URLs, and exit.",
    )
    return parser


def run_cli(args: Optional[List[str]] = None) -> int:
    """CLI execution wrapper returning integer exit code."""
    parser = build_parser()
    parsed_args = parser.parse_args(args)
    logger = setup_logger()

    if parsed_args.list_datasets:
        print("\nConfigured NSE Datasets:")
        print("-" * 80)
        for cfg in get_all_dataset_configs():
            print(f"Identifier:    {cfg.identifier.value}")
            print(f"Name:          {cfg.name}")
            print(f"Page URL:      {cfg.page_url}")
            print(f"API URL:       {cfg.api_url}")
            print(f"Subdirectory:  {cfg.output_subdir}")
            print("-" * 80)
        return 0

    # 1. Resolve dataset selection
    target_datasets: Optional[List[DatasetIdentifier]] = None
    if parsed_args.dataset:
        try:
            resolved_id = resolve_dataset_identifier(parsed_args.dataset)
            target_datasets = [resolved_id]
        except ValueError as exc:
            logger.error(str(exc))
            print(f"Error: {exc}", file=sys.stderr)
            return 2

    # 2. Configure output storage
    output_dir = get_output_dir(parsed_args.output_dir)
    storage = CSVStorage(base_output_dir=output_dir)
    orchestrator = NSEPipelineOrchestrator(storage=storage)

    mode = f"Individual [{target_datasets[0].value}]" if target_datasets else "Batch [All 4 datasets]"
    logger.info(f"NSE Downloader CLI started in mode: {mode}")
    logger.info(f"Effective Output Directory: {output_dir}")

    # 3. Execute pipeline
    try:
        summary = orchestrator.run(dataset_ids=target_datasets)
    except Exception as exc:
        logger.critical(f"Critical execution error: {exc}", exc_info=True)
        print(f"Critical error: {exc}", file=sys.stderr)
        return 1

    # 4. Return exit code (0 if all succeeded, 1 if any failed)
    print(summary.format_table())
    if summary.all_succeeded:
        logger.info("Pipeline execution completed successfully for all requested datasets.")
        return 0
    else:
        logger.warning(
            f"Pipeline execution completed with failures: {summary.failed}/{summary.total_attempted} failed."
        )
        return 1


def main() -> int:
    """Standard application entry point."""
    return run_cli(sys.argv[1:])


if __name__ == "__main__":
    sys.exit(main())
