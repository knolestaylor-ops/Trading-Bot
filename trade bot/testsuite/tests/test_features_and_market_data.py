"""Indicator and market-data modules that can't be used yet; each test records why."""
import polars as pl
import pytest

from features.engine import IndicatorEngine
from ingestion.marketdata_client import MarketDataClient

SHADOWED = "features/indicators.py shadows the features/indicators/ package, so nothing in it can be imported"


def test_indicator_engine_can_be_created():
    assert IndicatorEngine() is not None


@pytest.mark.xfail(reason=SHADOWED + "; and SMAIndicator.__init__ calls super().__init__() without df")
def test_sma_indicator_computes_rolling_mean():
    from features.indicators.sma import SMAIndicator

    df = pl.DataFrame({"close": [1.0, 2.0, 3.0, 4.0]})
    out = df.with_columns(SMAIndicator(3).calculate())

    assert out["SMA_3"].to_list() == [None, None, 2.0, 3.0]


@pytest.mark.xfail(reason=SHADOWED + "; and Indicators.SMA reads 'SMA:<n>' while SMAIndicator writes 'SMA_<n>'")
def test_base_indicator_reads_the_column_sma_indicator_writes():
    from features.indicators.base import Indicators
    from features.indicators.sma import SMAIndicator

    df = pl.DataFrame({"close": [1.0, 2.0, 3.0]}).with_columns(SMAIndicator(2).calculate())

    assert Indicators(df).SMA(2).to_list() == [None, 1.5, 2.5]


def test_market_data_client_can_be_created():
    assert MarketDataClient() is not None


@pytest.mark.xfail(reason="MarketDataClient has no _request and no way to receive a client")
def test_market_data_client_uses_the_given_client():
    class FakeClient:
        def __init__(self):
            self.calls = []

        def _request(self, method, endpoint, **kwargs):
            self.calls.append((method, endpoint))
            return {"bar": {}}

    fake = FakeClient()

    assert MarketDataClient(fake).latest_bar("AAPL") == {"bar": {}}
    assert fake.calls == [("GET", "/v2/stocks/AAPL/bars/latest")]
