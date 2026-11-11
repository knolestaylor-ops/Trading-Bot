"""TargetGenerator: label = 1 when the next close is higher than the current close."""
import polars as pl

from features.target_generator import TargetGenerator


def generate(closes, **extra_columns):
    return TargetGenerator().generate(pl.DataFrame({"close": closes, **extra_columns}))


def test_target_is_one_when_next_close_is_higher():
    assert generate([1.0, 2.0, 3.0])["target"].to_list()[:2] == [1, 1]


def test_target_is_zero_when_next_close_is_lower_or_equal():
    assert generate([3.0, 2.0, 2.0])["target"].to_list()[:2] == [0, 0]


def test_last_row_has_no_target():
    """There is no next close for the last bar; it must be dropped before training."""
    assert generate([1.0, 2.0])["target"].to_list()[-1] is None


def test_mixed_sequence():
    assert generate([1.0, 2.0, 2.0, 1.0, 5.0])["target"].to_list() == [1, 0, 0, 1, None]


def test_target_dtype_is_int8():
    assert generate([1.0, 2.0])["target"].dtype == pl.Int8


def test_keeps_existing_columns_and_does_not_modify_input():
    df = pl.DataFrame({"close": [1.0, 2.0], "volume": [10.0, 20.0]})

    out = TargetGenerator().generate(df)

    assert out.columns == ["close", "volume", "target"]
    assert df.columns == ["close", "volume"]


def test_empty_frame():
    out = TargetGenerator().generate(pl.DataFrame({"close": []}, schema={"close": pl.Float64}))

    assert out.height == 0
    assert "target" in out.columns
