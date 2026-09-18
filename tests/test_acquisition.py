"""Unit tests for the NSE Data Acquisition layer with mocked HTTP responses."""

import json
from unittest.mock import MagicMock, patch

import pytest
import requests

from nse_market_data.downloader.acquisition import NSEDataAcquisition
from nse_market_data.downloader.client import NSEClient
from nse_market_data.downloader.exceptions import (
    NSEConnectionError,
    NSEDataExtractionError,
    NSEHTTPError,
    NSEResponseParsingError,
    NSETimeoutError,
)
from nse_market_data.downloader.parser import (
    parse_52_week_high,
    parse_top_gainers_losers,
    parse_upper_band_hitters,
    parse_volume_gainers_spurts,
)
from nse_market_data.models import DatasetIdentifier, DownloadStatus


def make_mock_response(status_code: int = 200, text: str = "{}", json_data: dict = None):
    """Helper to generate a mock requests.Response."""
    mock_resp = MagicMock(spec=requests.Response)
    mock_resp.status_code = status_code
    mock_resp.reason = "OK" if status_code == 200 else "Error"
    if json_data is not None:
        mock_resp.text = json.dumps(json_data)
        mock_resp.json.return_value = json_data
    else:
        mock_resp.text = text
        if text:
            mock_resp.json.side_effect = lambda: json.loads(text)
        else:
            mock_resp.json.side_effect = json.JSONDecodeError("Empty", "", 0)
    return mock_resp


# ---------------------------------------------------------------------------
# Parser tests for the 4 datasets
# ---------------------------------------------------------------------------


def test_parser_top_gainers_losers_success():
    payload = {
        "legends": [["NIFTY", "NIFTY 50"]],
        "NIFTY": {
            "data": [
                {"symbol": "ADANIPORTS", "ltp": 1824, "perChange": 4.93},
                {"symbol": "BHARTIARTL", "ltp": 1893.3, "perChange": 3.12},
            ]
        },
        "time": "18-Sep-2026 16:00:00",
    }
    records, meta = parse_top_gainers_losers(payload)
    assert len(records) == 2
    assert records[0]["symbol"] == "ADANIPORTS"
    assert meta["raw_record_count"] == 2
    assert meta["timestamp"] == "18-Sep-2026 16:00:00"


def test_parser_upper_band_hitters_success():
    payload = {
        "upper": {
            "AllSec": {
                "data": [
                    {"symbol": "EMCURE", "series": "EQ", "ltp": "2083", "pChange": "9.07"},
                    {"symbol": "TBZ", "series": "EQ", "ltp": "603.55", "pChange": "4.99"},
                ]
            }
        },
        "timestamp": "18-Sep-2026",
    }
    records, meta = parse_upper_band_hitters(payload)
    assert len(records) == 2
    assert records[0]["symbol"] == "EMCURE"
    assert meta["raw_record_count"] == 2


def test_parser_volume_gainers_spurts_success():
    payload = {
        "data": [
            {"symbol": "NIFTYBETA", "companyName": "UTI Nifty 50 ETF", "volume": 2607269},
            {"symbol": "ATGL", "companyName": "Adani Total Gas Limited", "volume": 39305845},
        ],
        "timestamp": "18-Sep-2026 16:00:00",
    }
    records, meta = parse_volume_gainers_spurts(payload)
    assert len(records) == 2
    assert records[0]["symbol"] == "NIFTYBETA"
    assert meta["raw_record_count"] == 2


def test_parser_52_week_high_success():
    payload = {
        "data": [
            {"symbol": "AAREYDRUGS", "series": "EQ", "ltp": 101, "new52WHL": 103.5},
            {"symbol": "ACE", "series": "EQ", "ltp": 1229.1, "new52WHL": 1241.5},
        ],
        "timestamp": "18-Sep-2026 16:00:00",
    }
    records, meta = parse_52_week_high(payload)
    assert len(records) == 2
    assert records[0]["symbol"] == "AAREYDRUGS"
    assert meta["raw_record_count"] == 2


# ---------------------------------------------------------------------------
# HTTP Client tests (Requirements 1 - 8)
# ---------------------------------------------------------------------------


def test_client_successful_response():
    """1. Successful response retrieval and parsing."""
    mock_session = MagicMock()
    mock_session.get.return_value = make_mock_response(json_data={"data": [{"symbol": "INFY"}]})

    client = NSEClient(session=mock_session, max_retries=1)
    data = client.get_json("https://www.nseindia.com/api/test")

    assert "data" in data
    assert data["data"][0]["symbol"] == "INFY"


def test_client_connection_failure():
    """2. Connection failure across all retries raises NSEConnectionError."""
    mock_session = MagicMock()
    mock_session.get.side_effect = requests.exceptions.ConnectionError("Failed to connect")

    client = NSEClient(session=mock_session, max_retries=2, backoff_factor=0.01)
    with pytest.raises(NSEConnectionError) as exc_info:
        client.get_json("https://www.nseindia.com/api/test")

    assert "Network connection failed" in str(exc_info.value)
    assert mock_session.get.call_count == 2


def test_client_timeout():
    """3. Timeout failure across all retries raises NSETimeoutError."""
    mock_session = MagicMock()
    mock_session.get.side_effect = requests.exceptions.Timeout("Timed out")

    client = NSEClient(session=mock_session, max_retries=2, backoff_factor=0.01)
    with pytest.raises(NSETimeoutError) as exc_info:
        client.get_json("https://www.nseindia.com/api/test")

    assert "timed out" in str(exc_info.value)
    assert mock_session.get.call_count == 2


def test_client_http_error_non_retryable():
    """4. Non-retryable HTTP error (e.g. 404) fails immediately."""
    mock_session = MagicMock()
    mock_session.get.return_value = make_mock_response(status_code=404, text="Not Found")

    client = NSEClient(session=mock_session, max_retries=3, backoff_factor=0.01)
    with pytest.raises(NSEHTTPError) as exc_info:
        client.get_json("https://www.nseindia.com/api/test")

    assert exc_info.value.status_code == 404
    assert mock_session.get.call_count == 1  # No useless retries on 404


def test_client_retryable_failure_then_success():
    """5. Retryable failure (HTTP 500) followed by success on next attempt."""
    mock_session = MagicMock()
    err_resp = make_mock_response(status_code=500, text="Internal Server Error")
    success_resp = make_mock_response(json_data={"data": [{"symbol": "TCS"}]})
    mock_session.get.side_effect = [err_resp, success_resp]

    client = NSEClient(session=mock_session, max_retries=3, backoff_factor=0.01)
    data = client.get_json("https://www.nseindia.com/api/test")

    assert data == {"data": [{"symbol": "TCS"}]}
    assert mock_session.get.call_count == 2


def test_client_malformed_response():
    """6. Malformed JSON response raises NSEResponseParsingError."""
    mock_session = MagicMock()
    mock_session.get.return_value = make_mock_response(status_code=200, text="NOT_VALID_JSON{")

    client = NSEClient(session=mock_session, max_retries=1)
    with pytest.raises(NSEResponseParsingError) as exc_info:
        client.get_json("https://www.nseindia.com/api/test")

    assert "Malformed JSON" in str(exc_info.value)


def test_client_empty_response():
    """7. Empty response body raises NSEResponseParsingError."""
    mock_session = MagicMock()
    mock_session.get.return_value = make_mock_response(status_code=200, text="   ")

    client = NSEClient(session=mock_session, max_retries=1)
    with pytest.raises(NSEResponseParsingError) as exc_info:
        client.get_json("https://www.nseindia.com/api/test")

    assert "Empty response body" in str(exc_info.value)


def test_client_html_error_page_response():
    """Detects HTML returned on JSON endpoint and raises NSEResponseParsingError."""
    mock_session = MagicMock()
    html_text = "<!DOCTYPE html><html><body><h1>Access Denied</h1></body></html>"
    mock_session.get.return_value = make_mock_response(status_code=200, text=html_text)

    client = NSEClient(session=mock_session, max_retries=1)
    with pytest.raises(NSEResponseParsingError) as exc_info:
        client.get_json("https://www.nseindia.com/api/test")

    assert "HTML webpage" in str(exc_info.value)


def test_unexpected_response_structure():
    """8. Unexpected response structure raises NSEDataExtractionError."""
    payload = {"unexpected_root_key": "some_value"}
    with pytest.raises(NSEDataExtractionError):
        parse_volume_gainers_spurts(payload)


def test_empty_data_records_in_payload():
    """Empty data list raises NSEDataExtractionError."""
    payload = {"data": []}
    with pytest.raises(NSEDataExtractionError) as exc_info:
        parse_52_week_high(payload)
    assert "empty data array" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Acquisition Coordinator & Failure Isolation tests
# ---------------------------------------------------------------------------


def test_acquire_dataset_success():
    mock_client = MagicMock(spec=NSEClient)
    mock_client.get_json.return_value = {
        "data": [{"symbol": "INFY", "volume": 100}],
        "timestamp": "18-Sep-2026",
    }

    acq = NSEDataAcquisition(client=mock_client)
    result = acq.acquire_dataset(DatasetIdentifier.VOLUME_GAINERS_SPURTS)

    assert result.status == DownloadStatus.SUCCESS
    assert result.record_count == 1
    assert result.records[0]["symbol"] == "INFY"


def test_failure_isolation_in_batch():
    """Verify failure of one dataset does not block remaining datasets."""
    mock_client = MagicMock(spec=NSEClient)

    def side_effect_get(url):
        if "live-analysis-price-band-hitter" in url:
            # Simulate failure on Upper Band Hitters
            raise NSEConnectionError("Simulated connection timeout")
        if "live-analysis-variations" in url:
            return {"NIFTY": {"data": [{"symbol": "SBIN"}]}}
        if "live-analysis-volume-gainers" in url:
            return {"data": [{"symbol": "ITC"}]}
        if "live-analysis-data-52weekhighstock" in url:
            return {"data": [{"symbol": "RELIANCE"}]}
        return {"data": []}

    mock_client.get_json.side_effect = side_effect_get

    acq = NSEDataAcquisition(client=mock_client)
    results = acq.acquire_all()

    assert len(results) == 4
    # Upper Band should have failed
    assert results[DatasetIdentifier.UPPER_BAND_HITTERS].status == DownloadStatus.FAILED
    assert "NSEConnectionError" in results[DatasetIdentifier.UPPER_BAND_HITTERS].error_message

    # The other 3 datasets should have succeeded despite the failure of Upper Band
    assert results[DatasetIdentifier.TOP_GAINERS_LOSERS].status == DownloadStatus.SUCCESS
    assert results[DatasetIdentifier.TOP_GAINERS_LOSERS].record_count == 1
    assert results[DatasetIdentifier.VOLUME_GAINERS_SPURTS].status == DownloadStatus.SUCCESS
    assert results[DatasetIdentifier.VOLUME_GAINERS_SPURTS].record_count == 1
    assert results[DatasetIdentifier.FIFTY_TWO_WEEK_HIGH].status == DownloadStatus.SUCCESS
    assert results[DatasetIdentifier.FIFTY_TWO_WEEK_HIGH].record_count == 1

