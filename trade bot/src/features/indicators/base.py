
class Indicators:
    def __init__(self, df):
        self.df = df

    def get_df(self):
        return self.df

    def SMA(self, period):
        return self.df.get_column(f"SMA:{period}")
