
class SMACrossover:
    def __init__(self, fast_period, slow_period):
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.name = "SMACrossover"

    def generate_signal(self, df):

        if len(df) < 2:
            return "HOLD"

        fast = df[f"SMA_{self.fast_period}"]
        slow = df[f"SMA_{self.slow_period}"]

        curr_fast = fast[-1]
        curr_slow = slow[-1]

        prev_fast = fast[-2]
        prev_slow = slow[-2]

        if prev_fast <= prev_slow and curr_fast > curr_slow:
            return "BUY"

        if prev_fast >= prev_slow and curr_fast < curr_slow:
            return "SELL"

        return "HOLD"

