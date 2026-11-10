
class IndicatorEngine:
    def __init__(self):
        self.indicators = []

    def add_indicator(self, indicator):
        self.indicators.append(indicator)

    def apply(self, df):

        columns =  []

        for indicator in self.indicators:
            # indicator needs to have a calculate method
            columns.append(indicator.calculate(df))

        return df.with_columns(columns)
