"""MarketDataFrame: bar validation and the Polars OHLCV store.

marketdataframe.py crashes on import (its demo code appends an invalid sample bar),
so the class is loaded without that code; see support.load_definitions.
"""
from datetime import datetime, timezone

import polars as pl
import pytest

from support import load_definitions

MarketDataFrame = load_definitions("dataframe.marketdataframe").MarketDataFrame

APPEND_BUG = ("validate_bar casts volume to int, but the schema is Float64, so every "
              "append fails with a Polars SchemaError")

FIELDS = ["timestamp", "open", "high", "low", "close", "volume"]


def make_bar(ts="2024-01-02T14:30:00Z", o=100.0, h=101.0, l=99.5, c=100.5, v=1200):
    return {"timestamp": ts, "open": o, "high": h, "low": l, "close": c, "volume": v}


@pytest.fixture
def mdf():
    return MarketDataFrame()


# ---------------------------------------------------------------------
# Empty frame
# ---------------------------------------------------------------------

def test_starts_empty_with_declared_schema(mdf):
    assert mdf.bar_count() == 0
    assert mdf.df_shape() == (0, 6)
    assert mdf.df_height() == 0
    assert mdf.df_width() == 6
    assert dict(mdf.df.schema) == mdf.get_schema()
    assert mdf.get_schema()["timestamp"] == pl.Datetime("us", "UTC")
    assert list(mdf.get_schema()) == FIELDS


def test_has_bars(mdf):
    assert mdf.has_bars(0)
    assert not mdf.has_bars(1)


def test_empty_frame_has_no_current_timestamp(mdf):
    assert mdf.current_timestamp() is None
    assert mdf.get_latest_bar().height == 0
    assert mdf.get_latest_bars(5).height == 0


def test_append_no_bars_is_a_no_op(mdf):
    assert mdf.append_bars([]).height == 0
    assert mdf.bar_count() == 0


# ---------------------------------------------------------------------
# validate_bar
# ---------------------------------------------------------------------

def test_valid_bar_is_normalised(mdf):
    assert mdf.validate_bar(make_bar()) == {
        "timestamp": "2024-01-02T14:30:00Z", "open": 100.0, "high": 101.0,
        "low": 99.5, "close": 100.5, "volume": 1200,
    }


def test_numeric_strings_are_converted(mdf):
    bar = mdf.validate_bar(make_bar(o="100", h="101", l="99.5", c="100.5", v="1200"))

    assert (bar["open"], bar["high"], bar["low"], bar["close"]) == (100.0, 101.0, 99.5, 100.5)
    assert isinstance(bar["open"], float)


def test_extra_fields_are_dropped(mdf):
    assert set(mdf.validate_bar({**make_bar(), "vwap": 100.2})) == set(FIELDS)


def test_flat_bar_is_valid(mdf):
    mdf.validate_bar(make_bar(o=100, h=100, l=100, c=100))


def test_zero_volume_is_valid(mdf):
    assert mdf.validate_bar(make_bar(v=0))["volume"] == 0


@pytest.mark.parametrize("field", FIELDS)
def test_rejects_missing_field(mdf, field):
    bar = make_bar()
    del bar[field]

    with pytest.raises(ValueError, match=field):
        mdf.validate_bar(bar)


@pytest.mark.parametrize("field", ["o", "h", "l", "c"])
@pytest.mark.parametrize("price", [0, -1.5])
def test_rejects_non_positive_prices(mdf, field, price):
    with pytest.raises(ValueError, match="positive"):
        mdf.validate_bar(make_bar(**{field: price}))


@pytest.mark.parametrize("o, c", [(102, 100), (100, 102)])
def test_rejects_high_below_open_or_close(mdf, o, c):
    with pytest.raises(ValueError, match="High"):
        mdf.validate_bar(make_bar(o=o, h=101, l=99, c=c))


@pytest.mark.parametrize("o, c", [(98, 100), (100, 98)])
def test_rejects_low_above_open_or_close(mdf, o, c):
    with pytest.raises(ValueError, match="Low"):
        mdf.validate_bar(make_bar(o=o, h=101, l=99, c=c))


def test_rejects_negative_volume(mdf):
    with pytest.raises(ValueError, match="Volume"):
        mdf.validate_bar(make_bar(v=-1))


def test_rejects_non_numeric_price(mdf):
    with pytest.raises(ValueError):
        mdf.validate_bar(make_bar(o="abc"))


@pytest.mark.xfail(reason="volume is truncated with int(); fractional (e.g. crypto) volume is lost")
def test_fractional_volume_is_preserved(mdf):
    assert mdf.validate_bar(make_bar(v=12.75))["volume"] == 12.75


@pytest.mark.xfail(reason="Alpaca bars use the keys t/o/h/l/c/v, which are not mapped")
def test_accepts_alpaca_bar_format(mdf):
    alpaca_bar = {"t": "2024-01-02T14:30:00Z", "o": 100.0, "h": 101.0, "l": 99.5, "c": 100.5, "v": 1200}

    assert mdf.validate_bar(alpaca_bar)["close"] == 100.5


# ---------------------------------------------------------------------
# Conversion to DataFrames
# ---------------------------------------------------------------------

def test_bar_to_df_parses_timestamp_as_utc(mdf):
    df = mdf.bar_to_df(make_bar())

    assert df.height == 1
    assert df.schema["timestamp"] == pl.Datetime("us", "UTC")
    assert df["timestamp"][0] == datetime(2024, 1, 2, 14, 30, tzinfo=timezone.utc)


def test_bars_to_df_keeps_input_order(mdf):
    df = mdf.bars_to_df([make_bar(ts="2024-01-03T14:30:00Z"), make_bar(ts="2024-01-02T14:30:00Z")])

    assert df["timestamp"].dt.day().to_list() == [3, 2]


def test_bars_to_df_validates_every_bar(mdf):
    with pytest.raises(ValueError):
        mdf.bars_to_df([make_bar(), make_bar(v=-1)])


@pytest.mark.xfail(reason="unparseable timestamps surface as a Polars ComputeError, not a ValueError")
def test_rejects_malformed_timestamp(mdf):
    with pytest.raises(ValueError):
        mdf.bar_to_df(make_bar(ts="not-a-date"))


@pytest.mark.xfail(reason=APPEND_BUG)
def test_bar_to_df_matches_declared_schema(mdf):
    assert dict(mdf.bar_to_df(make_bar()).schema) == mdf.get_schema()


# ---------------------------------------------------------------------
# Appending
# ---------------------------------------------------------------------

def test_invalid_bar_leaves_frame_unchanged(mdf):
    with pytest.raises(ValueError):
        mdf.append_bars([make_bar(), make_bar(h=1, l=9)])

    assert mdf.bar_count() == 0


@pytest.mark.xfail(reason=APPEND_BUG)
def test_append_bar_adds_a_row(mdf):
    mdf.append_bar(make_bar())

    assert mdf.bar_count() == 1
    assert mdf.has_bars(1)
    assert dict(mdf.df.schema) == mdf.get_schema()


@pytest.mark.xfail(reason=APPEND_BUG)
def test_append_bars_sorts_by_timestamp(mdf):
    mdf.append_bars([
        make_bar(ts="2024-01-03T14:30:00Z"),
        make_bar(ts="2024-01-01T14:30:00Z"),
        make_bar(ts="2024-01-02T14:30:00Z"),
    ])

    assert mdf.df["timestamp"].dt.day().to_list() == [1, 2, 3]


@pytest.mark.xfail(reason=APPEND_BUG)
def test_append_bars_keeps_last_duplicate(mdf):
    mdf.append_bars([make_bar(c=100.5), make_bar(c=100.9)])

    assert mdf.bar_count() == 1
    assert mdf.df["close"][0] == 100.9


# Not strict: once appends work, unique() without keep= may keep either row.
@pytest.mark.xfail(reason=APPEND_BUG + "; and unique() without keep= keeps an arbitrary duplicate",
                   strict=False)
def test_append_bar_replaces_duplicate_timestamp(mdf):
    mdf.append_bar(make_bar(c=100.5))
    mdf.append_bar(make_bar(c=100.9))

    assert mdf.bar_count() == 1
    assert mdf.df["close"][0] == 100.9


@pytest.mark.xfail(reason=APPEND_BUG)
def test_current_timestamp_and_latest_bars(mdf):
    mdf.append_bars([make_bar(ts=f"2024-01-0{day}T14:30:00Z", c=100 + day / 10) for day in (1, 2, 3)])

    assert mdf.current_timestamp() == datetime(2024, 1, 3, 14, 30, tzinfo=timezone.utc)
    assert mdf.get_latest_bar()["close"].to_list() == [100.3]
    assert mdf.get_latest_bars(2)["close"].to_list() == [100.2, 100.3]
