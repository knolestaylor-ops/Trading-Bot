
class MarketDataClient():
    def __init__(self):
        pass

    def latest_bars(self):
        return self._request("GET", "/v2/stocks/bars/latest")

    def latest_quotes(self):
        return self._request("GET", "/v2/stocks/quotes/latest")

    def snapshots(self):
        return self._request("GET", "/v2/stocks/snapshots")

    def latest_trades(self):
        return self._request("GET", "/v2/stocks/trades/latest")

    def latest_bar(self, symbol):
        return self._request("GET", f"/v2/stocks/{symbol}/bars/latest")

    def latest_quote(self, symbol):
        return self._request("GET", f"/v2/stocks/{symbol}/quotes/latest")

    def snapshot(self, symbol):
        return self._request("GET", f"/v2/stocks/{symbol}/snapshot")

    def latest_trade(self, symbol):
        return self._request("GET", f"/v2/stocks/{symbol}/trades/latest")