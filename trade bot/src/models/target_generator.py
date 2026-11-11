import polars as pl

class TargetGenerator:

    def generate(self, df):
        return (
            (pl.col("close").shift(-1) >
            pl.col("close")
             )
        .cast(pl.Int8)
        .alias("target")
        )