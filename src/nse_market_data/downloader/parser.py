"""Response parsers for extracting records from NSE JSON payloads."""

import logging
from typing import Any, Dict, List, Optional, Tuple

from nse_market_data.downloader.exceptions import NSEDataExtractionError
from nse_market_data.models import DatasetIdentifier

logger = logging.getLogger("nse_market_data.downloader")


def parse_top_gainers_losers(payload: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Extracts records from the Top Gainers/Losers endpoint payload."""
    # Preferred index is NIFTY (matching the benchmark export 'T20-GL-gainers-NIFTY')
    candidates = ["NIFTY", "allSec", "SecGtr20", "data"]
    records: Optional[List[Dict[str, Any]]] = None

    for candidate in candidates:
        container = payload.get(candidate)
        if isinstance(container, dict) and isinstance(container.get("data"), list):
            records = container["data"]
            break
        elif isinstance(container, list):
            records = container
            break

    if records is None or not isinstance(records, list):
        raise NSEDataExtractionError(
            f"Top Gainers/Losers payload missing expected record lists. Keys found: {list(payload.keys())}"
        )

    if not records:
        raise NSEDataExtractionError("Top Gainers/Losers payload contained empty data array.")

    metadata = {
        "timestamp": payload.get("time") or payload.get("timestamp"),
        "raw_record_count": len(records),
        "source_index": candidate if records is not None else None,
    }
    return records, metadata


def parse_upper_band_hitters(payload: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Extracts records from the Upper Band Hitters endpoint payload."""
    upper_block = payload.get("upper")
    if not isinstance(upper_block, dict):
        raise NSEDataExtractionError(
            f"Upper Band payload missing 'upper' section. Keys found: {list(payload.keys())}"
        )

    # Preferred category is AllSec
    all_sec = upper_block.get("AllSec")
    records: Optional[List[Dict[str, Any]]] = None
    if isinstance(all_sec, dict) and isinstance(all_sec.get("data"), list):
        records = all_sec["data"]
    elif isinstance(upper_block.get("data"), list):
        records = upper_block["data"]

    if records is None or not isinstance(records, list):
        raise NSEDataExtractionError(
            f"Upper Band payload missing 'AllSec.data'. Keys in 'upper': {list(upper_block.keys())}"
        )

    if not records:
        raise NSEDataExtractionError("Upper Band Hitters payload contained empty data array.")

    metadata = {
        "timestamp": payload.get("timestamp") or upper_block.get("timestamp"),
        "raw_record_count": len(records),
    }
    return records, metadata


def parse_volume_gainers_spurts(payload: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Extracts records from the Volume Gainers/Spurts endpoint payload."""
    records = payload.get("data")
    if not isinstance(records, list):
        raise NSEDataExtractionError(
            f"Volume Gainers payload missing 'data' list. Keys found: {list(payload.keys())}"
        )

    if not records:
        raise NSEDataExtractionError("Volume Gainers payload contained empty data array.")

    metadata = {
        "timestamp": payload.get("timestamp"),
        "raw_record_count": len(records),
    }
    return records, metadata


def parse_52_week_high(payload: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Extracts records from the 52 Week High endpoint payload."""
    records = payload.get("data")
    if not isinstance(records, list):
        raise NSEDataExtractionError(
            f"52 Week High payload missing 'data' list. Keys found: {list(payload.keys())}"
        )

    if not records:
        raise NSEDataExtractionError("52 Week High payload contained empty data array.")

    metadata = {
        "timestamp": payload.get("timestamp"),
        "raw_record_count": len(records),
    }
    return records, metadata


PARSERS = {
    DatasetIdentifier.TOP_GAINERS_LOSERS: parse_top_gainers_losers,
    DatasetIdentifier.UPPER_BAND_HITTERS: parse_upper_band_hitters,
    DatasetIdentifier.VOLUME_GAINERS_SPURTS: parse_volume_gainers_spurts,
    DatasetIdentifier.FIFTY_TWO_WEEK_HIGH: parse_52_week_high,
}


def parse_dataset_response(
    dataset_id: DatasetIdentifier, payload: Dict[str, Any]
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Dispatches payload parsing to the specific dataset parser."""
    if dataset_id not in PARSERS:
        raise ValueError(f"No parser registered for dataset: {dataset_id}")

    parser = PARSERS[dataset_id]
    return parser(payload)

