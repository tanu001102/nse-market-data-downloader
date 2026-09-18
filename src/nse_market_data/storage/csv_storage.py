"""CSV Storage module for persisting validated market datasets safely and deterministically."""

import csv
from datetime import date, datetime
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from nse_market_data.config import get_dataset_config, get_output_dir
from nse_market_data.models import DatasetConfig, DatasetIdentifier, DownloadStatus, StorageResult
from nse_market_data.storage.exceptions import (
    StorageDirectoryError,
    StorageError,
    StorageWriteError,
)

logger = logging.getLogger("nse_market_data.storage")


class CSVStorage:
    """Manages writing validated records to organized CSV files on disk using atomic
    write patterns and a deterministic same-day overwrite/update policy.
    """

    def __init__(self, base_output_dir: Optional[Path] = None):
        self.base_output_dir = Path(base_output_dir) if base_output_dir else get_output_dir()

    def generate_filename(self, config: DatasetConfig, run_date: date) -> str:
        """Generates deterministic filename: <prefix>_YYYY-MM-DD.csv"""
        date_str = run_date.strftime("%Y-%m-%d")
        return f"{config.filename_prefix}_{date_str}.csv"

    def get_dataset_dir(self, config: DatasetConfig) -> Path:
        """Determines the subdirectory for the dataset: <base>/<output_subdir>"""
        return self.base_output_dir / config.output_subdir

    def save(
        self,
        dataset_id: DatasetIdentifier,
        records: List[Dict[str, Any]],
        run_date: Optional[date] = None,
    ) -> StorageResult:
        """Persists validated records into a CSV file.

        Duplicate file policy:
        If a CSV file already exists for the given dataset and date, it is
        atomically replaced with the fresh validated dataset to prevent
        spurious duplicate files (e.g. data_1.csv).
        """
        config = get_dataset_config(dataset_id)
        effective_date = run_date or datetime.now().date()
        target_dir = self.get_dataset_dir(config)
        filename = self.generate_filename(config, effective_date)
        target_path = target_dir / filename

        # 1. Ensure target directory exists
        try:
            target_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            msg = f"Failed to create target directory '{target_dir}': {exc}"
            logger.error(msg)
            raise StorageDirectoryError(msg) from exc

        is_overwrite = target_path.exists()
        if is_overwrite:
            logger.info(
                f"Existing file found for same date at '{target_path}'. Enforcing overwrite/update policy."
            )

        # 2. Determine CSV fieldnames and transform records according to column_mapping
        column_mapping = config.column_mapping
        if column_mapping:
            fieldnames = list(column_mapping.values())
        elif records:
            fieldnames = list(records[0].keys())
        else:
            fieldnames = []

        # 3. Write atomically via a temporary file
        temp_filename = f".{filename}.tmp"
        temp_path = target_dir / temp_filename

        try:
            logger.info(f"Writing {len(records)} records to temporary file '{temp_path}'")
            with open(temp_path, mode="w", newline="", encoding="utf-8") as csv_file:
                writer = csv.DictWriter(
                    csv_file,
                    fieldnames=fieldnames,
                    extrasaction="ignore",
                    lineterminator="\n",
                )
                writer.writeheader()

                for item in records:
                    if column_mapping:
                        # Map raw API keys to standardized CSV headers
                        row_dict = {
                            header: item.get(raw_key, "")
                            for raw_key, header in column_mapping.items()
                        }
                    else:
                        row_dict = item
                    writer.writerow(row_dict)

            # 4. Atomic file replacement (Windows & POSIX safe)
            os.replace(temp_path, target_path)
            action = "Overwrote existing" if is_overwrite else "Created new"
            logger.info(f"{action} CSV file successfully: '{target_path}' ({len(records)} records)")

            return StorageResult(
                dataset_id=dataset_id,
                output_path=target_path,
                record_count=len(records),
                is_overwrite=is_overwrite,
                status=DownloadStatus.SUCCESS,
            )

        except OSError as exc:
            # Clean up temporary file on failure
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass
            msg = f"Failed writing CSV storage file '{target_path}': {exc}"
            logger.error(msg)
            raise StorageWriteError(msg) from exc

        except Exception as exc:
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass
            msg = f"Unexpected error while writing CSV for {config.name}: {exc}"
            logger.error(msg)
            raise StorageError(msg) from exc

