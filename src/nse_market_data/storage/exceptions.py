"""Custom exceptions for the CSV storage layer."""


class StorageError(Exception):
    """Base exception for storage errors."""

    pass


class StorageDirectoryError(StorageError):
    """Raised when the target storage directory cannot be created or accessed."""

    pass


class StorageWriteError(StorageError):
    """Raised when writing to CSV file fails."""

    pass

