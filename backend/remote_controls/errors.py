class BackendAPIError(Exception):
    """
    API-safe error that Flask can return without leaking stack traces.
    """
    def __init__(
        self,
        code: str,
        message: str,
        http_status: int = 500,
        details: str | None = None,
    ):
        super().__init__(message)
        self.code = code
        self.message = message
        self.http_status = http_status
        self.details = details