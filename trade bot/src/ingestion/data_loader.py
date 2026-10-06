
from utils.config_loader import logger

class HistoricalDataClient:

    def __init__(self, client):
        self._request = client._request # needs to work on the same session as alpaca_client
        self.logger = logger

    def _paginate(self, method, endpoint, params):
        all_items = []
        next_token = None

        while True:
            if next_token:
                params["page_token"] = next_token

            response = self._request(method, endpoint, params=params)

            data_key = next(k for k in response.keys() if k not in ("next_page_token"))
            items = response.get(data_key, [])

            all_items.extend(items)
            next_token = response.get("next_page_token")

            if not next_token:
                break

        return all_items

    def get_historical_bars(self, symbols, start=None, end=None, timeframe="1Min", limit=None):
        params = {
            "symbols": symbols,
            "start": start,
            "end": end,
            "timeframe": timeframe,
            "limit": limit
        }
        return self._paginate("GET", "/v2/stocks/bars", params = params)

    def get_historical_auctions(self, symbols, start=None, end=None, timeframe="1Min", limit=None):
        params = {
            "symbols": symbols,
            "start": start,
            "end": end,
            "timeframe": timeframe,
            "limit": limit
        }
        return self._paginate("GET", "/v2/stocks/auctions", params = params)

    def get_historical_quotes(self, symbols, start=None, end=None, timeframe="1Min", limit=None):
        params = {
            "symbols": symbols,
            "start": start,
            "end": end,
            "timeframe": timeframe,
            "limit": limit
        }
        return self._paginate("GET", "/v2/stocks/quotes", params = params)

    def get_historical_trades(self, symbols, start=None, end=None, timeframe="1Min", limit=None):
        params = {
            "symbols": symbols,
            "start": start,
            "end": end,
            "timeframe": timeframe,
            "limit": limit
        }
        return self._paginate("GET", "/v2/stocks/trades", params = params)

    def get_historical_auction(self, symbol):
        return self._request("GET", f"/v2/stocks/{symbol}/auctions")

    def get_historical_bar(self, symbol):
        return self._request("GET", f"/v2/stocks/{symbol}/bars")

    def get_historical_quote(self, symbol):
        return self._request("GET", f"/v2/stocks/{symbol}/quotes")

    def get_historical_trade(self, symbol):
        return self._request("GET", f"/v2/stocks/{symbol}/trades")

