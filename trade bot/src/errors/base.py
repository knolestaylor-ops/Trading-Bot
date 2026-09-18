

class TradeBotError(Exception):
    def __init__(self, message, *, context=None):
        super().__init__(message)
        self.context = context or {}

class RetryableError(TradeBotError):
    pass


class UnretryableError(TradeBotError):
    pass