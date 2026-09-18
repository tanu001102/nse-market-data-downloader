"""Custom exceptions for the Data Validation layer."""


class ValidationError(Exception):
    """Base exception for validation errors."""

    pass


class EmptyDatasetError(ValidationError):
    """Raised when an acquired dataset contains no records."""

    pass


class InvalidDataStructureError(ValidationError):
    """Raised when data structure is not a list of dictionaries."""

    pass


class MissingColumnsError(ValidationError):
    """Raised when mandatory schema keys are absent from records."""

    def __init__(self, message: str, missing_columns: list[str]):
        super().__init__(message)
        self.missing_columns = missing_columns


class UnusableRecordError(ValidationError):
    """Raised when records lack critical identifying values."""

    pass

