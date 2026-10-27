import polars as pl

bar = {
    "timestamp": "2024-01-01T09:30:00Z",
    "open": 1.0,
    "high": 1.0,
    "low": 9.0,
    "close": 1.0,
    "volume": 12.0,
}

bar1 = {
    "timestamp": "2024-02-01T09:30:00Z",
    "open": 100.0,
    "high": 101.0,
    "low": 99.5,
    "close": 100.7,
    "volume": 12000.0,
}

class MarketDataFrame:
    def __init__(self):
        self.schema =  {
            "timestamp": pl.Datetime("us","UTC"),
            "open": pl.Float64,
            "high": pl.Float64,
            "low": pl.Float64,
            "close": pl.Float64,
            "volume": pl.Float64,
        }
        self.df = pl.DataFrame(schema = self.schema)

    def bar_count(self):
        return len(self.df)

    def df_shape(self):
        return self.df.shape

    def df_height(self):
        return self.df.height

    def df_width(self):
        return self.df.width

    def bar_to_df(self, bar: dict) -> pl.DataFrame:
        return pl.DataFrame([bar]).with_columns([pl.col("timestamp").str.to_datetime(time_unit= "us", time_zone= "UTC")])

    def bars_to_df(self, bars: list) -> pl.DataFrame:
        return pl.DataFrame(bars).with_columns([pl.col("timestamp").str.to_datetime(time_unit= "us", time_zone= "UTC")])

    def append_bar(self, bar: dict) -> pl.DataFrame:
        new_df = self.bar_to_df(bar)
        self.df = pl.concat([self.df, new_df], how = "vertical").unique(subset=['timestamp']).sort('timestamp')
        return self.df

    def append_bars(self, bars: list) -> pl.DataFrame:
        if not bars:
            return self.df

        new_df = self.bars_to_df(bars)

        self.df = pl.concat([self.df, new_df], how = "vertical").unique(subset=['timestamp'], keep= "last").sort('timestamp')
        return self.df

    def current_timestamp(self):
        if self.df.is_empty():
            return None

        return self.df.item(self.df.height - 1,0)

    def market_price(self):
        pass

    def highest_high(self):
        pass

    def lowest_low(self):
        pass

    def sma(self):
        pass

    def ema(self):
        pass

    def resample(self):
        pass

    def save_parquet(self):
        pass

    def load_parquet(self):
        pass




    def validate_bar(self,bar):
        self._validate_fields()
        self._validate_values()
        self._validate_types()
        self._validate_positive()
        self._validate_relationship()




dataframe = MarketDataFrame()
print(dataframe.append_bar(bar))
print(dataframe.append_bar(bar1))
print(dataframe.df)
print(dataframe.current_timestamp())
