from errors.base import UnretryableError


class AuthenticationError(UnretryableError):
    pass

class ValidationError(UnretryableError):
    pass

class InsufficientFundsError(UnretryableError):
    pass

class AccountError(UnretryableError):
    pass

class RetriesExhaustedError(UnretryableError):
    pass