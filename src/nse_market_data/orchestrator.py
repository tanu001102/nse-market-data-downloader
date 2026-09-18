"""Application pipeline orchestrator coordinating Acquisition, Validation, and Storage."""

from dataclasses import dataclass, field
from datetime import datetime
import logging
from pathlib import Path
import time
from typing import Dict, List, Optional

from nse_market_data.config import DATASET_CONFIGS, get_all_dataset_configs, get_dataset_config
from nse_market_data.downloader.acquisition import NSEDataAcquisition
from nse_market_data.models import DatasetIdentifier, DownloadStatus
from nse_market_data.storage.csv_storage import CSVStorage
from nse_market_data.validation.validator import DataValidator

logger = logging.getLogger("nse_market_data.orchestrator")


@dataclass
class PipelineDatasetResult:
    """Detailed execution result for an individual dataset through the complete pipeline."""

    dataset_id: DatasetIdentifier
    name: str
    status: DownloadStatus
    raw_count: int = 0
    valid_count: int = 0
    duplicate_count: int = 0
    output_path: Optional[Path] = None
    is_overwrite: bool = False
    error_stage: Optional[str] = None
    error_message: Optional[str] = None
    duration_seconds: float = 0.0


@dataclass
class PipelineRunSummary:
    """Overall execution summary across all requested datasets."""

    total_attempted: int
    successful: int
    failed: int
    results: Dict[DatasetIdentifier, PipelineDatasetResult]
    start_time: datetime
    end_time: datetime
    duration_seconds: float

    @property
    def all_succeeded(self) -> bool:
        return self.failed == 0 and self.successful > 0

    def format_table(self) -> str:
        """Formats summary as a clean tabular string for console and logs."""
        lines = [
            "",
            "=" * 90,
            "                      NSE MARKET DATA DOWNLOADER — RUN SUMMARY",
            "=" * 90,
            f"Execution Period: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')} to {self.end_time.strftime('%H:%M:%S')} ({self.duration_seconds:.2f}s)",
            f"Total Datasets Attempted: {self.total_attempted} | Succeeded: {self.successful} | Failed: {self.failed}",
            "-" * 90,
            f"{'Dataset':<28} {'Status':<10} {'Raw':<6} {'Valid':<6} {'Dups':<6} {'Output File':<30}",
            "-" * 90,
        ]

        for res in self.results.values():
            filename = res.output_path.name if res.output_path else (f"[{res.error_stage} error]" if res.error_stage else "-")
            status_display = res.status.value.upper()
            lines.append(
                f"{res.name:<28} {status_display:<10} {res.raw_count:<6} {res.valid_count:<6} {res.duplicate_count:<6} {filename:<30}"
            )
            if res.status == DownloadStatus.FAILED and res.error_message:
                lines.append(f"  └── Failure ({res.error_stage}): {res.error_message}")

        lines.append("=" * 90)
        return "\n".join(lines)


class NSEPipelineOrchestrator:
    """Coordinates the end-to-end data pipeline:
    Configuration -> Acquisition -> Parsing -> Validation -> Deduplication -> Storage -> Logging
    """

    def __init__(
        self,
        acquisition: Optional[NSEDataAcquisition] = None,
        validator: Optional[DataValidator] = None,
        storage: Optional[CSVStorage] = None,
    ):
        self.acquisition = acquisition or NSEDataAcquisition()
        self.validator = validator or DataValidator()
        self.storage = storage or CSVStorage()

    def run_dataset(self, dataset_id: DatasetIdentifier) -> PipelineDatasetResult:
        """Executes the pipeline for a single dataset with stage-by-stage isolation."""
        config = get_dataset_config(dataset_id)
        start_ts = time.time()
        logger.info(f">>> Processing dataset: {config.name} ({dataset_id.value})")

        # ---------------------------------------------------------
        # STAGE 1 & 2: Acquisition & Payload Parsing
        # ---------------------------------------------------------
        acq_result = self.acquisition.acquire_dataset(dataset_id)
        if acq_result.status != DownloadStatus.SUCCESS:
            duration = time.time() - start_ts
            logger.error(f"Stage 1 (Acquisition) FAILED for {config.name}: {acq_result.error_message}")
            return PipelineDatasetResult(
                dataset_id=dataset_id,
                name=config.name,
                status=DownloadStatus.FAILED,
                error_stage="Acquisition",
                error_message=acq_result.error_message,
                duration_seconds=duration,
            )

        raw_records = acq_result.records or []
        logger.info(f"Stage 1 (Acquisition) PASSED for {config.name}: {len(raw_records)} records")

        # ---------------------------------------------------------
        # STAGE 3 & 4: Validation & Deduplication
        # ---------------------------------------------------------
        val_result = self.validator.validate(dataset_id, raw_records)
        if not val_result.is_valid:
            duration = time.time() - start_ts
            logger.error(f"Stage 2 (Validation) FAILED for {config.name}: {val_result.error_message}")
            return PipelineDatasetResult(
                dataset_id=dataset_id,
                name=config.name,
                status=DownloadStatus.FAILED,
                raw_count=val_result.original_count,
                error_stage="Validation",
                error_message=val_result.error_message,
                duration_seconds=duration,
            )

        logger.info(
            f"Stage 2 (Validation & Deduplication) PASSED for {config.name}: "
            f"{val_result.valid_count} clean records ({val_result.duplicate_count} duplicates removed)"
        )

        # ---------------------------------------------------------
        # STAGE 5: CSV Storage (with Safe Write & Overwrite Policy)
        # ---------------------------------------------------------
        try:
            store_result = self.storage.save(dataset_id, val_result.validated_records)
        except Exception as exc:
            duration = time.time() - start_ts
            logger.error(f"Stage 3 (Storage) FAILED for {config.name}: {exc}")
            return PipelineDatasetResult(
                dataset_id=dataset_id,
                name=config.name,
                status=DownloadStatus.FAILED,
                raw_count=val_result.original_count,
                valid_count=val_result.valid_count,
                duplicate_count=val_result.duplicate_count,
                error_stage="Storage",
                error_message=str(exc),
                duration_seconds=duration,
            )

        duration = time.time() - start_ts
        logger.info(
            f"Stage 3 (Storage) PASSED for {config.name}: saved to {store_result.output_path.name} "
            f"({duration:.2f}s, overwrite={store_result.is_overwrite})"
        )

        return PipelineDatasetResult(
            dataset_id=dataset_id,
            name=config.name,
            status=DownloadStatus.SUCCESS,
            raw_count=val_result.original_count,
            valid_count=val_result.valid_count,
            duplicate_count=val_result.duplicate_count,
            output_path=store_result.output_path,
            is_overwrite=store_result.is_overwrite,
            duration_seconds=duration,
        )

    def run(self, dataset_ids: Optional[List[DatasetIdentifier]] = None) -> PipelineRunSummary:
        """Executes the pipeline across requested datasets (or all 4 if None) with failure isolation."""
        targets = dataset_ids if dataset_ids is not None else [c.identifier for c in get_all_dataset_configs()]
        start_time = datetime.now()
        start_ts = time.time()
        results: Dict[DatasetIdentifier, PipelineDatasetResult] = {}

        logger.info(f"Starting NSE pipeline execution for {len(targets)} dataset(s)")

        for dataset_id in targets:
            try:
                res = self.run_dataset(dataset_id)
                results[dataset_id] = res
            except Exception as exc:
                # Top-level guard preventing one dataset exception from breaking remaining datasets
                config = get_dataset_config(dataset_id)
                logger.error(f"Unhandled pipeline error on {config.name}: {exc}", exc_info=True)
                results[dataset_id] = PipelineDatasetResult(
                    dataset_id=dataset_id,
                    name=config.name,
                    status=DownloadStatus.FAILED,
                    error_stage="Unexpected",
                    error_message=str(exc),
                )

        end_time = datetime.now()
        duration_seconds = time.time() - start_ts

        successful = sum(1 for r in results.values() if r.status == DownloadStatus.SUCCESS)
        failed = sum(1 for r in results.values() if r.status == DownloadStatus.FAILED)

        summary = PipelineRunSummary(
            total_attempted=len(targets),
            successful=successful,
            failed=failed,
            results=results,
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration_seconds,
        )

        table_output = summary.format_table()
        logger.info(table_output)
        return summary

