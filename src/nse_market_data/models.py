"""Data models and enums for the NSE Market Data Downloader."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class DatasetIdentifier(str, Enum):
    """Supported NSE dataset identifiers."""

    TOP_GAINERS_LOSERS = "top-gainers-losers"
    UPPER_BAND_HITTERS = "upper-band-hitters"
    VOLUME_GAINERS_SPURTS = "volume-gainers-spurts"
    FIFTY_TWO_WEEK_HIGH = "52-week-high"


class DownloadStatus(str, Enum):
    """Status of a dataset download operation."""

    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass(frozen=True)
class DatasetConfig:
    """Configuration metadata for an individual NSE dataset."""

    identifier: DatasetIdentifier
    name: str
    page_url: str
    api_url: str
    output_subdir: str
    filename_prefix: str
    description: str
    required_keys: Tuple[str, ...] = ()
    unique_key_fields: Tuple[str, ...] = ("symbol",)
    column_mapping: Dict[str, str] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """Outcome of validating raw acquired records."""

    dataset_id: DatasetIdentifier
    is_valid: bool
    original_count: int = 0
    valid_count: int = 0
    duplicate_count: int = 0
    validated_records: List[Dict[str, Any]] = field(default_factory=list)
    missing_columns: List[str] = field(default_factory=list)
    error_message: Optional[str] = None


@dataclass
class StorageResult:
    """Outcome of writing validated records to CSV storage."""

    dataset_id: DatasetIdentifier
    output_path: Path
    record_count: int = 0
    is_overwrite: bool = False
    status: DownloadStatus = DownloadStatus.PENDING
    error_message: Optional[str] = None


@dataclass
class DownloadResult:
    """Captures execution outcome for a dataset download attempt."""

    dataset_id: DatasetIdentifier
    status: DownloadStatus
    record_count: int = 0
    records: Optional[List[Dict[str, Any]]] = None
    output_path: Optional[Path] = None
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
