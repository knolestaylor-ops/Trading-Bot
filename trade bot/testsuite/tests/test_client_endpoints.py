import pytest


class DummyResponse:
    def __init__(self, status_code=200, text="", json_data=None):
        self.status_code = status_code
        self.text = text
        self._json_data = json_data

    def json(self):
        return self._json_data


# ---------------------------------------------------------------------
# Simple wrappers: account, orders, positions, etc.
# We just verify they call _request with the right method/endpoint.
# ---------------------------------------------------------------------

def _set_response(client, json_data):
    client.session.response = DummyResponse(
        status_code=200,
        text="ok",
        json_data=json_data,
    )


def test_get_account_calls_correct_endpoint(client):
    _set_response(client, {"id": "acct"})
    data = client.get_account()

    assert data == {"id": "acct"}
    assert client.session.last_request["method"] == "GET"
    assert client.session.last_request["url"].endswith("/v2/account")


def test_submit_order_uses_orders_endpoint(client):
    payload = {"symbol": "AAPL", "qty": 1}
    _set_response(client, {"id": "order123"})

    data = client.submit_order(payload)

    assert data == {"id": "order123"}
    assert client.session.last_request["method"] == "POST"
    assert client.session.last_request["url"].endswith("/v2/orders")
    assert client.session.last_request["kwargs"]["json"] == payload


def test_get_bars_uses_historical_base_and_params(client):
    _set_response(client, {"bars": [1, 2, 3]})

    data = client.get_bars("AAPL", timeframe="5min", limit=50)

    assert data == {"bars": [1, 2, 3]}
    assert client.session.last_request["url"].startswith(client.historical_url)
    assert client.session.last_request["url"].endswith("/v2/stocks/AAPL/bars")
    assert client.session.last_request["kwargs"]["json"] == {
        "timeframe": "5min",
        "limit": 50,
    }
