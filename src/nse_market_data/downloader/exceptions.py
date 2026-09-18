"""Custom exceptions for the NSE Data Acquisition module."""


class NSEDownloaderError(Exception):
    """Base exception for all NSE Downloader operations."""

    pass


class NSEConnectionError(NSEDownloaderError):
    """Raised when a network or DNS connection to NSE fails."""

    pass


class NSETimeoutError(NSEDownloaderError):
    """Raised when an HTTP request to NSE times out."""

    pass


class NSEHTTPError(NSEDownloaderError):
    """Raised when an HTTP error status code is received from NSE."""

    def __init__(self, message: str, status_code: int):
        super().__init__(message)
        self.status_code = status_code


class NSEResponseParsingError(NSEDownloaderError):
    """Raised when an NSE response cannot be parsed as expected JSON."""

    pass


class NSEDataExtractionError(NSEDownloaderError):
    """Raised when expected data fields or tabular arrays are absent in the response."""

    pass

