from features.indicators.base import Indicators
import polars as pl

class SMAIndicator(Indicators):
    def __init__(self, period):
        super().__init__()

        self.name = "SMA"
        self.period = period

    def calculate(self):
        return pl.col("close").rolling_mean(window_size= self.period).alias(f"{self.name}_{self.period}")