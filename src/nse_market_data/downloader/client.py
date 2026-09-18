"""HTTP Client for communicating with NSE India endpoints."""

import json
import logging
import time
from typing import Any, Dict, Optional, Set

import requests

from nse_market_data.config import (
    DEFAULT_BACKOFF_FACTOR,
    DEFAULT_HEADERS,
    DEFAULT_MAX_RETRIES,
    DEFAULT_TIMEOUT_SECONDS,
    NSE_BASE_URL,
)
from nse_market_data.downloader.exceptions import (
    NSEConnectionError,
    NSEHTTPError,
    NSEResponseParsingError,
    NSETimeoutError,
)

logger = logging.getLogger("nse_market_data.downloader")

RETRYABLE_STATUS_CODES: Set[int] = {429, 500, 502, 503, 504}


class NSEClient:
    """Manages an HTTP session with NSE India, applying realistic headers,
    handling cookies, executing requests with exponential backoff retries,
    and decoding JSON payloads safely.
    """

    def __init__(
        self,
        timeout: int = DEFAULT_TIMEOUT_SECONDS,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
        session: Optional[requests.Session] = None,
    ):
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.session = session or requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        self._session_initialized = False

    def initialize_session(self, force: bool = False) -> None:
        """Visits base URL to establish initial cookies if not already done."""
        if self._session_initialized and not force:
            return

        logger.info(f"Initializing NSE session via {NSE_BASE_URL}")
        try:
            resp = self.session.get(
                NSE_BASE_URL,
                timeout=self.timeout,
                headers={"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"},
            )
            # NSE sometimes responds with 200 or 403 on homepage to automated bots,
            # but API endpoints may still succeed with session cookies established.
            self._session_initialized = True
            logger.debug(f"Session initialized with status {resp.status_code}")
        except requests.exceptions.RequestException as exc:
            logger.warning(f"Session initialization encountered non-fatal error: {exc}")
            self._session_initialized = True

    def get_json(self, url: str, custom_headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Performs a GET request against an NSE JSON endpoint with retries and backoff.

        Raises:
            NSETimeoutError: On request timeout.
            NSEConnectionError: On network or socket failure.
            NSEHTTPError: On non-200 HTTP response.
            NSEResponseParsingError: On malformed JSON, empty response, or HTML error page.
        """
        headers = self.session.headers.copy()
        if custom_headers:
            headers.update(custom_headers)

        last_error: Optional[Exception] = None

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Requesting {url} (Attempt {attempt}/{self.max_retries})")
                response = self.session.get(url, headers=headers, timeout=self.timeout)

                # Check HTTP status
                if response.status_code != 200:
                    if response.status_code in RETRYABLE_STATUS_CODES and attempt < self.max_retries:
                        sleep_time = self.backoff_factor * (2 ** (attempt - 1))
                        logger.warning(
                            f"HTTP {response.status_code} received from {url}. Retrying in {sleep_time:.1f}s..."
                        )
                        time.sleep(sleep_time)
                        continue
                    raise NSEHTTPError(
                        f"HTTP request failed with status {response.status_code}: {response.reason}",
                        status_code=response.status_code,
                    )

                # Check for empty response
                raw_text = response.text.strip()
                if not raw_text:
                    raise NSEResponseParsingError("Empty response body received from NSE.")

                # Check if response returned an HTML error page instead of JSON
                if raw_text.startswith("<!DOCTYPE") or raw_text.startswith("<html"):
                    raise NSEResponseParsingError(
                        "Received HTML webpage or error page instead of expected JSON API data."
                    )

                # Parse JSON
                try:
                    data = response.json()
                except (json.JSONDecodeError, ValueError) as json_err:
                    raise NSEResponseParsingError(f"Malformed JSON in response: {json_err}") from json_err

                if not isinstance(data, dict):
                    raise NSEResponseParsingError(
                        f"Expected JSON object (dict), received {type(data).__name__} instead."
                    )

                return data

            except requests.exceptions.Timeout as exc:
                last_error = NSETimeoutError(f"Request to {url} timed out after {self.timeout}s")
                if attempt < self.max_retries:
                    sleep_time = self.backoff_factor * (2 ** (attempt - 1))
                    logger.warning(f"Timeout on {url}. Retrying in {sleep_time:.1f}s...")
                    time.sleep(sleep_time)
                else:
                    logger.error(f"Request to {url} permanently timed out.")
                    raise last_error from exc

            except requests.exceptions.ConnectionError as exc:
                last_error = NSEConnectionError(f"Network connection failed for {url}: {exc}")
                if attempt < self.max_retries:
                    sleep_time = self.backoff_factor * (2 ** (attempt - 1))
                    logger.warning(f"Connection error on {url}. Retrying in {sleep_time:.1f}s...")
                    time.sleep(sleep_time)
                else:
                    logger.error(f"Network connection permanently failed for {url}.")
                    raise last_error from exc

            except (NSEHTTPError, NSEResponseParsingError):
                # Non-retryable HTTP error or parsing issue - re-raise immediately
                raise

            except Exception as exc:
                logger.error(f"Unexpected error requesting {url}: {exc}")
                raise NSEDownloaderError(f"Unexpected error: {exc}") from exc

        if last_error:
            raise last_error
        raise NSEDownloaderError(f"Failed to acquire data from {url}")

