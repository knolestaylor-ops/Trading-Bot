# SMA, EMA, RSI, MAC, ATR, etc.
from features.indicators.sma import SMAIndicator


class IndicatorEngine:
    def __init__(self):
        pass

    def apply(self, df):
        return df.with_columns(
            SMAIndicator(20).calculate(),
            SMAIndicator(50).calculate(),
            SMAIndicator(100).calculate()
        )
