"""PayloadBuilder: every order type, every validation rule."""
import pytest

from errors.retryable import DataError
from execution.payload_builder import PayloadBuilder

VALID = {
    "market_buy": dict(symbol="AAPL", time_in_force="day", qty=10),
    "limit_buy": dict(symbol="AAPL", time_in_force="day", limit_price=150.5, qty=10),
    "stop_buy": dict(symbol="AAPL", time_in_force="gtc", stop_price=155, qty=10),
    "stop_limit_buy": dict(symbol="AAPL", time_in_force="gtc", limit_price=150, stop_price=155, qty=10),
    "market_sell": dict(symbol="AAPL", time_in_force="day", qty=10),
    "limit_sell": dict(symbol="AAPL", time_in_force="day", limit_price=150.5, qty=10),
    "stop_sell": dict(symbol="AAPL", time_in_force="gtc", stop_price=155, qty=10),
    "stop_limit_sell": dict(symbol="AAPL", time_in_force="gtc", limit_price=150, stop_price=155, qty=10),
}


def expected(side, **fields):
    return {"symbol": "AAPL", "side": side, **fields}


EXPECTED = {
    "market_buy": expected("buy", type="market", time_in_force="day", qty="10"),
    "limit_buy": expected("buy", type="limit", time_in_force="day", qty="10", limit_price="150.5"),
    "stop_buy": expected("buy", type="stop", time_in_force="gtc", qty="10", stop_price="155"),
    "stop_limit_buy": expected("buy", type="stop_limit", time_in_force="gtc", qty="10",
                               stop_price="155", limit_price="150"),
    "market_sell": expected("sell", type="market", time_in_force="day", qty="10"),
    "limit_sell": expected("sell", type="limit", time_in_force="day", qty="10", limit_price="150.5"),
    "stop_sell": expected("sell", type="stop", time_in_force="gtc", qty="10", stop_price="155"),
    "stop_limit_sell": expected("sell", type="stop_limit", time_in_force="gtc", qty="10",
                                stop_price="155", limit_price="150"),
}

ALL = list(VALID)
QTY_OR_NOTIONAL = ["market_buy", "limit_buy", "market_sell", "limit_sell"]
LIMIT = ["limit_buy", "limit_sell"]
QTY_ONLY = ["stop_buy", "stop_limit_buy", "stop_sell", "stop_limit_sell"]
WITH_LIMIT_PRICE = ["limit_buy", "limit_sell", "stop_limit_buy", "stop_limit_sell"]
WITH_STOP_PRICE = ["stop_buy", "stop_sell", "stop_limit_buy", "stop_limit_sell"]
STOP_LIMIT = ["stop_limit_buy", "stop_limit_sell"]


@pytest.fixture
def builder():
    return PayloadBuilder()


def build(builder, name, **overrides):
    return getattr(builder, name)(**{**VALID[name], **overrides})


# ---------------------------------------------------------------------
# Valid payloads
# ---------------------------------------------------------------------

@pytest.mark.parametrize("name", ALL)
def test_builds_expected_payload(builder, name):
    assert build(builder, name) == EXPECTED[name]


@pytest.mark.parametrize("name", ALL)
def test_all_payload_values_are_strings(builder, name):
    """Alpaca expects numeric order fields as strings, which avoids float formatting issues."""
    assert all(isinstance(value, str) for value in build(builder, name).values())


@pytest.mark.parametrize("tif", sorted(PayloadBuilder.ALLOWED_TIFS))
def test_accepts_every_alpaca_time_in_force(builder, tif):
    assert build(builder, "market_buy", time_in_force=tif)["time_in_force"] == tif


def test_accepts_fractional_quantities(builder):
    assert build(builder, "market_buy", qty=0.5)["qty"] == "0.5"


@pytest.mark.parametrize("name", QTY_OR_NOTIONAL)
def test_notional_order(builder, name):
    payload = build(builder, name, qty=None, notional=500)

    assert payload["notional"] == "500"
    assert "qty" not in payload


# ---------------------------------------------------------------------
# Fields every order type validates
# ---------------------------------------------------------------------

@pytest.mark.parametrize("name", ALL)
def test_rejects_missing_symbol(builder, name):
    with pytest.raises(DataError, match="symbol"):
        build(builder, name, symbol=None)


@pytest.mark.xfail(reason="an empty symbol passes validation; only None is checked")
@pytest.mark.parametrize("name", ALL)
def test_rejects_empty_symbol(builder, name):
    with pytest.raises(DataError):
        build(builder, name, symbol="")


@pytest.mark.parametrize("name", ALL)
@pytest.mark.parametrize("tif", ["bogus", "", None])
def test_rejects_invalid_time_in_force(builder, name, tif):
    with pytest.raises(DataError, match="time_in_force"):
        build(builder, name, time_in_force=tif)


@pytest.mark.parametrize("name", ALL)
@pytest.mark.parametrize("qty", [0, -1, -0.5])
def test_rejects_non_positive_qty(builder, name, qty):
    with pytest.raises(DataError):
        build(builder, name, qty=qty)


@pytest.mark.parametrize("name", [
    pytest.param(name, marks=pytest.mark.xfail(
        reason="float('abc') raises a raw ValueError; only the stop-limit builders convert it to DataError"))
    if name not in STOP_LIMIT else name
    for name in ALL
])
def test_rejects_non_numeric_qty(builder, name):
    with pytest.raises(DataError):
        build(builder, name, qty="abc")


# ---------------------------------------------------------------------
# qty vs notional
# ---------------------------------------------------------------------

@pytest.mark.parametrize("name", QTY_OR_NOTIONAL)
def test_rejects_qty_and_notional_together(builder, name):
    with pytest.raises(DataError, match="not both"):
        build(builder, name, qty=1, notional=100)


@pytest.mark.parametrize("name", QTY_OR_NOTIONAL)
def test_rejects_neither_qty_nor_notional(builder, name):
    with pytest.raises(DataError, match="qty or notional"):
        build(builder, name, qty=None)


@pytest.mark.parametrize("name", QTY_OR_NOTIONAL)
@pytest.mark.parametrize("notional", [0, -100])
def test_rejects_non_positive_notional(builder, name, notional):
    with pytest.raises(DataError, match="notional"):
        build(builder, name, qty=None, notional=notional)


@pytest.mark.parametrize("name", LIMIT)
def test_limit_notional_requires_day_time_in_force(builder, name):
    with pytest.raises(DataError, match="day"):
        build(builder, name, qty=None, notional=500, time_in_force="gtc")


@pytest.mark.parametrize("name", QTY_ONLY)
def test_stop_orders_require_qty(builder, name):
    with pytest.raises(DataError, match="qty"):
        build(builder, name, qty=None)


# ---------------------------------------------------------------------
# Prices
# ---------------------------------------------------------------------

@pytest.mark.parametrize("name", WITH_LIMIT_PRICE)
@pytest.mark.parametrize("limit_price", [None, 0, -5])
def test_rejects_missing_or_non_positive_limit_price(builder, name, limit_price):
    with pytest.raises(DataError):
        build(builder, name, limit_price=limit_price)


@pytest.mark.parametrize("name", WITH_STOP_PRICE)
@pytest.mark.parametrize("stop_price", [None, 0, -5])
def test_rejects_missing_or_non_positive_stop_price(builder, name, stop_price):
    with pytest.raises(DataError):
        build(builder, name, stop_price=stop_price)


@pytest.mark.parametrize("name", STOP_LIMIT)
@pytest.mark.parametrize("field", ["stop_price", "limit_price"])
def test_stop_limit_rejects_non_numeric_prices(builder, name, field):
    with pytest.raises(DataError, match="numerical"):
        build(builder, name, **{field: "abc"})


@pytest.mark.parametrize("stop_price, limit_price", [(150, 150), (140, 150)])
def test_sell_stop_limit_requires_stop_above_limit(builder, stop_price, limit_price):
    with pytest.raises(DataError, match="Stop price"):
        build(builder, "stop_limit_sell", stop_price=stop_price, limit_price=limit_price)


@pytest.mark.xfail(reason="the sell-side rule (stop > limit) is applied to buys too; a buy "
                          "stop-limit normally has limit >= stop")
def test_buy_stop_limit_accepts_limit_at_or_above_stop(builder):
    payload = build(builder, "stop_limit_buy", stop_price=155, limit_price=156)

    assert payload["limit_price"] == "156"


@pytest.mark.parametrize("name", [
    "stop_limit_buy",
    pytest.param("stop_limit_sell", marks=pytest.mark.xfail(
        reason="a bare `except:` swallows the specific DataError and replaces its message")),
])
def test_stop_limit_reports_the_real_validation_error(builder, name):
    with pytest.raises(DataError, match="positive qty"):
        build(builder, name, qty=-1)
