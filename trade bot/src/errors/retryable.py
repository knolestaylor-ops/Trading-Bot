from errors.base import RetryableError


class NetworkError(RetryableError):
    pass

class RateLimitError(RetryableError):
    def __init__(self, message="Rate limit exceeded", *, retry_after=None, context=None):
        super().__init__(message, context=context)
        self.retry_after = retry_after

class ServerError(RetryableError):
    pass

class DataError(RetryableError):
    pass