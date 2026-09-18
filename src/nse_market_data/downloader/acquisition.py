"""Data acquisition orchestrator for NSE datasets."""

import logging
from typing import Dict, List, Optional

from nse_market_data.config import DATASET_CONFIGS, get_all_dataset_configs
from nse_market_data.downloader.client import NSEClient
from nse_market_data.downloader.exceptions import NSEDownloaderError
from nse_market_data.downloader.parser import parse_dataset_response
from nse_market_data.models import DatasetConfig, DatasetIdentifier, DownloadResult, DownloadStatus

logger = logging.getLogger("nse_market_data.downloader")


class NSEDataAcquisition:
    """Coordinates fetching and initial payload parsing for NSE datasets."""

    def __init__(self, client: Optional[NSEClient] = None):
        self.client = client or NSEClient()

    def acquire_dataset(self, dataset_id: DatasetIdentifier) -> DownloadResult:
        """Acquires and parses a single dataset by its identifier."""
        if dataset_id not in DATASET_CONFIGS:
            return DownloadResult(
                dataset_id=dataset_id,
                status=DownloadStatus.FAILED,
                error_message=f"Unknown dataset identifier: {dataset_id}",
            )

        config: DatasetConfig = DATASET_CONFIGS[dataset_id]
        logger.info(f"Starting acquisition for: {config.name} ({config.identifier.value})")

        try:
            payload = self.client.get_json(config.api_url)
            records, metadata = parse_dataset_response(dataset_id, payload)
            logger.info(
                f"Successfully acquired {config.name}: {len(records)} records extracted. Metadata: {metadata}"
            )
            return DownloadResult(
                dataset_id=dataset_id,
                status=DownloadStatus.SUCCESS,
                record_count=len(records),
                records=records,
            )

        except NSEDownloaderError as exc:
            logger.error(f"Acquisition failed for {config.name}: {type(exc).__name__} - {exc}")
            return DownloadResult(
                dataset_id=dataset_id,
                status=DownloadStatus.FAILED,
                error_message=f"{type(exc).__name__}: {exc}",
            )

        except Exception as exc:
            logger.error(f"Unexpected error during acquisition of {config.name}: {exc}", exc_info=True)
            return DownloadResult(
                dataset_id=dataset_id,
                status=DownloadStatus.FAILED,
                error_message=f"Unexpected error: {exc}",
            )

    def acquire_all(self) -> Dict[DatasetIdentifier, DownloadResult]:
        """Acquires all configured datasets independently with full failure isolation."""
        results: Dict[DatasetIdentifier, DownloadResult] = {}
        all_configs = get_all_dataset_configs()

        logger.info(f"Initiating batch acquisition across {len(all_configs)} datasets")

        for config in all_configs:
            result = self.acquire_dataset(config.identifier)
            results[config.identifier] = result

        successful = sum(1 for r in results.values() if r.status == DownloadStatus.SUCCESS)
        failed = sum(1 for r in results.values() if r.status == DownloadStatus.FAILED)
        logger.info(
            f"Batch acquisition completed: {successful}/{len(all_configs)} succeeded, {failed} failed."
        )

        return results

