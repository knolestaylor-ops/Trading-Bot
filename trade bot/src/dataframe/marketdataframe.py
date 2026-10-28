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

    def has_bars(self, count: int) -> bool:
        return self.bar_count() >= count

    def df_shape(self):
        return self.df.shape

    def df_height(self):
        return self.df.height

    def df_width(self):
        return self.df.width

    def get_latest_bar(self):
        return self.df.tail(1)

    def get_latest_bars(self, count: int) -> pl.DataFrame:
        return self.df.tail(count)

    def bar_to_df(self, unvalidated_bar: dict) -> pl.DataFrame:
        bar = self.validate_bar(unvalidated_bar)
        return pl.DataFrame([bar]).with_columns([pl.col("timestamp").str.to_datetime(time_unit= "us", time_zone= "UTC")])

    def bars_to_df(self, unvalidated_bars: list) -> pl.DataFrame:
        bars = []

        for unvalidated_bar in unvalidated_bars:
            bar = self.validate_bar(unvalidated_bar)
            bars.append(bar)

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

    def _validate_fields(self, bar):
        required_fields = {
            "timestamp",
            "open",
            "high",
            "low",
            "close",
            "volume"
        }

        # Check required fields
        missing = required_fields - set(bar.keys())

        if missing:
            raise ValueError(
                f"Missing required fields: {missing}"
            )

    def _validate_prices(self, open_price, high_price, low_price, close_price):

        if open_price <= 0:
            raise ValueError("Open price must be positive")

        if high_price <= 0:
            raise ValueError("High price must be positive")

        if low_price <= 0:
            raise ValueError("Low price must be positive")

        if close_price <= 0:
            raise ValueError("Close price must be positive")


    def _validate_OHCL(self, high_price, low_price, open_price, close_price):

        if high_price < max(open_price, close_price):
            raise ValueError("High must be greater than or equal to open and close")

        if low_price > min(open_price, close_price):
            raise ValueError("Low must be less than or equal to open and close")

        if low_price > high_price:
            raise ValueError("Low cannot be greater than high")

    def _validate_volume(self, volume):
        if volume < 0:
            raise ValueError(
                "Volume cannot be negative"
            )
    def validate_bar(self,bar):
        self._validate_fields(bar)

        open_price = float(bar["open"])
        high_price = float(bar["high"])
        low_price = float(bar["low"])
        close_price = float(bar["close"])
        volume = int(bar["volume"])

        self._validate_prices(open_price, high_price, low_price, close_price)
        self._validate_OHCL(high_price, low_price, open_price, close_price)
        self._validate_volume(volume)

        return {
            "timestamp": bar["timestamp"],
            "open": open_price,
            "high": high_price,
            "low": low_price,
            "close": close_price,
            "volume": volume
        }



dataframe = MarketDataFrame()
print(dataframe.append_bar(bar))
print(dataframe.append_bar(bar1))
print(dataframe.df)
print(dataframe.current_timestamp())
