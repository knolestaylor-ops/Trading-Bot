"""AlpacaClient._request: the function body, and the behaviour seen through its decorators."""
import pytest
import requests

from errors.base import RetryableError, TradeBotError, UnretryableError
from errors.unretryable import AuthenticationError, RetriesExhaustedError
from ingestion.alpaca_client import AlpacaClient
from support import DATA_URL, TRADING_URL, DummyResponse

# `_request` is wrapped as retry(safe_api_call(body)); functools.wraps exposes each layer.
raw_request = AlpacaClient._request.__wrapped__.__wrapped__

RETRY_BUG = (
    "safe_api_call's `except Exception` turns RetryableError into UnretryableError, "
    "so @retry never retries"
)


def ok(json_data):
    return DummyResponse(status_code=200, json_data=json_data)


# ---------------------------------------------------------------------
# Undecorated body: URL routing, status mapping, JSON parsing
# ---------------------------------------------------------------------

class TestRequestBody:

    def test_uses_trading_url_for_account_endpoints(self, client):
        client.session.response = ok({"ok": True})

        assert raw_request(client, "GET", "/v2/account") == {"ok": True}
        assert client.session.last_request["url"] == TRADING_URL + "/v2/account"

    @pytest.mark.parametrize("kind", ["bars", "auctions", "quotes", "trades"])
    def test_uses_data_url_for_historical_endpoints(self, client, kind):
        client.session.response = ok({kind: []})

        raw_request(client, "GET", f"/v2/stocks/AAPL/{kind}")

        assert client.session.last_request["url"] == f"{DATA_URL}/v2/stocks/AAPL/{kind}"

    def test_forwards_method_and_kwargs_to_session(self, client):
        client.session.response = ok({})

        raw_request(client, "POST", "/v2/orders", json={"symbol": "AAPL"}, params={"a": 1})

        call = client.session.last_request
        assert call["method"] == "POST"
        assert call["kwargs"] == {"json": {"symbol": "AAPL"}, "params": {"a": 1}}

    def test_returns_none_on_empty_body(self, client):
        client.session.response = DummyResponse(status_code=204, text="")

        assert raw_request(client, "DELETE", "/v2/orders") is None

    def test_raises_unretryable_on_bad_json(self, client):
        client.session.response = DummyResponse(status_code=200, text="not-json")

        with pytest.raises(UnretryableError, match="parse JSON"):
            raw_request(client, "GET", "/v2/account")

    @pytest.mark.parametrize("status", [500, 502, 503, 599])
    def test_raises_retryable_on_5xx(self, client, status):
        client.session.response = DummyResponse(status_code=status, text="server down")

        with pytest.raises(RetryableError, match=str(status)):
            raw_request(client, "GET", "/v2/account")

    @pytest.mark.parametrize("status", [408, 429])
    def test_raises_retryable_on_timeout_and_rate_limit(self, client, status):
        client.session.response = DummyResponse(status_code=status, text="slow down")

        with pytest.raises(RetryableError, match=str(status)):
            raw_request(client, "GET", "/v2/account")

    @pytest.mark.parametrize("status", [400, 401, 403, 404, 422])
    def test_raises_unretryable_on_other_4xx(self, client, status):
        client.session.response = DummyResponse(status_code=status, text="bad request")

        with pytest.raises(UnretryableError, match="bad request"):
            raw_request(client, "GET", "/v2/account")

    @pytest.mark.parametrize("exc", [requests.ConnectionError("down"), requests.Timeout("slow")])
    def test_network_failures_are_retryable(self, client, exc):
        client.session.queue = [exc]

        with pytest.raises(RetryableError, match="Network issue"):
            raw_request(client, "GET", "/v2/account")

    def test_2xx_status_codes_are_not_errors(self, client):
        client.session.response = DummyResponse(status_code=201, json_data={"id": "o1"})

        assert raw_request(client, "POST", "/v2/orders") == {"id": "o1"}


# ---------------------------------------------------------------------
# Public behaviour: what callers of client._request actually get
# ---------------------------------------------------------------------

class TestRequestThroughDecorators:

    def test_success_returns_parsed_json_in_one_call(self, client, sleeps):
        client.session.response = ok({"id": "acct"})

        assert client._request("GET", "/v2/account") == {"id": "acct"}
        assert len(client.session.calls) == 1
        assert sleeps == []

    def test_client_error_is_not_retried(self, client, sleeps):
        client.session.response = DummyResponse(status_code=400, text="bad request")

        with pytest.raises(UnretryableError):
            client._request("GET", "/v2/account")

        assert len(client.session.calls) == 1
        assert sleeps == []

    def test_submit_order_is_never_sent_twice_after_a_timeout(self, client):
        """Regression guard: blindly retrying a POST /v2/orders can place duplicate orders.

        This passes today only because retries are broken; it must keep passing after
        they're fixed (e.g. by not retrying order submission, or by using client_order_id).
        """
        client.session.queue = [requests.Timeout("read timed out")]
        client.session.response = ok({"id": "o1"})

        try:
            client.submit_order({"symbol": "AAPL", "qty": "1"})
        except TradeBotError:
            pass

        order_posts = [c for c in client.session.calls if c["method"] == "POST"]
        assert len(order_posts) == 1

    @pytest.mark.xfail(reason=RETRY_BUG)
    def test_server_error_is_retried_then_exhausted(self, client):
        client.session.response = DummyResponse(status_code=503, text="server down")

        with pytest.raises(RetriesExhaustedError) as excinfo:
            client._request("GET", "/v2/account")

        assert len(client.session.calls) == 3
        assert excinfo.value.context["attempts"] == 3

    @pytest.mark.xfail(reason=RETRY_BUG)
    def test_transient_server_error_recovers(self, client):
        client.session.queue = [DummyResponse(status_code=503, text="down"), ok({"id": "acct"})]

        assert client._request("GET", "/v2/account") == {"id": "acct"}
        assert len(client.session.calls) == 2

    @pytest.mark.xfail(reason=RETRY_BUG)
    def test_rate_limit_is_retried(self, client):
        client.session.queue = [DummyResponse(status_code=429, text="slow down"), ok({"id": "acct"})]

        assert client._request("GET", "/v2/account") == {"id": "acct"}

    @pytest.mark.xfail(reason=RETRY_BUG)
    def test_connection_error_is_retried(self, client):
        client.session.queue = [requests.ConnectionError("down"), ok({"id": "acct"})]

        assert client._request("GET", "/v2/account") == {"id": "acct"}

    @pytest.mark.xfail(reason="safe_api_call raises DataError on a None result, so empty "
                              "204 responses (e.g. DELETE) are retried 3 times and then fail")
    def test_empty_body_returns_none(self, client):
        client.session.response = DummyResponse(status_code=204, text="")

        assert client.cancel_all_orders() is None
        assert len(client.session.calls) == 1

    @pytest.mark.xfail(reason="401 is reported as a generic UnretryableError, not AuthenticationError")
    def test_unauthorized_raises_authentication_error(self, client):
        client.session.response = DummyResponse(status_code=401, text="unauthorized")

        with pytest.raises(AuthenticationError):
            client._request("GET", "/v2/account")

    @pytest.mark.xfail(reason="no timeout is passed to session.request, so a dead connection hangs forever")
    def test_every_request_has_a_timeout(self, client):
        client.session.response = ok({})

        client.get_account()

        assert client.session.last_request["kwargs"].get("timeout")
