class InvalidFileError(Exception):
    """Exception raised for invalid files."""

    def __init__(
        self,
        message: str,
        reason: str = "invalid file",
        checksum: str | None = None,
    ) -> None:
        super().__init__(message)
        self.reason = reason
        self.checksum = checksum
