
from utils.config_loader import logger

class HistoricalDataClient:

    def __init__(self, client):
        self._request = client._request # needs to work on the same session as alpaca_client
        self.logger = logger

    def get_historical_bars(self):
        return self._request("GET", "/v2/stocks/bars")

    def get_historical_auctions(self):
        return self._request("GET", "/v2/stocks/auctions")

    def get_historical_quotes(self):
        return self._request("GET", "/v2/stocks/quotes")

    def get_historical_trades(self):
        return self._request("GET", "/v2/stocks/trades")

    def get_historical_auction(self, symbol):
        return self._request("GET", f"/v2/stocks/{symbol}/auctions")

    def get_historical_bar(self, symbol):
        return self._request("GET", f"/v2/stocks/{symbol}/bars")

    def get_historical_quote(self, symbol):
        return self._request("GET", f"/v2/stocks/{symbol}/quotes")

    def get_historical_trade(self, symbol):
        return self._request("GET", f"/v2/stocks/{symbol}/trades")