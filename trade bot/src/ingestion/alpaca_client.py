# REST/Websocket client for Alpaca
import pandas as pd
import requests
import os
from errors.retryable import *
from errors.unretryable import *
from utils.config_loader import logger
from utils.decorators import retry, safe_api_call
from alpaca.trading.client import TradingClient



"""

2. REST Client Initialization
Handles:
Account info
Submit orders
Get positions
Cancel orders
Get assets

3. Market Data Client (optional but recommended)
For pulling:
Historical OHLCV
Latest quotes
Bars for training data

4. Helper Functions
submit_market_order()
get_latest_price()
stream_prices()
on_trade_update()
5. A single exported object


Market
get_clock
is_market_open
get_calendar
Assets
get_asset(symbol)
list_assets
tradable_assets
validate_symbol(symbol)

Orders
submit_order
cancel_order
cancel_all_orders
replace_order
get_orders
get_order_by_id
Helpers
safe_submit_order
safe_close_position
safe_get_position
log_errors
"""


api_key = str(os.getenv("API_KEY"))
api_secret = str(os.getenv("API_SECRET"))


class AlpacaClient:
    def __init__(self):

        # ---------------------------------------------------------------------
        # Section: Initialization
        # ---------------------------------------------------------------------

        self.key = api_key
        self.secret = api_secret
        self.trading_client = TradingClient(api_key=api_key, secret_key=api_secret, paper=True)
        self.session = requests.Session()
        self.session.headers.update({"APCA-API-KEY-ID": self.key, "APCA-API-SECRET-KEY": self.secret})

        self.base_url = "https://paper-api.alpaca.com"
        self.logger = logger

    # ---------------------------------------------------------------------
    # Section: Requests
    # ---------------------------------------------------------------------

    @retry
    @safe_api_call
    def _request(self, method: str, endpoint: str, **kwargs):

        self.logger.debug(f"Requesting {method} {endpoint}  kwargs = {kwargs}")
        url = f"{self.base_url}{endpoint}"

        try:
            response = self.session.request(method, url, **kwargs)
            self.logger.debug(f"RESPONSE: {response.status_code}, {response.text}")
        except (requests.ConnectionError, requests.Timeout) as e:
            raise RetryableError(f"Network issue: {e}")

        if  500 <= response.status_code < 600:
            raise RetryableError(f"Server error: {response.status_code}: {response.text} ")

        if 400 <= response.status_code < 500:
            raise UnretryableError(f"Client error: {response.status_code}: {response.text} ")

        if not response.text:
            return None

        try:
            data = response.json()

        except ValueError:
            raise ValueError("Failed to parse JSON response from Alpaca")

        return data

    # === Account ===

    def get_account(self):
        return self._request("GET", "/v2/account")

    def get_account_config(self):
        return self._request("GET", "/v2/account/configurations")

    def patch_account_config(self):
        return self._request("PATCH", "/v2/account/configurations")

    # === activities ===

    def get_account_activities(self):
        return self._request("GET", "/v2/account/activities")

    def filter_account_activities(self, activity_type):
        return self._request("GET", f"/v2/account/activities/{activity_type}")

    def get_buying_power(self, account):
        return float(account["buying_power"])

    def get_equity(self):
        return float(account["equity"])

    def get_balance_change(self, account):
        return float(account.equity) - float(account.last_equity)

    def get_cash(self, account):
        return self._request("GET", "/v2/cash", params={"account": account})

    # === Portfolio ===

    def get_portfolio_history(self):
        return self._request("GET", "/v2/portfolio_history")

    def get_portfolio_history_table(self):
        portfolio_history = self.get_portfolio_history()
        df = pd.DataFrame({
            "timestamp": portfolio_history.timestamp,
            "equity": portfolio_history.equity,
            "profit_loss": portfolio_history.profit_loss,
            "profit_loss_pct": portfolio_history.profit_loss_pct
        })

        # Convert timestamps to readable datetime
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")

        return df

    # === Assets ===

    def list_assets(self):
        return self._request("GET", "/v2/assets")

    def tradable_assets(self, assets):
        for asset in assets:
            if asset.tradable:
                logger.info(f"Tradable assets: {asset}")

    # === Orders ===

    def prep_payload_buy(self, symbol, side = "buy", qty=None, notional=None, time_in_force="day", type="market"):
        logger.info("Preparing payload")
        payload = {
                "symbol": symbol,
                "side": side,
                "time_in_force": time_in_force,
                "type": type
            }

        if qty is not None:
            payload["qty"] = str(qty)
        elif notional is not None:
            payload["notional"] = str(notional)
        else:
            raise DataError("Must provide either qty or notional")

        return payload

    def place_market_order(self, payload):
        return self._request("POST", "/v2/market_orders", json=payload)

    def prepare_sell_order(self, symbol, side = "sell", qty = None, notional = None, time_in_force = "day", type="market"):
        logger.info("Preparing payload")
        payload = {
            "symbol": symbol,
            "side": side,
            "time_in_force": time_in_force,
            "type": type
        }

        if qty is not None:
            payload["qty"] = str(qty)
        elif notional is not None:
            payload["   notional"] = str(notional)
        else:
            raise DataError("Must provide either qty or notional")

        return payload

    def sell_order(self, payload):
        return self._request("POST", "/v2/market_orders", json=payload)

    def liquidate_order(self, payload):
        return self._request("DELETE", f"/v2/positions", json=payload)

    def see_orders(self):
        return self._request("GET", "/v2/orders")

    # === Calendar ===

    def get_US_market_calendar(self):
        return self._request("GET", "/v2/calendar")

    def get_clock(self):
        return self._request("GET", "/v2/clock")

    # === Positions ===

    def get_open_positions(self):
        return self._request("GET", "/v2/positions")

    def close_all_positions(self):
        return self._request("DELETE", "/v2/positions")

    def get_position(self, symbol):
        return self._request("GET", f"/v2/position/{symbol}")

    def close_position(self, symbol):
        return self._request("DELETE", f"/v2/position/{symbol}")

    def exercise_options_position(self, symbol):
        return self._request("POST", f"/v2/positions/{symbol}/exercise")

    # === Watchlists ===

    def get_all_watchlists(self):
        return self._request("GET", "/v2/watchlists")

    def create_watchlist(self):
        return self._request("POST", "/v2/watchlists")

    def get_watchlist_by_id(self, id):
        return self._request("GET", f"/v2/watchlists/{id}")

    def update_watchlist_by_id(self, id):
        return self._request("PUT", f"/v2/watchlists/{id}")

    def add_asset_to_watchlist(self, id):
        return self._request("POST", f"/v2/watchlists/{id}")

    def delete_watchlist(self, id):
        return self._request("DELETE", f"/v2/watchlists/{id}")

    def get_watchlist_by_name(self, name):
        return self._request("GET", f"/v2/watchlists:{name}")

    def update_watchlist_by_name(self, name):
        return self._request("PUT", f"/v2/watchlists:{name}")

    def add_asset_to_watchlist_by_name(self, name):
        return self._request("POST", f"/v2/watchlists:{name}")

    def delete_watchlist_by_name(self, name):
        return self._request("DELETE", f"/v2/watchlists:{name}")

    def delete_symbol_from_watchlist(self, id, symbol):
        return self._request("DELETE", f"/v2/watchlists/{id}/{symbol}")

    



alpaca_client = AlpacaClient()
account = alpaca_client.get_account()


