"""The exception hierarchy that drives retry decisions."""
import pytest

from errors.base import RetryableError, TradeBotError, UnretryableError
from errors.retryable import DataError, NetworkError, RateLimitError, ServerError
from errors.unretryable import (
    AccountError,
    AuthenticationError,
    InsufficientFundsError,
    RetriesExhaustedError,
    ValidationError,
)

RETRYABLE = [NetworkError, RateLimitError, ServerError, DataError]
UNRETRYABLE = [AuthenticationError, ValidationError, InsufficientFundsError, AccountError, RetriesExhaustedError]


@pytest.mark.parametrize("cls", RETRYABLE)
def test_retryable_errors(cls):
    assert issubclass(cls, RetryableError)
    assert not issubclass(cls, UnretryableError)


@pytest.mark.parametrize("cls", UNRETRYABLE)
def test_unretryable_errors(cls):
    assert issubclass(cls, UnretryableError)
    assert not issubclass(cls, RetryableError)


@pytest.mark.parametrize("cls", [RetryableError, UnretryableError, *RETRYABLE, *UNRETRYABLE])
def test_all_errors_share_a_base_class(cls):
    assert issubclass(cls, TradeBotError)
    assert issubclass(cls, Exception)


def test_message_and_context():
    err = TradeBotError("failed", context={"symbol": "AAPL"})

    assert str(err) == "failed"
    assert err.context == {"symbol": "AAPL"}


def test_context_defaults_to_a_fresh_dict():
    first, second = TradeBotError("a"), TradeBotError("b")
    first.context["key"] = "value"

    assert second.context == {}


def test_context_is_keyword_only():
    with pytest.raises(TypeError):
        TradeBotError("msg", {"positional": True})


def test_rate_limit_error_defaults():
    err = RateLimitError()

    assert str(err) == "Rate limit exceeded"
    assert err.retry_after is None
    assert err.context == {}


def test_rate_limit_error_keeps_retry_after():
    err = RateLimitError(retry_after=30, context={"endpoint": "/v2/orders"})

    assert err.retry_after == 30
    assert err.context == {"endpoint": "/v2/orders"}


@pytest.mark.xfail(reason="design: DataError is raised for invalid order input, which "
                          "can never succeed on retry, so it should not be retryable")
def test_data_error_is_not_retryable():
    assert not issubclass(DataError, RetryableError)
