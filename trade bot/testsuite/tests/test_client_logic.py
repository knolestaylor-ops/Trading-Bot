"""AlpacaClient helpers that transform responses rather than just forwarding them."""
from types import SimpleNamespace

import pandas as pd
import pytest

from ingestion import alpaca_client as alpaca_module

# ---------------------------------------------------------------------
# Portfolio history table
# ---------------------------------------------------------------------

HISTORY = {
    "timestamp": [1700000000, 1700000600],
    "equity": [10000.0, 10100.0],
    "profit_loss": [0.0, 100.0],
    "profit_loss_pct": [0.0, 0.01],
    "base_value": 10000.0,
    "timeframe": "5Min",
}


def test_portfolio_history_table_builds_dataframe(client, respond):
    respond(HISTORY)

    df = client.get_portfolio_history_table()

    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == ["timestamp", "equity", "profit_loss", "profit_loss_pct"]
    assert df["equity"].tolist() == [10000.0, 10100.0]
    assert df["profit_loss_pct"].tolist() == [0.0, 0.01]


def test_portfolio_history_table_converts_unix_seconds_to_datetime(client, respond):
    respond(HISTORY)

    df = client.get_portfolio_history_table()

    assert pd.api.types.is_datetime64_any_dtype(df["timestamp"])
    assert df["timestamp"].iloc[0] == pd.Timestamp("2023-11-14 22:13:20")
    assert df["timestamp"].iloc[1] - df["timestamp"].iloc[0] == pd.Timedelta(minutes=10)


def test_portfolio_history_table_handles_empty_history(client, respond):
    respond({"timestamp": [], "equity": [], "profit_loss": [], "profit_loss_pct": []})

    df = client.get_portfolio_history_table()

    assert df.empty
    assert list(df.columns) == ["timestamp", "equity", "profit_loss", "profit_loss_pct"]


def test_portfolio_history_table_requests_portfolio_history(client, respond):
    respond(HISTORY)

    client.get_portfolio_history_table()

    assert client.session.last_request["url"].endswith("/v2/portfolio_history")


# ---------------------------------------------------------------------
# Account helpers (Alpaca returns numbers as strings)
# ---------------------------------------------------------------------

ACCOUNT = {
    "buying_power": "5000",
    "equity": "10000",
    "last_equity": "9500",
    "cash": "2000.55",
}


def test_account_helpers_parse_numeric_strings(client):
    assert client.get_buying_power(ACCOUNT) == 5000.0
    assert client.get_equity(ACCOUNT) == 10000.0
    assert client.get_cash(ACCOUNT) == 2000.55


@pytest.mark.parametrize("equity, last_equity, change", [
    ("10000", "9500", 500.0),
    ("9000", "9500", -500.0),
    ("9500", "9500", 0.0),
])
def test_balance_change_is_equity_minus_last_equity(client, equity, last_equity, change):
    assert client.get_balance_change({"equity": equity, "last_equity": last_equity}) == change


@pytest.mark.parametrize("helper", ["get_buying_power", "get_equity", "get_cash", "get_balance_change"])
def test_account_helpers_raise_on_missing_field(client, helper):
    with pytest.raises(KeyError):
        getattr(client, helper)({})


# ---------------------------------------------------------------------
# Assets
# ---------------------------------------------------------------------

def test_tradable_assets_logs_only_tradable_ones(client, monkeypatch):
    logged = []
    monkeypatch.setattr(alpaca_module.logger, "info", logged.append)
    assets = [SimpleNamespace(symbol="AAPL", tradable=True), SimpleNamespace(symbol="XYZ", tradable=False)]

    client.tradable_assets(assets)

    assert len(logged) == 1
    assert "AAPL" in logged[0]


@pytest.mark.xfail(reason="list_assets returns dicts, but tradable_assets uses attribute access "
                          "and returns nothing")
def test_tradable_assets_filters_api_response(client):
    assets = [{"symbol": "AAPL", "tradable": True}, {"symbol": "XYZ", "tradable": False}]

    assert client.tradable_assets(assets) == [{"symbol": "AAPL", "tradable": True}]
