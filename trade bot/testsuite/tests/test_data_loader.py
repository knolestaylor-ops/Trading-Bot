"""HistoricalDataClient: pagination and endpoint wiring.

data_loader.py can't be imported normally (broken import, live API call at module
level), so its definitions are loaded without that code; see support.load_definitions.
"""
import copy

import pytest

from errors.base import TradeBotError
from support import load_definitions

data_loader = load_definitions("ingestion.data_loader", skip_imports={"alpaca_client"})
HistoricalDataClient = data_loader.HistoricalDataClient


class FakeClient:
    """Records `_request` calls (deep-copied, since _paginate mutates params) and replays responses."""

    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []

    def _request(self, method, endpoint, **kwargs):
        self.calls.append({"method": method, "endpoint": endpoint, "kwargs": copy.deepcopy(kwargs)})
        return self.responses.pop(0) if self.responses else None


def page(items, token=None, key="bars"):
    return {key: items, "next_page_token": token}


def test_shares_the_clients_request_method():
    fake = FakeClient()

    assert HistoricalDataClient(fake)._request == fake._request


# ---------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------

def test_single_page():
    fake = FakeClient(page([1, 2]))

    assert HistoricalDataClient(fake)._paginate("GET", "/v2/stocks/bars", {"symbols": "AAPL"}) == [1, 2]
    assert len(fake.calls) == 1
    assert "page_token" not in fake.calls[0]["kwargs"]["params"]


def test_follows_next_page_tokens_until_exhausted():
    fake = FakeClient(page([1, 2], "p2"), page([3], "p3"), page([4]))

    result = HistoricalDataClient(fake)._paginate("GET", "/v2/stocks/bars", {"symbols": "AAPL"})

    assert result == [1, 2, 3, 4]
    assert [c["kwargs"]["params"].get("page_token") for c in fake.calls] == [None, "p2", "p3"]
    assert all(c["kwargs"]["params"]["symbols"] == "AAPL" for c in fake.calls)


def test_stops_when_next_page_token_is_missing():
    fake = FakeClient({"trades": [1]}, page([2]))

    assert HistoricalDataClient(fake)._paginate("GET", "/v2/stocks/trades", {}) == [1]
    assert len(fake.calls) == 1


def test_finds_the_data_key_regardless_of_order():
    fake = FakeClient({"next_page_token": None, "quotes": ["q1"]})

    assert HistoricalDataClient(fake)._paginate("GET", "/v2/stocks/quotes", {}) == ["q1"]


@pytest.mark.xfail(reason="multi-symbol responses map symbol -> list; list.extend(dict) keeps "
                          "only the symbol names and drops every bar")
def test_multi_symbol_response_keeps_all_bars():
    aapl, msft = {"c": 190.0}, {"c": 410.0}
    fake = FakeClient(page({"AAPL": [aapl], "MSFT": [msft]}))

    result = HistoricalDataClient(fake).get_historical_bars("AAPL,MSFT")

    assert result == {"AAPL": [aapl], "MSFT": [msft]}


@pytest.mark.xfail(reason="_paginate writes page_token into the caller's params dict")
def test_does_not_mutate_callers_params():
    params = {"symbols": "AAPL"}
    fake = FakeClient(page([1], "p2"), page([2]))

    HistoricalDataClient(fake)._paginate("GET", "/v2/stocks/bars", params)

    assert params == {"symbols": "AAPL"}


@pytest.mark.xfail(reason="an empty or missing response raises AttributeError/StopIteration "
                          "instead of a project error")
@pytest.mark.parametrize("response", [None, {}, {"next_page_token": None}])
def test_empty_response_raises_a_project_error(response):
    fake = FakeClient(response)

    with pytest.raises(TradeBotError):
        HistoricalDataClient(fake)._paginate("GET", "/v2/stocks/bars", {})


# ---------------------------------------------------------------------
# Multi-symbol endpoints
# ---------------------------------------------------------------------

@pytest.mark.parametrize("method, endpoint, key", [
    ("get_historical_bars", "/v2/stocks/bars", "bars"),
    ("get_historical_auctions", "/v2/stocks/auctions", "auctions"),
    ("get_historical_quotes", "/v2/stocks/quotes", "quotes"),
    ("get_historical_trades", "/v2/stocks/trades", "trades"),
])
def test_multi_symbol_endpoints(method, endpoint, key):
    fake = FakeClient(page(["item"], key=key))

    result = getattr(HistoricalDataClient(fake), method)(
        "AAPL", start="2024-01-01", end="2024-01-31", timeframe="1Day", limit=500,
    )

    assert result == ["item"]
    assert fake.calls[0]["method"] == "GET"
    assert fake.calls[0]["endpoint"] == endpoint
    assert fake.calls[0]["kwargs"]["params"] == {
        "symbols": "AAPL", "start": "2024-01-01", "end": "2024-01-31", "timeframe": "1Day", "limit": 500,
    }


def test_multi_symbol_defaults():
    fake = FakeClient(page([]))

    HistoricalDataClient(fake).get_historical_bars("AAPL")

    assert fake.calls[0]["kwargs"]["params"] == {
        "symbols": "AAPL", "start": None, "end": None, "timeframe": "1Min", "limit": None,
    }


@pytest.mark.xfail(reason="a list of symbols is sent as-is; Alpaca expects one comma-separated string")
def test_symbol_list_is_sent_comma_separated():
    fake = FakeClient(page([]))

    HistoricalDataClient(fake).get_historical_bars(["AAPL", "MSFT"])

    assert fake.calls[0]["kwargs"]["params"]["symbols"] == "AAPL,MSFT"


# ---------------------------------------------------------------------
# Single-symbol endpoints
# ---------------------------------------------------------------------

@pytest.mark.parametrize("method, endpoint", [
    ("get_historical_auction", "/v2/stocks/AAPL/auctions"),
    ("get_historical_bar", "/v2/stocks/AAPL/bars"),
    ("get_historical_quote", "/v2/stocks/AAPL/quotes"),
    ("get_historical_trade", "/v2/stocks/AAPL/trades"),
])
def test_single_symbol_endpoints(method, endpoint):
    fake = FakeClient({"symbol": "AAPL"})

    assert getattr(HistoricalDataClient(fake), method)("AAPL") == {"symbol": "AAPL"}
    assert fake.calls == [{"method": "GET", "endpoint": endpoint, "kwargs": {}}]
