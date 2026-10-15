import pandas as pd


class DummyResponse:
    def __init__(self, status_code=200, text="", json_data=None):
        self.status_code = status_code
        self.text = text
        self._json_data = json_data

    def json(self):
        return self._json_data


def _set_response(client, json_data):
    client.session.response = DummyResponse(
        status_code=200,
        text="ok",
        json_data=json_data,
    )


# ---------------------------------------------------------------------
# Portfolio history table
# ---------------------------------------------------------------------

def test_get_portfolio_history_table_builds_dataframe(client):
    _set_response(
        client,
        {
            "timestamp": [1700000000, 1700000600],
            "equity": [10000.0, 10100.0],
            "profit_loss": [0.0, 100.0],
            "profit_loss_pct": [0.0, 0.01],
        },
    )

    df = client.get_portfolio_history_table()

    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == [
        "timestamp",
        "equity",
        "profit_loss",
        "profit_loss_pct",
    ]
    # timestamp converted to datetime
    assert pd.api.types.is_datetime64_any_dtype(df["timestamp"])
    assert df["equity"].tolist() == [10000.0, 10100.0]


# ---------------------------------------------------------------------
# Account helper methods
# ---------------------------------------------------------------------

def test_account_helpers(client):
    account = {
        "buying_power": "5000",
        "equity": "10000",
        "last_equity": "9500",
        "cash": "2000",
    }

    assert client.get_buying_power(account) == 5000.0
    assert client.get_equity(account) == 10000.0
    assert client.get_balance_change(account) == 500.0
    assert client.get_cash(account) == 2000.0
