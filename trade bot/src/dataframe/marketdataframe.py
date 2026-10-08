import numpy as np

class MarketDataFrame:
    def __init__(self, close, high, low, number, open, time_stamp, volume):
        self.close = np.array(c.close for c in close)
        self.high = np.array(h.high for h in high)
        self.low = np.array(l.low for l in low)
        self.number = np.array(n.number for n in number)
        self.open = np.array(o.open for o in open)
        self.time_stamp = np.array(t.time_stamp for t in time_stamp)
        self.volume = np.array(v.volume for v in volume)