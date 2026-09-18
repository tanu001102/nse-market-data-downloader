"""Centralized configuration module for NSE Market Data Downloader."""

import os
from pathlib import Path
from typing import Dict, List, Optional

from nse_market_data.models import DatasetConfig, DatasetIdentifier

# Base directory paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_DATA_DIR = BASE_DIR / "data"
DEFAULT_RAW_DIR = DEFAULT_DATA_DIR / "raw"
DEFAULT_OUTPUT_DIR = DEFAULT_DATA_DIR / "output"
DEFAULT_LOG_DIR = BASE_DIR / "logs"

# HTTP and network configurations
DEFAULT_TIMEOUT_SECONDS = int(os.environ.get("NSE_REQUEST_TIMEOUT", "15"))
DEFAULT_MAX_RETRIES = int(os.environ.get("NSE_MAX_RETRIES", "3"))
DEFAULT_BACKOFF_FACTOR = float(os.environ.get("NSE_BACKOFF_FACTOR", "1.0"))
NSE_BASE_URL = "https://www.nseindia.com"

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/128.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/",
}

# The four required datasets defined strictly according to assignment requirements
DATASET_CONFIGS: Dict[DatasetIdentifier, DatasetConfig] = {
    DatasetIdentifier.TOP_GAINERS_LOSERS: DatasetConfig(
        identifier=DatasetIdentifier.TOP_GAINERS_LOSERS,
        name="Top Gainers / Losers",
        page_url="https://www.nseindia.com/market-data/top-gainers-losers",
        api_url="https://www.nseindia.com/api/live-analysis-variations?index=gainers",
        output_subdir="top_gainers_losers",
        filename_prefix="top_gainers_losers",
        description="Top gainers and losers in the market",
        required_keys=(
            "symbol",
            "open_price",
            "high_price",
            "low_price",
            "ltp",
            "prev_price",
            "perChange",
        ),
        unique_key_fields=("symbol", "series"),
        column_mapping={
            "symbol": "SYMBOL",
            "series": "SERIES",
            "open_price": "OPEN",
            "high_price": "HIGH",
            "low_price": "LOW",
            "prev_price": "PREV_CLOSE",
            "ltp": "LTP",
            "perChange": "PERCENT_CHANGE",
            "trade_quantity": "VOLUME",
            "turnover": "VALUE",
            "ca_ex_dt": "CA_EX_DATE",
            "ca_purpose": "CA_PURPOSE",
        },
    ),
    DatasetIdentifier.UPPER_BAND_HITTERS: DatasetConfig(
        identifier=DatasetIdentifier.UPPER_BAND_HITTERS,
        name="Upper Band Hitters",
        page_url="https://www.nseindia.com/market-data/upper-band-hitters",
        api_url="https://www.nseindia.com/api/live-analysis-price-band-hitter",
        output_subdir="upper_band_hitters",
        filename_prefix="upper_band_hitters",
        description="Securities that hit their upper price band",
        required_keys=(
            "symbol",
            "series",
            "ltp",
            "change",
            "pChange",
            "priceBand",
        ),
        unique_key_fields=("symbol", "series"),
        column_mapping={
            "symbol": "SYMBOL",
            "series": "SERIES",
            "ltp": "LTP",
            "change": "CHANGE",
            "pChange": "PERCENT_CHANGE",
            "priceBand": "PRICE_BAND_PERCENT",
            "totalTradedVol": "VOLUME_LAKHS",
            "turnover": "VALUE_CRORES",
            "highPrice": "HIGH_PRICE",
            "lowPrice": "LOW_PRICE",
            "yearHigh": "YEAR_HIGH",
            "yearLow": "YEAR_LOW",
        },
    ),
    DatasetIdentifier.VOLUME_GAINERS_SPURTS: DatasetConfig(
        identifier=DatasetIdentifier.VOLUME_GAINERS_SPURTS,
        name="Volume Gainers / Spurts",
        page_url="https://www.nseindia.com/market-data/volume-gainers-spurts",
        api_url="https://www.nseindia.com/api/live-analysis-volume-gainers",
        output_subdir="volume_gainers_spurts",
        filename_prefix="volume_gainers_spurts",
        description="Securities exhibiting volume spurts and gainers",
        required_keys=(
            "symbol",
            "companyName",
            "volume",
            "ltp",
            "pChange",
        ),
        unique_key_fields=("symbol",),
        column_mapping={
            "symbol": "SYMBOL",
            "companyName": "SECURITY_NAME",
            "volume": "TODAY_VOLUME",
            "week1AvgVolume": "PAST_WEEK_AVG_VOLUME",
            "week1volChange": "PAST_WEEK_CHANGE",
            "week2AvgVolume": "PAST_2_WEEK_AVG_VOLUME",
            "week2volChange": "PAST_2_WEEK_CHANGE",
            "ltp": "TODAY_LTP",
            "pChange": "TODAY_PERCENT_CHANGE",
            "turnover": "TODAY_VALUE",
        },
    ),
    DatasetIdentifier.FIFTY_TWO_WEEK_HIGH: DatasetConfig(
        identifier=DatasetIdentifier.FIFTY_TWO_WEEK_HIGH,
        name="52 Week High — Equity Market",
        page_url="https://www.nseindia.com/market-data/52-week-high-equity-market",
        api_url="https://www.nseindia.com/api/live-analysis-data-52weekhighstock",
        output_subdir="52_week_high",
        filename_prefix="52_week_high",
        description="Equity market securities touching 52-week highs",
        required_keys=(
            "symbol",
            "series",
            "ltp",
            "new52WHL",
            "prev52WHL",
            "prevHLDate",
        ),
        unique_key_fields=("symbol", "series"),
        column_mapping={
            "symbol": "SYMBOL",
            "series": "SERIES",
            "ltp": "LTP",
            "change": "CHANGE",
            "pChange": "PERCENT_CHANGE",
            "new52WHL": "NEW_52W_HIGH_PRICE",
            "prev52WHL": "PREV_HIGH",
            "prevHLDate": "PREV_HIGH_DATE",
            "prevClose": "PREV_CLOSE",
            "comapnyName": "COMPANY_NAME",
        },
    ),
}

DATASET_ALIASES: Dict[str, DatasetIdentifier] = {
    "52-week-high-equity-market": DatasetIdentifier.FIFTY_TWO_WEEK_HIGH,
}


def get_dataset_config(dataset_id: DatasetIdentifier) -> DatasetConfig:
    """Retrieve configuration for a specific dataset identifier."""
    if dataset_id not in DATASET_CONFIGS:
        raise ValueError(f"Unknown dataset identifier: {dataset_id}")
    return DATASET_CONFIGS[dataset_id]


def get_all_dataset_configs() -> List[DatasetConfig]:
    """Retrieve configurations for all four required datasets."""
    return list(DATASET_CONFIGS.values())


def get_output_dir(override: Optional[Path] = None) -> Path:
    """Determine the effective output directory (override > env var > default)."""
    if override:
        return Path(override)

    env_path = os.environ.get("NSE_OUTPUT_DIR")
    if env_path:
        return Path(env_path)

    return DEFAULT_OUTPUT_DIR


def resolve_dataset_identifier(name: str) -> DatasetIdentifier:
    """Resolves a string identifier or alias to a valid DatasetIdentifier."""
    clean_name = name.strip().lower()
    if clean_name in DATASET_ALIASES:
        return DATASET_ALIASES[clean_name]
    try:
        return DatasetIdentifier(clean_name)
    except ValueError:
        valid_choices = [d.value for d in DatasetIdentifier] + list(DATASET_ALIASES.keys())
        raise ValueError(
            f"Invalid dataset '{name}'. Available choices: {', '.join(valid_choices)}"
        )


def get_valid_cli_choices() -> List[str]:
    """Returns valid choices for the CLI --dataset option including aliases."""
    return [d.value for d in DatasetIdentifier] + list(DATASET_ALIASES.keys())
