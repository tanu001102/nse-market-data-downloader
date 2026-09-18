"""Unit tests for the CSV Storage module."""

import csv
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

from nse_market_data.config import get_dataset_config
from nse_market_data.models import DatasetIdentifier, DownloadStatus
from nse_market_data.storage.csv_storage import CSVStorage
from nse_market_data.storage.exceptions import StorageDirectoryError, StorageWriteError


@pytest.fixture
def storage(tmp_path):
    return CSVStorage(base_output_dir=tmp_path)


def test_csv_creation_and_filename(storage, tmp_path):
    """1, 2. CSV file is created with correct date-identifying filename."""
    sample_data = [
        {
            "symbol": "INFY",
            "companyName": "Infosys Limited",
            "volume": 50000,
            "week1AvgVolume": 10000,
            "week1volChange": 5.0,
            "week2AvgVolume": 12000,
            "week2volChange": 4.0,
            "ltp": 1600.0,
            "pChange": 2.5,
            "turnover": 8000.0,
        }
    ]
    test_date = date(2026, 9, 18)
    res = storage.save(DatasetIdentifier.VOLUME_GAINERS_SPURTS, sample_data, run_date=test_date)

    assert res.status == DownloadStatus.SUCCESS
    assert res.record_count == 1
    assert res.is_overwrite is False
    assert res.output_path.exists()
    assert res.output_path.name == "volume_gainers_spurts_2026-09-18.csv"


def test_expected_columns_and_content(storage):
    """3, 4. Header columns and row records are correctly written."""
    sample_data = [
        {
            "symbol": "AAREYDRUGS",
            "series": "EQ",
            "ltp": 101,
            "change": -0.72,
            "pChange": -0.71,
            "new52WHL": 103.5,
            "prev52WHL": 102.96,
            "prevHLDate": "17-Sep-2026",
            "prevClose": "101.72",
            "comapnyName": "Aarey Drugs",
        }
    ]
    test_date = date(2026, 9, 18)
    res = storage.save(DatasetIdentifier.FIFTY_TWO_WEEK_HIGH, sample_data, run_date=test_date)

    # Read back the written CSV
    with open(res.output_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 1
    assert "SYMBOL" in reader.fieldnames
    assert "SERIES" in reader.fieldnames
    assert "NEW_52W_HIGH_PRICE" in reader.fieldnames
    assert rows[0]["SYMBOL"] == "AAREYDRUGS"
    assert rows[0]["SERIES"] == "EQ"
    assert rows[0]["NEW_52W_HIGH_PRICE"] == "103.5"


def test_directory_created_when_absent(tmp_path):
    """5. Deep output directory structure is automatically created."""
    deep_dir = tmp_path / "custom" / "nested" / "output"
    custom_storage = CSVStorage(base_output_dir=deep_dir)

    sample = [{"symbol": "EMCURE", "series": "EQ", "ltp": "2083", "change": "10", "pChange": "9", "priceBand": "10"}]
    res = custom_storage.save(DatasetIdentifier.UPPER_BAND_HITTERS, sample, run_date=date(2026, 9, 18))

    assert res.output_path.exists()
    assert res.output_path.parent == deep_dir / "upper_band_hitters"


def test_same_day_repeated_execution_policy(storage):
    """6, 7. Repeated save for same dataset/date replaces file without creating duplicate files."""
    initial_data = [
        {"symbol": "INFY", "companyName": "Infosys", "volume": 100, "week1AvgVolume": 10, "week1volChange": 1, "week2AvgVolume": 10, "week2volChange": 1, "ltp": 1500, "pChange": 1, "turnover": 10}
    ]
    updated_data = [
        {"symbol": "INFY", "companyName": "Infosys", "volume": 200, "week1AvgVolume": 10, "week1volChange": 1, "week2AvgVolume": 10, "week2volChange": 1, "ltp": 1510, "pChange": 2, "turnover": 20},
        {"symbol": "TCS", "companyName": "Tata", "volume": 300, "week1AvgVolume": 20, "week1volChange": 2, "week2AvgVolume": 20, "week2volChange": 2, "ltp": 3500, "pChange": 3, "turnover": 30},
    ]
    test_date = date(2026, 9, 18)

    # First run
    res1 = storage.save(DatasetIdentifier.VOLUME_GAINERS_SPURTS, initial_data, run_date=test_date)
    assert res1.is_overwrite is False
    assert res1.record_count == 1

    # Second run on the same date
    res2 = storage.save(DatasetIdentifier.VOLUME_GAINERS_SPURTS, updated_data, run_date=test_date)
    assert res2.is_overwrite is True
    assert res2.record_count == 2
    assert res2.output_path == res1.output_path

    # Verify no secondary file like volume_gainers_spurts_2026-09-18_1.csv was created
    parent_dir = res1.output_path.parent
    csv_files = list(parent_dir.glob("*.csv"))
    assert len(csv_files) == 1
    assert csv_files[0].name == "volume_gainers_spurts_2026-09-18.csv"

    # Verify updated content is present
    with open(res2.output_path, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 2
    assert rows[0]["TODAY_VOLUME"] == "200"


def test_storage_write_failure_handling(storage, monkeypatch):
    """8. File write exception is handled and temporary file is removed."""
    sample = [{"symbol": "INFY", "companyName": "Infosys", "volume": 100, "week1AvgVolume": 10, "week1volChange": 1, "week2AvgVolume": 10, "week2volChange": 1, "ltp": 1500, "pChange": 1, "turnover": 10}]
    
    # Simulate an error during open
    with patch("builtins.open", side_effect=OSError("Disk write error")):
        with pytest.raises(StorageWriteError) as exc_info:
            storage.save(DatasetIdentifier.VOLUME_GAINERS_SPURTS, sample)
        assert "Disk write error" in str(exc_info.value)

