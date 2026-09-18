"""Unit tests for the Application Orchestrator and CLI."""

from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from nse_market_data.downloader.acquisition import NSEDataAcquisition
from nse_market_data.models import (
    DatasetIdentifier,
    DownloadResult,
    DownloadStatus,
    StorageResult,
    ValidationResult,
)
from nse_market_data.orchestrator import NSEPipelineOrchestrator, PipelineRunSummary
from nse_market_data.storage.csv_storage import CSVStorage
from nse_market_data.validation.validator import DataValidator


@pytest.fixture
def mock_acquisition():
    mock = MagicMock(spec=NSEDataAcquisition)
    # Default: returns successful acquisition with 2 sample records
    def default_acquire(dataset_id):
        return DownloadResult(
            dataset_id=dataset_id,
            status=DownloadStatus.SUCCESS,
            record_count=2,
            records=[
                {"symbol": "INFY", "series": "EQ", "ltp": 1500, "perChange": 2.0, "open_price": 1490, "high_price": 1510, "low_price": 1485, "prev_price": 1470},
                {"symbol": "TCS", "series": "EQ", "ltp": 3500, "perChange": 1.5, "open_price": 3490, "high_price": 3520, "low_price": 3480, "prev_price": 3450},
            ],
        )
    mock.acquire_dataset.side_effect = default_acquire
    return mock


@pytest.fixture
def mock_validator():
    mock = MagicMock(spec=DataValidator)
    # Default: returns valid with 2 records
    def default_validate(dataset_id, records):
        return ValidationResult(
            dataset_id=dataset_id,
            is_valid=True,
            original_count=len(records),
            valid_count=len(records),
            duplicate_count=0,
            validated_records=records,
        )
    mock.validate.side_effect = default_validate
    return mock


@pytest.fixture
def mock_storage(tmp_path):
    mock = MagicMock(spec=CSVStorage)
    def default_save(dataset_id, records, run_date=None):
        out_file = tmp_path / f"{dataset_id.value}.csv"
        out_file.touch()
        return StorageResult(
            dataset_id=dataset_id,
            output_path=out_file,
            record_count=len(records),
            is_overwrite=False,
            status=DownloadStatus.SUCCESS,
        )
    mock.save.side_effect = default_save
    return mock


@pytest.fixture
def orchestrator(mock_acquisition, mock_validator, mock_storage):
    return NSEPipelineOrchestrator(
        acquisition=mock_acquisition,
        validator=mock_validator,
        storage=mock_storage,
    )


# ---------------------------------------------------------------------------
# Orchestrator Workflow Tests
# ---------------------------------------------------------------------------


def test_orchestrator_all_four_datasets_success(orchestrator):
    """1, 4. All four datasets selected and completed successfully."""
    summary = orchestrator.run()

    assert summary.total_attempted == 4
    assert summary.successful == 4
    assert summary.failed == 0
    assert summary.all_succeeded is True
    assert len(summary.results) == 4

    for res in summary.results.values():
        assert res.status == DownloadStatus.SUCCESS
        assert res.output_path is not None
        assert res.valid_count == 2
        assert res.error_stage is None


def test_orchestrator_single_dataset(orchestrator):
    """2. Single dataset selected and executed."""
    summary = orchestrator.run([DatasetIdentifier.TOP_GAINERS_LOSERS])

    assert summary.total_attempted == 1
    assert summary.successful == 1
    assert summary.failed == 0
    assert DatasetIdentifier.TOP_GAINERS_LOSERS in summary.results


def test_failure_isolation_acquisition(orchestrator, mock_acquisition):
    """5, 6. One dataset fails during acquisition; remaining 3 datasets continue and succeed."""
    def acquire_with_failure(dataset_id):
        if dataset_id == DatasetIdentifier.UPPER_BAND_HITTERS:
            return DownloadResult(
                dataset_id=dataset_id,
                status=DownloadStatus.FAILED,
                error_message="Simulated HTTP 503 Service Unavailable",
            )
        return DownloadResult(
            dataset_id=dataset_id,
            status=DownloadStatus.SUCCESS,
            record_count=1,
            records=[{"symbol": "TEST"}],
        )

    mock_acquisition.acquire_dataset.side_effect = acquire_with_failure

    summary = orchestrator.run()

    assert summary.total_attempted == 4
    assert summary.successful == 3
    assert summary.failed == 1
    assert summary.all_succeeded is False

    # Upper band hitters failed at Acquisition stage
    upper_band_res = summary.results[DatasetIdentifier.UPPER_BAND_HITTERS]
    assert upper_band_res.status == DownloadStatus.FAILED
    assert upper_band_res.error_stage == "Acquisition"
    assert "503" in upper_band_res.error_message

    # Other 3 datasets succeeded
    assert summary.results[DatasetIdentifier.TOP_GAINERS_LOSERS].status == DownloadStatus.SUCCESS
    assert summary.results[DatasetIdentifier.VOLUME_GAINERS_SPURTS].status == DownloadStatus.SUCCESS
    assert summary.results[DatasetIdentifier.FIFTY_TWO_WEEK_HIGH].status == DownloadStatus.SUCCESS


def test_validation_failure_prevents_storage(orchestrator, mock_validator, mock_storage):
    """7. Validation failure marks dataset as failed and prevents invalid CSV storage."""
    def validate_with_failure(dataset_id, records):
        if dataset_id == DatasetIdentifier.VOLUME_GAINERS_SPURTS:
            return ValidationResult(
                dataset_id=dataset_id,
                is_valid=False,
                error_message="Missing required column(s): TODAY_VOLUME",
            )
        return ValidationResult(
            dataset_id=dataset_id,
            is_valid=True,
            original_count=len(records),
            valid_count=len(records),
            duplicate_count=0,
            validated_records=records,
        )

    mock_validator.validate.side_effect = validate_with_failure

    summary = orchestrator.run()

    assert summary.successful == 3
    assert summary.failed == 1

    vol_res = summary.results[DatasetIdentifier.VOLUME_GAINERS_SPURTS]
    assert vol_res.status == DownloadStatus.FAILED
    assert vol_res.error_stage == "Validation"
    assert "Missing required column" in vol_res.error_message

    # Check that storage.save was never called for VOLUME_GAINERS_SPURTS
    called_dataset_ids = [call.args[0] for call in mock_storage.save.call_args_list]
    assert DatasetIdentifier.VOLUME_GAINERS_SPURTS not in called_dataset_ids


def test_storage_failure_reported(orchestrator, mock_storage):
    """8. Storage write failure is captured and isolated."""
    mock_storage.save.side_effect = OSError("Disk full")

    summary = orchestrator.run([DatasetIdentifier.TOP_GAINERS_LOSERS])

    assert summary.successful == 0
    assert summary.failed == 1
    res = summary.results[DatasetIdentifier.TOP_GAINERS_LOSERS]
    assert res.status == DownloadStatus.FAILED
    assert res.error_stage == "Storage"
    assert "Disk full" in res.error_message


def test_summary_table_formatting(orchestrator):
    """9. Formatted summary table is generated with record counts and status."""
    summary = orchestrator.run()
    table = summary.format_table()

    assert "RUN SUMMARY" in table
    assert "Total Datasets Attempted: 4"
    assert "top-gainers-losers" in table or "Top Gainers / Losers" in table
    assert "SUCCESS" in table


# ---------------------------------------------------------------------------
# CLI Invocation Tests
# ---------------------------------------------------------------------------


def test_cli_help_flag():
    """CLI --help flag exits cleanly."""
    from main import run_cli
    with pytest.raises(SystemExit) as exc_info:
        run_cli(["--help"])
    assert exc_info.value.code == 0


def test_cli_list_datasets():
    """CLI --list-datasets prints available datasets and exits with 0."""
    from main import run_cli
    exit_code = run_cli(["--list-datasets"])
    assert exit_code == 0


def test_cli_invalid_dataset():
    """CLI with invalid dataset name returns exit code 2."""
    from main import run_cli
    exit_code = run_cli(["--dataset", "non_existent_dataset"])
    assert exit_code == 2


def test_cli_alias_resolution(tmp_path):
    """CLI accepts 52-week-high-equity-market alias and maps it properly."""
    from main import run_cli
    with patch("main.NSEPipelineOrchestrator.run") as mock_run:
        mock_summary = MagicMock(spec=PipelineRunSummary)
        mock_summary.all_succeeded = True
        mock_summary.format_table.return_value = "Summary Table"
        mock_run.return_value = mock_summary

        exit_code = run_cli(["--dataset", "52-week-high-equity-market", "--output-dir", str(tmp_path)])
        assert exit_code == 0
        mock_run.assert_called_once_with(dataset_ids=[DatasetIdentifier.FIFTY_TWO_WEEK_HIGH])

