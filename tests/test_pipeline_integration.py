"""Integration tests verifying the complete flow: Acquisition -> Validation -> Deduplication -> CSV Storage."""

import csv
from datetime import date
from unittest.mock import MagicMock

import pytest

from nse_market_data.downloader.acquisition import NSEDataAcquisition
from nse_market_data.downloader.client import NSEClient
from nse_market_data.models import DatasetIdentifier, DownloadStatus
from nse_market_data.storage.csv_storage import CSVStorage
from nse_market_data.validation.validator import DataValidator


@pytest.fixture
def mock_nse_client():
    """Returns an NSEClient mock pre-populated with data for all 4 endpoints, including duplicates."""
    client = MagicMock(spec=NSEClient)

    mock_responses = {
        "live-analysis-variations": {
            "NIFTY": {
                "data": [
                    {"symbol": "ADANIPORTS", "series": "EQ", "open_price": 1748, "high_price": 1824, "low_price": 1744, "ltp": 1824, "prev_price": 1738.3, "perChange": 4.93, "trade_quantity": 4148803, "turnover": 74138.69},
                    {"symbol": "BHARTIARTL", "series": "EQ", "open_price": 1843, "high_price": 1893, "low_price": 1835, "ltp": 1893, "prev_price": 1836.0, "perChange": 3.12, "trade_quantity": 1418978, "turnover": 26592.92},
                    {"symbol": "ADANIPORTS", "series": "EQ", "open_price": 1748, "high_price": 1824, "low_price": 1744, "ltp": 1824, "prev_price": 1738.3, "perChange": 4.93, "trade_quantity": 4148803, "turnover": 74138.69}, # Duplicate
                ]
            }
        },
        "live-analysis-price-band-hitter": {
            "upper": {
                "AllSec": {
                    "data": [
                        {"symbol": "EMCURE", "series": "EQ", "ltp": "2083", "change": "173.2", "pChange": "9.07", "priceBand": "10", "totalTradedVol": 17.4, "turnover": 349.0},
                        {"symbol": "TBZ", "series": "EQ", "ltp": "603.55", "change": "28.7", "pChange": "4.99", "priceBand": "5", "totalTradedVol": 14.3, "turnover": 86.4},
                    ]
                }
            }
        },
        "live-analysis-volume-gainers": {
            "data": [
                {"symbol": "NIFTYBETA", "companyName": "UTI Nifty 50 ETF", "volume": 2607269, "week1AvgVolume": 31044, "week1volChange": 83.9, "week2AvgVolume": 35029, "week2volChange": 74.4, "ltp": 261.99, "pChange": 1.19, "turnover": 6761.1},
                {"symbol": "ATGL", "companyName": "Adani Total Gas Limited", "volume": 39305845, "week1AvgVolume": 525614, "week1volChange": 74.7, "week2AvgVolume": 530622, "week2volChange": 74.0, "ltp": 657.6, "pChange": 12.03, "turnover": 25650.9},
            ]
        },
        "live-analysis-data-52weekhighstock": {
            "data": [
                {"symbol": "AAREYDRUGS", "series": "EQ", "ltp": 101, "new52WHL": 103.5, "prev52WHL": 102.96, "prevHLDate": "17-Sep-2026", "change": -0.72, "pChange": -0.71},
                {"symbol": "ACE", "series": "EQ", "ltp": 1229.1, "new52WHL": 1241.5, "prev52WHL": 1213.2, "prevHLDate": "17-Sep-2026", "change": 23.5, "pChange": 1.95},
            ]
        },
    }

    def side_effect(url, headers=None):
        for key, payload in mock_responses.items():
            if key in url:
                return payload
        raise ValueError(f"Unexpected URL: {url}")

    client.get_json.side_effect = side_effect
    return client


def test_pipeline_all_four_datasets_e2e(mock_nse_client, tmp_path):
    """Verifies complete end-to-end pipeline across all 4 datasets:
    Acquisition -> Validation -> Deduplication -> CSV Storage.
    """
    acquisition = NSEDataAcquisition(client=mock_nse_client)
    validator = DataValidator()
    storage = CSVStorage(base_output_dir=tmp_path)
    test_date = date(2026, 9, 18)

    # 1. Acquire
    acq_results = acquisition.acquire_all()
    assert len(acq_results) == 4

    saved_files = []

    # 2. Validate, Deduplicate, Store
    for dataset_id, acq_res in acq_results.items():
        assert acq_res.status == DownloadStatus.SUCCESS
        assert acq_res.records is not None

        # Validation & Deduplication
        val_res = validator.validate(dataset_id, acq_res.records)
        assert val_res.is_valid is True

        # Special check: top-gainers had 3 records with 1 duplicate -> 2 clean records
        if dataset_id == DatasetIdentifier.TOP_GAINERS_LOSERS:
            assert val_res.original_count == 3
            assert val_res.valid_count == 2
            assert val_res.duplicate_count == 1

        # Storage
        store_res = storage.save(dataset_id, val_res.validated_records, run_date=test_date)
        assert store_res.status == DownloadStatus.SUCCESS
        assert store_res.output_path.exists()
        saved_files.append(store_res.output_path)

        # Verify CSV contents on disk
        with open(store_res.output_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == val_res.valid_count
            assert "SYMBOL" in reader.fieldnames

    assert len(saved_files) == 4


def test_four_dataset_failure_isolation_end_to_end(mock_nse_client, tmp_path):
    """Explicitly tests assignment requirement:
    Dataset A -> SUCCESS
    Dataset B -> FAILS
    Dataset C -> SUCCESS
    Dataset D -> SUCCESS

    Verifies that failure of Dataset B (Upper Band Hitters) does not stop C and D,
    that A, C, D are saved as CSVs, and that the summary captures both.
    """
    from unittest.mock import patch
    from nse_market_data.downloader.exceptions import NSEHTTPError
    from nse_market_data.orchestrator import NSEPipelineOrchestrator

    original_side_effect = mock_nse_client.get_json.side_effect

    def failing_side_effect(url, headers=None):
        if "live-analysis-price-band-hitter" in url:
            raise NSEHTTPError("HTTP 503 Service Unavailable", status_code=503)
        return original_side_effect(url, headers=headers)

    mock_nse_client.get_json.side_effect = failing_side_effect

    acquisition = NSEDataAcquisition(client=mock_nse_client)
    validator = DataValidator()
    storage = CSVStorage(base_output_dir=tmp_path)
    orchestrator = NSEPipelineOrchestrator(
        acquisition=acquisition,
        validator=validator,
        storage=storage,
    )

    summary = orchestrator.run()

    assert summary.total_attempted == 4
    assert summary.successful == 3
    assert summary.failed == 1
    assert summary.all_succeeded is False

    # Check that A (top-gainers), C (volume-gainers), D (52-week-high) are saved
    today_str = date.today().strftime("%Y-%m-%d")
    top_file = tmp_path / "top_gainers_losers" / f"top_gainers_losers_{today_str}.csv"
    upper_dir = tmp_path / "upper_band_hitters"
    vol_file = tmp_path / "volume_gainers_spurts" / f"volume_gainers_spurts_{today_str}.csv"
    high_file = tmp_path / "52_week_high" / f"52_week_high_{today_str}.csv"

    assert top_file.exists()
    assert vol_file.exists()
    assert high_file.exists()

    # Upper band file should NOT exist because it failed
    if upper_dir.exists():
        assert len(list(upper_dir.glob("*.csv"))) == 0

    # Upper band result captures the failure
    upper_res = summary.results[DatasetIdentifier.UPPER_BAND_HITTERS]
    assert upper_res.status == DownloadStatus.FAILED
    assert upper_res.error_stage == "Acquisition"
    assert "503" in upper_res.error_message


def test_cli_full_run_with_custom_output_dir(mock_nse_client, tmp_path):
    """Tests full CLI execution with mocked network writing to custom --output-dir."""
    from main import run_cli
    from unittest.mock import patch
    with patch("nse_market_data.downloader.acquisition.NSEClient", return_value=mock_nse_client):
        exit_code = run_cli(["--output-dir", str(tmp_path)])
        assert exit_code == 0
        csv_files = list(tmp_path.glob("*/*.csv"))
        assert len(csv_files) == 4

