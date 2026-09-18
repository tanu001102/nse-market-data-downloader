"""Data validator module for verifying schema conformity and deduplicating records."""

import logging
from typing import Any, Dict, List, Optional, Set, Tuple

from nse_market_data.config import DATASET_CONFIGS, get_dataset_config
from nse_market_data.models import DatasetConfig, DatasetIdentifier, ValidationResult
from nse_market_data.validation.exceptions import (
    EmptyDatasetError,
    InvalidDataStructureError,
    MissingColumnsError,
    UnusableRecordError,
    ValidationError,
)

logger = logging.getLogger("nse_market_data.validation")


class DataValidator:
    """Validates raw dataset records against expected schemas and removes duplicate records."""

    def __init__(self, configs: Optional[Dict[DatasetIdentifier, DatasetConfig]] = None):
        self.configs = configs or DATASET_CONFIGS

    def validate(
        self, dataset_id: DatasetIdentifier, records: Any
    ) -> ValidationResult:
        """Performs non-raising structural and schema validation with deduplication.

        Returns a ValidationResult object capturing status, counts, and clean records.
        """
        config = self.configs.get(dataset_id)
        if not config:
            return ValidationResult(
                dataset_id=dataset_id,
                is_valid=False,
                error_message=f"Configuration not found for dataset {dataset_id}",
            )

        logger.info(f"Validating dataset '{config.name}' ({dataset_id.value})")

        # 1. Verify structure type
        if not isinstance(records, list):
            msg = f"Expected list of records, received {type(records).__name__}"
            logger.error(f"Validation failed for {config.name}: {msg}")
            return ValidationResult(
                dataset_id=dataset_id,
                is_valid=False,
                error_message=msg,
            )

        # 2. Verify non-empty
        if len(records) == 0:
            msg = "Dataset contains zero records (empty dataset)."
            logger.error(f"Validation failed for {config.name}: {msg}")
            return ValidationResult(
                dataset_id=dataset_id,
                is_valid=False,
                original_count=0,
                error_message=msg,
            )

        original_count = len(records)

        # 3. Check for dictionary type and required keys across records
        all_missing_keys: Set[str] = set()
        required_keys = set(config.required_keys)

        for idx, item in enumerate(records):
            if not isinstance(item, dict):
                msg = f"Record at index {idx} is not a dictionary (type: {type(item).__name__})."
                logger.error(f"Validation failed for {config.name}: {msg}")
                return ValidationResult(
                    dataset_id=dataset_id,
                    is_valid=False,
                    original_count=original_count,
                    error_message=msg,
                )

            item_keys = set(item.keys())
            missing = required_keys - item_keys
            if missing:
                all_missing_keys.update(missing)

        if all_missing_keys:
            sorted_missing = sorted(list(all_missing_keys))
            msg = f"Missing required column(s): {', '.join(sorted_missing)}"
            logger.error(f"Validation failed for {config.name}: {msg}")
            return ValidationResult(
                dataset_id=dataset_id,
                is_valid=False,
                original_count=original_count,
                missing_columns=sorted_missing,
                error_message=msg,
            )

        # 4. Check for unusable records and perform deduplication (Keep-First Policy)
        seen_keys: Set[Tuple[str, ...]] = set()
        clean_records: List[Dict[str, Any]] = []
        duplicate_count = 0
        unusable_count = 0

        for item in records:
            # Primary symbol check
            symbol_raw = item.get("symbol")
            if symbol_raw is None or not str(symbol_raw).strip():
                unusable_count += 1
                continue

            # Build stable business key from configured unique_key_fields
            key_parts = tuple(
                str(item.get(field, "")).strip().upper()
                for field in config.unique_key_fields
            )

            if key_parts in seen_keys:
                duplicate_count += 1
                logger.debug(f"Duplicate record detected for key {key_parts}; skipping.")
                continue

            seen_keys.add(key_parts)
            clean_records.append(item)

        if not clean_records:
            msg = "All records were rejected as unusable or duplicates."
            logger.error(f"Validation failed for {config.name}: {msg}")
            return ValidationResult(
                dataset_id=dataset_id,
                is_valid=False,
                original_count=original_count,
                error_message=msg,
            )

        if duplicate_count > 0:
            logger.info(
                f"Deduplication completed for {config.name}: removed {duplicate_count} duplicate record(s)."
            )

        if unusable_count > 0:
            logger.warning(
                f"Filtered {unusable_count} unusable record(s) lacking valid symbols in {config.name}."
            )

        logger.info(
            f"Validation PASSED for {config.name}: {len(clean_records)} valid records (Original: {original_count}, Duplicates removed: {duplicate_count})"
        )

        return ValidationResult(
            dataset_id=dataset_id,
            is_valid=True,
            original_count=original_count,
            valid_count=len(clean_records),
            duplicate_count=duplicate_count,
            validated_records=clean_records,
        )

    def validate_or_raise(
        self, dataset_id: DatasetIdentifier, records: Any
    ) -> ValidationResult:
        """Performs validation and raises explicit exceptions on failure."""
        result = self.validate(dataset_id, records)
        if not result.is_valid:
            if "Expected list" in (result.error_message or "") or "not a dictionary" in (result.error_message or ""):
                raise InvalidDataStructureError(result.error_message or "Invalid structure")
            if result.original_count == 0:
                raise EmptyDatasetError(result.error_message or "Empty dataset")
            if result.missing_columns:
                raise MissingColumnsError(
                    result.error_message or "Missing columns",
                    missing_columns=result.missing_columns,
                )
            raise ValidationError(result.error_message or "Validation failed")
        return result

