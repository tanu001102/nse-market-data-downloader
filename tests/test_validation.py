"""Unit tests for the Data Validation layer."""

import pytest

from nse_market_data.models import DatasetIdentifier
from nse_market_data.validation.exceptions import (
    EmptyDatasetError,
    InvalidDataStructureError,
    MissingColumnsError,
    ValidationError,
)
from nse_market_data.validation.validator import DataValidator


@pytest.fixture
def validator():
    return DataValidator()


# ---------------------------------------------------------------------------
# Valid data tests across all 4 datasets
# ---------------------------------------------------------------------------


def test_validation_top_gainers_success(validator):
    sample = [
        {
            "symbol": "ADANIPORTS",
            "series": "EQ",
            "open_price": 1748,
            "high_price": 1824,
            "low_price": 1744,
            "ltp": 1824,
            "prev_price": 1738.3,
            "perChange": 4.93,
            "trade_quantity": 4148803,
            "turnover": 74138.69,
        }
    ]
    res = validator.validate(DatasetIdentifier.TOP_GAINERS_LOSERS, sample)
    assert res.is_valid is True
    assert res.valid_count == 1
    assert res.duplicate_count == 0


def test_validation_upper_band_success(validator):
    sample = [
        {
            "symbol": "EMCURE",
            "series": "EQ",
            "ltp": "2083",
            "change": "173.2",
            "pChange": "9.07",
            "priceBand": "10",
        }
    ]
    res = validator.validate(DatasetIdentifier.UPPER_BAND_HITTERS, sample)
    assert res.is_valid is True
    assert res.valid_count == 1
    assert res.duplicate_count == 0


def test_validation_volume_gainers_success(validator):
    sample = [
        {
            "symbol": "NIFTYBETA",
            "companyName": "UTI Nifty 50 ETF",
            "volume": 2607269,
            "ltp": 261.99,
            "pChange": 1.19,
        }
    ]
    res = validator.validate(DatasetIdentifier.VOLUME_GAINERS_SPURTS, sample)
    assert res.is_valid is True
    assert res.valid_count == 1
    assert res.duplicate_count == 0


def test_validation_52_week_high_success(validator):
    sample = [
        {
            "symbol": "AAREYDRUGS",
            "series": "EQ",
            "ltp": 101,
            "new52WHL": 103.5,
            "prev52WHL": 102.96,
            "prevHLDate": "17-Sep-2026",
        }
    ]
    res = validator.validate(DatasetIdentifier.FIFTY_TWO_WEEK_HIGH, sample)
    assert res.is_valid is True
    assert res.valid_count == 1
    assert res.duplicate_count == 0


# ---------------------------------------------------------------------------
# Empty dataset handling
# ---------------------------------------------------------------------------


def test_empty_dataset_rejected(validator):
    res = validator.validate(DatasetIdentifier.TOP_GAINERS_LOSERS, [])
    assert res.is_valid is False
    assert "empty dataset" in res.error_message.lower()

    with pytest.raises(EmptyDatasetError):
        validator.validate_or_raise(DatasetIdentifier.TOP_GAINERS_LOSERS, [])


# ---------------------------------------------------------------------------
# Missing required columns
# ---------------------------------------------------------------------------


def test_missing_required_column_rejected(validator):
    # Missing 'ltp' and 'perChange'
    sample = [
        {
            "symbol": "ADANIPORTS",
            "series": "EQ",
            "open_price": 1748,
            "high_price": 1824,
            "low_price": 1744,
            "prev_price": 1738.3,
        }
    ]
    res = validator.validate(DatasetIdentifier.TOP_GAINERS_LOSERS, sample)
    assert res.is_valid is False
    assert "ltp" in res.missing_columns
    assert "perChange" in res.missing_columns

    with pytest.raises(MissingColumnsError) as exc_info:
        validator.validate_or_raise(DatasetIdentifier.TOP_GAINERS_LOSERS, sample)
    assert "ltp" in exc_info.value.missing_columns


# ---------------------------------------------------------------------------
# Unexpected structure handling
# ---------------------------------------------------------------------------


def test_invalid_data_structure_not_a_list(validator):
    res = validator.validate(DatasetIdentifier.VOLUME_GAINERS_SPURTS, {"data": []})
    assert res.is_valid is False
    assert "Expected list" in res.error_message

    with pytest.raises(InvalidDataStructureError):
        validator.validate_or_raise(DatasetIdentifier.VOLUME_GAINERS_SPURTS, "invalid_string")


def test_invalid_record_not_a_dict(validator):
    sample = ["not_a_dict", 123]
    res = validator.validate(DatasetIdentifier.VOLUME_GAINERS_SPURTS, sample)
    assert res.is_valid is False
    assert "not a dictionary" in res.error_message

    with pytest.raises(InvalidDataStructureError):
        validator.validate_or_raise(DatasetIdentifier.VOLUME_GAINERS_SPURTS, sample)


# ---------------------------------------------------------------------------
# Duplicate handling
# ---------------------------------------------------------------------------


def test_duplicate_records_detected_and_removed(validator):
    sample = [
        {"symbol": "INFY", "companyName": "Infosys", "volume": 100, "ltp": 1500, "pChange": 1.5},
        {"symbol": "TCS", "companyName": "Tata Consultancy", "volume": 200, "ltp": 3500, "pChange": 2.0},
        {"symbol": "INFY", "companyName": "Infosys Duplicate", "volume": 100, "ltp": 1500, "pChange": 1.5},  # Duplicate of INFY
    ]
    res = validator.validate(DatasetIdentifier.VOLUME_GAINERS_SPURTS, sample)
    assert res.is_valid is True
    assert res.original_count == 3
    assert res.valid_count == 2
    assert res.duplicate_count == 1
    # Check that the first record was retained
    symbols = [r["symbol"] for r in res.validated_records]
    assert symbols == ["INFY", "TCS"]
    assert res.validated_records[0]["companyName"] == "Infosys"


def test_series_aware_duplicates(validator):
    """Securities with same symbol but distinct series (EQ vs BE) are NOT duplicates."""
    sample = [
        {"symbol": "HEG", "series": "EQ", "ltp": "237", "change": "10", "pChange": "4.9", "priceBand": "5"},
        {"symbol": "HEG", "series": "BE", "ltp": "237", "change": "10", "pChange": "4.9", "priceBand": "5"},
        {"symbol": "HEG", "series": "EQ", "ltp": "237", "change": "10", "pChange": "4.9", "priceBand": "5"},  # Exact duplicate of EQ
    ]
    res = validator.validate(DatasetIdentifier.UPPER_BAND_HITTERS, sample)
    assert res.is_valid is True
    assert res.original_count == 3
    assert res.valid_count == 2
    assert res.duplicate_count == 1
    assert [(r["symbol"], r["series"]) for r in res.validated_records] == [("HEG", "EQ"), ("HEG", "BE")]


def test_records_with_blank_symbols_filtered(validator):
    sample = [
        {"symbol": "   ", "series": "EQ", "ltp": "100", "change": "5", "pChange": "5", "priceBand": "5"},
        {"symbol": "VALID", "series": "EQ", "ltp": "100", "change": "5", "pChange": "5", "priceBand": "5"},
    ]
    res = validator.validate(DatasetIdentifier.UPPER_BAND_HITTERS, sample)
    assert res.is_valid is True
    assert res.valid_count == 1
    assert res.validated_records[0]["symbol"] == "VALID"

