"""utils.decorators.retry and utils.decorators.safe_api_call, tested on plain functions."""
import json
from types import SimpleNamespace

import pytest
import requests

from errors.base import RetryableError, UnretryableError
from errors.retryable import DataError, NetworkError, RateLimitError, ServerError
from errors.unretryable import AccountError, AuthenticationError, RetriesExhaustedError
from utils.decorators import retry, safe_api_call


def scripted(*outcomes):
    """A function that returns or raises `outcomes` in order and records its calls."""
    calls = []

    def fn(*args, **kwargs):
        calls.append((args, kwargs))
        outcome = outcomes[len(calls) - 1]
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome

    return fn, calls


# ---------------------------------------------------------------------
# retry
# ---------------------------------------------------------------------

class TestRetry:

    def test_returns_first_success_without_sleeping(self, sleeps):
        fn, calls = scripted("ok")

        assert retry(fn)() == "ok"
        assert len(calls) == 1
        assert sleeps == []

    def test_forwards_arguments(self):
        fn, calls = scripted("ok")

        retry(fn)(1, 2, key="value")

        assert calls == [((1, 2), {"key": "value"})]

    def test_retries_retryable_errors_until_success(self, sleeps):
        fn, calls = scripted(RetryableError("a"), NetworkError("b"), "ok")

        assert retry(fn)() == "ok"
        assert len(calls) == 3
        assert sleeps == [0.3, 0.6]

    def test_raises_retries_exhausted_after_three_attempts(self):
        fn, calls = scripted(ServerError("one"), ServerError("two"), ServerError("last"))

        with pytest.raises(RetriesExhaustedError) as excinfo:
            retry(fn)()

        assert len(calls) == 3
        assert excinfo.value.context == {"last_error": "last", "attempts": 3}
        assert isinstance(excinfo.value, UnretryableError)

    def test_backoff_is_exponential(self, sleeps):
        fn, _ = scripted(*[RetryableError("x")] * 3)

        with pytest.raises(RetriesExhaustedError):
            retry(fn)()

        assert sleeps[:2] == [0.3, 0.6]

    @pytest.mark.xfail(reason="retry sleeps after the final attempt even though nothing follows")
    def test_does_not_sleep_after_final_attempt(self, sleeps):
        fn, _ = scripted(*[RetryableError("x")] * 3)

        with pytest.raises(RetriesExhaustedError):
            retry(fn)()

        assert sleeps == [0.3, 0.6]

    @pytest.mark.xfail(reason="RetriesExhaustedError is raised without `from`, losing the original traceback")
    def test_exhausted_error_chains_the_last_failure(self):
        fn, _ = scripted(*[ServerError("x")] * 3)

        with pytest.raises(RetriesExhaustedError) as excinfo:
            retry(fn)()

        assert isinstance(excinfo.value.__cause__, ServerError)

    @pytest.mark.parametrize("error", [UnretryableError("no"), AuthenticationError("bad key")])
    def test_does_not_retry_unretryable_errors(self, error, sleeps):
        fn, calls = scripted(error, "never reached")

        with pytest.raises(type(error)) as excinfo:
            retry(fn)()

        assert excinfo.value is error
        assert len(calls) == 1
        assert sleeps == []

    def test_does_not_retry_unrelated_exceptions(self):
        fn, calls = scripted(ValueError("bug"), "never reached")

        with pytest.raises(ValueError):
            retry(fn)()

        assert len(calls) == 1

    def test_preserves_function_metadata(self):
        def fetch_account():
            """Docstring."""

        wrapped = retry(fetch_account)

        assert wrapped.__name__ == "fetch_account"
        assert wrapped.__doc__ == "Docstring."
        assert wrapped.__wrapped__ is fetch_account


# ---------------------------------------------------------------------
# safe_api_call
# ---------------------------------------------------------------------

def guarded(result=None, raises=None):
    """Call a safe_api_call-wrapped method that returns `result` or raises `raises`."""

    @safe_api_call
    def method(self):
        if raises is not None:
            raise raises
        return result

    return method(object())


def http_error(status):
    return requests.HTTPError(f"HTTP {status}", response=SimpleNamespace(status_code=status))


class TestSafeApiCall:

    @pytest.mark.parametrize("result", [{"id": 1}, [], 0, ""])
    def test_returns_non_none_results_unchanged(self, result):
        assert guarded(result=result) == result

    def test_none_result_raises_data_error(self):
        with pytest.raises(DataError, match="Empty response"):
            guarded(result=None)

    @pytest.mark.parametrize("exc", [
        requests.Timeout("slow"),
        requests.ConnectTimeout("slow connect"),
        requests.ConnectionError("down"),
    ])
    def test_network_failures_become_network_error(self, exc):
        with pytest.raises(NetworkError):
            guarded(raises=exc)

    @pytest.mark.parametrize("status, expected", [
        (401, AuthenticationError),
        (403, AccountError),
        (429, RateLimitError),
        (500, ServerError),
        (503, ServerError),
    ])
    def test_http_errors_are_classified_by_status(self, status, expected):
        with pytest.raises(expected):
            guarded(raises=http_error(status))

    @pytest.mark.parametrize("status", [400, 404, 418])
    def test_other_http_errors_are_generic_unretryable(self, status):
        with pytest.raises(UnretryableError) as excinfo:
            guarded(raises=http_error(status))

        assert type(excinfo.value) is UnretryableError
        assert str(status) in str(excinfo.value)

    def test_malformed_json_becomes_data_error(self):
        with pytest.raises(DataError, match="Malformed JSON"):
            guarded(raises=json.JSONDecodeError("Expecting value", "doc", 0))

    def test_unexpected_exceptions_become_unretryable(self):
        with pytest.raises(UnretryableError, match="Unexpected error: 'missing'"):
            guarded(raises=KeyError("missing"))

    @pytest.mark.xfail(reason="`except Exception` re-wraps the project's own errors as "
                              "UnretryableError, which is why retries never happen")
    @pytest.mark.parametrize("error", [
        RetryableError("transient"),
        RateLimitError(),
        AuthenticationError("bad key"),
    ])
    def test_project_errors_pass_through_unchanged(self, error):
        with pytest.raises(type(error)) as excinfo:
            guarded(raises=error)

        assert excinfo.value is error

    def test_preserves_function_metadata(self):
        def get_clock(self):
            pass

        assert safe_api_call(get_clock).__name__ == "get_clock"
