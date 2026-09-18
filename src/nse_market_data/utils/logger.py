"""Logging setup and formatting for the NSE Market Data Downloader."""

import logging
from pathlib import Path
from typing import Optional

from nse_market_data.config import DEFAULT_LOG_DIR

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logger(
    name: str = "nse_market_data",
    log_dir: Optional[Path] = None,
    log_file: str = "downloader.log",
    level: int = logging.INFO,
) -> logging.Logger:
    """Configures and returns a logger with both console and rotating file output.
    
    Logs will support recording:
    - Attempted datasets and timestamps
    - Operation status (success/failure)
    - Processed record counts
    - Diagnostic error and exception details
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding duplicate handlers if setup_logger is called repeatedly
    if logger.hasHandlers():
        return logger

    formatter = logging.Formatter(fmt=LOG_FORMAT, datefmt=DATE_FORMAT)

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler
    target_log_dir = Path(log_dir) if log_dir else DEFAULT_LOG_DIR
    try:
        target_log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(target_log_dir / log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except OSError as exc:
        # Fallback to console only if filesystem permissions prevent log creation
        logger.warning(f"Unable to initialize file handler in {target_log_dir}: {exc}")

    return logger

