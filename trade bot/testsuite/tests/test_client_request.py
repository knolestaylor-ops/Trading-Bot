import pytest
from errors.retryable import RetryableError
from errors.unretryable import UnretryableError


class DummyResponse:
    def __init__(self, status_code=200, text="", json_data=None):
        self.status_code = status_code
        self.text = text
        self._json_data = json_data

    def json(self):
        if self._json_data is None:
            raise ValueError("No JSON")
        return self._json_data


# ---------------------------------------------------------------------
# _request core behavior
# ---------------------------------------------------------------------

def test_request_uses_base_url_for_non_historical(client):
    client.session.response = DummyResponse(
        status_code=200,
        text='{"ok": true}',
        json_data={"ok": True},
    )

    data = client._request("GET", "/v2/account")

    assert data == {"ok": True}
    assert client.session.last_request["url"] == (
        client.base_url + "/v2/account"
    )


def test_request_uses_historical_url_for_allowed_suffix(client):
    client.session.response = DummyResponse(
        status_code=200,
        text='{"bars": []}',
        json_data={"bars": []},
    )

    data = client._request("GET", "/v2/stocks/AAPL/bars")

    assert data == {"bars": []}
    assert client.session.last_request["url"] == (
        client.historical_url + "/v2/stocks/AAPL/bars"
    )


def test_request_returns_none_on_empty_body(client):
    client.session.response = DummyResponse(
        status_code=200,
        text="",
        json_data=None,
    )

    result = client._request("GET", "/v2/account")
    assert result is None


def test_request_raises_unretryable_on_bad_json(client):
    client.session.response = DummyResponse(
        status_code=200,
        text="not-json",
        json_data=None,  # json() will raise ValueError
    )

    with pytest.raises(UnretryableError):
        client._request("GET", "/v2/account")


# ---------------------------------------------------------------------
# Error mapping
# ---------------------------------------------------------------------

def test_request_raises_retryable_on_5xx(client):
    client.session.response = DummyResponse(
        status_code=503,
        text="server down",
        json_data=None,
    )

    with pytest.raises(RetryableError):
        client._request("GET", "/v2/account")


def test_request_raises_retryable_on_408_429(client):
    client.session.response = DummyResponse(
        status_code=429,
        text="rate limit",
        json_data=None,
    )

    with pytest.raises(RetryableError):
        client._request("GET", "/v2/account")


def test_request_raises_unretryable_on_4xx(client):
    client.session.response = DummyResponse(
        status_code=400,
        text="bad request",
        json_data=None,
    )

    with pytest.raises(UnretryableError):
        client._request("GET", "/v2/account")
