"""Every AlpacaClient endpoint wrapper: HTTP method, URL, request body/params."""
import pytest

from ingestion import alpaca_client as alpaca_module
from support import DATA_URL, TRADING_URL


def routed_to_trading_api(reason="the base URL is chosen from the last path segment "
                                 "('latest'/'snapshot'), so market-data calls go to the trading API"):
    return pytest.mark.xfail(reason=reason)


ENDPOINTS = [
    # (method name, args, HTTP method, full URL)
    ("get_account", (), "GET", TRADING_URL + "/v2/account"),
    ("get_account_config", (), "GET", TRADING_URL + "/v2/account/configurations"),
    ("patch_account_config", (), "PATCH", TRADING_URL + "/v2/account/configurations"),
    ("get_account_activities", (), "GET", TRADING_URL + "/v2/account/activities"),
    ("filter_account_activities", ("FILL",), "GET", TRADING_URL + "/v2/account/activities/FILL"),
    ("get_portfolio_history", (), "GET", TRADING_URL + "/v2/portfolio_history"),
    ("list_assets", (), "GET", TRADING_URL + "/v2/assets"),
    ("get_US_market_calendar", (), "GET", TRADING_URL + "/v2/calendar"),
    ("get_clock", (), "GET", TRADING_URL + "/v2/clock"),
    ("get_open_positions", (), "GET", TRADING_URL + "/v2/positions"),
    ("close_all_positions", (), "DELETE", TRADING_URL + "/v2/positions"),
    ("get_position", ("AAPL",), "GET", TRADING_URL + "/v2/positions/AAPL"),
    ("close_position", ("AAPL",), "DELETE", TRADING_URL + "/v2/positions/AAPL"),
    ("exercise_options_position", ("AAPL240119C00100000",), "POST",
     TRADING_URL + "/v2/positions/AAPL240119C00100000/exercise"),
    ("get_all_watchlist", (), "GET", TRADING_URL + "/v2/watchlists"),
    ("create_watchlist", (), "POST", TRADING_URL + "/v2/watchlists"),
    ("get_watchlist_by_id", ("w1",), "GET", TRADING_URL + "/v2/watchlists/w1"),
    ("update_watchlist_by_id", ("w1",), "PUT", TRADING_URL + "/v2/watchlists/w1"),
    ("add_asset_to_watchlist", ("w1",), "POST", TRADING_URL + "/v2/watchlists/w1"),
    ("delete_watchlist_by_id", ("w1",), "DELETE", TRADING_URL + "/v2/watchlists/w1"),
    ("get_watchlist_by_name", ("tech",), "GET", TRADING_URL + "/v2/watchlists:by_name"),
    ("update_watchlist_by_name", ("tech",), "PUT", TRADING_URL + "/v2/watchlists:by_name"),
    ("add_asset_to_watchlist_by_name", ("tech",), "POST", TRADING_URL + "/v2/watchlists:by_name"),
    ("delete_watchlist_by_name", ("tech",), "DELETE", TRADING_URL + "/v2/watchlists:by_name"),
    ("delete_symbol_from_watchlist", ("w1", "AAPL"), "DELETE", TRADING_URL + "/v2/watchlists/w1/AAPL"),
    ("liquidate_order", ("AAPL",), "DELETE", TRADING_URL + "/v2/positions/AAPL"),
    ("see_orders", (), "GET", TRADING_URL + "/v2/orders"),
    ("get_order", ("o1",), "GET", TRADING_URL + "/v2/orders/o1"),
    ("cancel_order", ("o1",), "DELETE", TRADING_URL + "/v2/orders/o1"),
    ("cancel_all_orders", (), "DELETE", TRADING_URL + "/v2/orders"),
    ("get_bars", ("AAPL",), "GET", DATA_URL + "/v2/stocks/AAPL/bars"),
    pytest.param("get_last_trade", ("AAPL",), "GET", DATA_URL + "/v2/stocks/AAPL/trades/latest",
                 marks=routed_to_trading_api()),
    pytest.param("get_last_quote", ("AAPL",), "GET", DATA_URL + "/v2/stocks/AAPL/quotes/latest",
                 marks=routed_to_trading_api()),
    pytest.param("get_snapshot", ("AAPL",), "GET", DATA_URL + "/v2/stocks/AAPL/snapshot",
                 marks=routed_to_trading_api()),
]


@pytest.mark.parametrize("name, args, http_method, url", ENDPOINTS)
def test_endpoint_calls_correct_method_and_url(client, respond, name, args, http_method, url):
    respond({"ok": True})

    result = getattr(client, name)(*args)

    assert result == {"ok": True}
    assert len(client.session.calls) == 1
    assert client.session.last_request["method"] == http_method
    assert client.session.last_request["url"] == url


def test_submit_order_posts_payload_as_json(client, respond):
    payload = {"symbol": "AAPL", "qty": "1", "side": "buy", "type": "market", "time_in_force": "day"}
    respond({"id": "order123"})

    assert client.submit_order(payload) == {"id": "order123"}
    assert client.session.last_request["method"] == "POST"
    assert client.session.last_request["url"] == TRADING_URL + "/v2/orders"
    assert client.session.last_request["kwargs"]["json"] == payload


def test_replace_order_patches_payload_as_json(client, respond):
    respond({"id": "o1"})

    client.replace_order("o1", {"qty": "2"})

    assert client.session.last_request["method"] == "PATCH"
    assert client.session.last_request["url"] == TRADING_URL + "/v2/orders/o1"
    assert client.session.last_request["kwargs"]["json"] == {"qty": "2"}


# Replaces the old test, which asserted the bug (bars options sent as a JSON body).
@pytest.mark.xfail(reason="get_bars sends its options as a JSON body on a GET; they must be query params")
def test_get_bars_sends_query_params(client, respond):
    respond({"bars": []})

    client.get_bars("AAPL", timeframe="5Min", limit=50)

    kwargs = client.session.last_request["kwargs"]
    assert kwargs.get("params") == {"timeframe": "5Min", "limit": 50}
    assert "json" not in kwargs


@pytest.mark.xfail(reason="the default timeframe '1min' is not a valid Alpaca timeframe ('1Min')")
def test_get_bars_default_timeframe_is_valid(client, respond):
    respond({"bars": []})

    client.get_bars("AAPL")

    sent = client.session.last_request["kwargs"]
    options = sent.get("params") or sent.get("json")
    assert options["timeframe"] == "1Min"


@pytest.mark.xfail(reason="the *_by_name watchlist methods ignore their `name` argument")
def test_watchlist_by_name_sends_name(client, respond):
    respond({})

    client.get_watchlist_by_name("tech")

    assert client.session.last_request["kwargs"].get("params") == {"name": "tech"}


# ---------------------------------------------------------------------
# Construction: credentials and base URLs
# ---------------------------------------------------------------------

def test_sends_credentials_as_alpaca_headers(client):
    assert client.session.headers["APCA-API-KEY-ID"] == "test_key"
    assert client.session.headers["APCA-API-SECRET-KEY"] == "test_secret"


def test_defaults_to_paper_trading(client):
    """Safety guard: the client must never point at the live trading API by default."""
    assert client.base_url == TRADING_URL
    assert client.historical_url == DATA_URL


@pytest.mark.xfail(reason="API_KEY/API_SECRET are read once at import time, not when the client is created")
def test_credentials_are_read_from_environment_at_construction(monkeypatch):
    monkeypatch.setenv("API_KEY", "env_key")
    monkeypatch.setenv("API_SECRET", "env_secret")

    c = alpaca_module.AlpacaClient()

    assert c.session.headers["APCA-API-KEY-ID"] == "env_key"


@pytest.mark.xfail(reason="missing credentials silently become the string 'None' instead of failing fast")
def test_missing_credentials_fail_fast(monkeypatch):
    monkeypatch.delenv("API_KEY", raising=False)
    monkeypatch.delenv("API_SECRET", raising=False)

    with pytest.raises(Exception):
        alpaca_module.AlpacaClient()
