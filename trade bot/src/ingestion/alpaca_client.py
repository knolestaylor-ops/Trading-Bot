# REST/Websocket client for Alpaca
import pandas as pd
import requests
import os
from errors.retryable import *
from errors.unretryable import *
from utils.config_loader import logger
from utils.decorators import retry, safe_api_call
from execution.payload_builder import PayloadBuilder


api_key = str(os.getenv("API_KEY"))
api_secret = str(os.getenv("API_SECRET"))

class AlpacaClient:

        # ---------------------------------------------------------------------
        # Section: Initialization
        # ---------------------------------------------------------------------


        def __init__(self):
            ALLOWED_HISTORICAL_URLS = ["bars", "auctions", "quotes", "trades",]

            self.key = api_key
            self.secret = api_secret
            self.session = requests.Session() # main request session
            self.session.headers.update({"APCA-API-KEY-ID": self.key, "APCA-API-SECRET-KEY": self.secret})
            self.base_url = "https://paper-api.alpaca.markets" # base url for all market requests
            self.historical_url = "https://data.alpaca.markets"# base url for all historical requests

            self.logger = logger
            self.payloads = PayloadBuilder()
        # ---------------------------------------------------------------------
        # Section: Requests
        # ---------------------------------------------------------------------

        @retry
        @safe_api_call
        def _request(self, method: str, endpoint: str, **kwargs):

            self.logger.debug(f"Requesting {method} {endpoint}  kwargs = {kwargs}")

            last = endpoint.split("/")[-1]

            if last in ALLOWED_HISTORICAL_URLS:
                base = self.historical_url
            else:
                base = self.base_url

            url = base + endpoint

            try:
                response = self.session.request(method, url, **kwargs)
                self.logger.debug(f"RESPONSE: {response.status_code}, {response.text}")
                
            except (requests.ConnectionError, requests.Timeout) as e:
                raise RetryableError(f"Network issue: {e}")

            if  500 <= response.status_code < 600:
                raise RetryableError(f"Server error: {response.status_code}: {response.text} ")

            if response.status_code in (408, 429):
                raise RetryableError(f"API error: {response.status_code}: {response.text} ")

            elif 400 <= response.status_code < 500:
                raise UnretryableError(f"Client error: {response.status_code}: {response.text} ")

            if not response.text:
                return None

            try:
                data = response.json()

            except ValueError:
                raise UnretryableError("Failed to parse JSON response from Alpaca")

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

        def get_equity(self, account):
            return float(account["equity"])

        def get_balance_change(self, account):
            return float(account["equity"]) - float(account["last_equity"])

        def get_cash(self, account):
            return float(account["cash"])

        # === Portfolio ===

        def get_portfolio_history(self):
            return self._request("GET", "/v2/portfolio_history")

        def get_portfolio_history_table(self):
            portfolio_history = self.get_portfolio_history()
            df = pd.DataFrame({
                "timestamp": portfolio_history["timestamp"],
                "equity": portfolio_history["equity"],
                "profit_loss": portfolio_history["profit_loss"],
                "profit_loss_pct": portfolio_history["profit_loss_pct"]
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

        def get_US_market_calendar(self):
            return self._request("GET", "/v2/calendar")

        # === Calendar ===

        def get_clock(self):
            return self._request("GET", "/v2/clock")

        def get_open_positions(self):
            return self._request("GET", "/v2/positions")

        # === Positions ===

        def close_all_positions(self):
            return self._request("DELETE", "/v2/positions")

        def get_position(self, symbol):
            return self._request("GET", f"/v2/positions/{symbol}")

        def close_position(self, symbol):
            return self._request("DELETE", f"/v2/positions/{symbol}")

        def exercise_options_position(self, symbol):
            return self._request("POST", f"/v2/positions/{symbol}/exercise")

        # === Watchlist ===

        def get_all_watchlist(self):
            return self._request("GET", "/v2/watchlists")

        def create_watchlist(self):
            return self._request("POST", "/v2/watchlists")

        def get_watchlist_by_id(self, watchlist_id):
            return self._request("GET", f"/v2/watchlists/{watchlist_id}")

        def update_watchlist_by_id(self, watchlist_id):
            return self._request("PUT", f"/v2/watchlists/{watchlist_id}")

        def add_asset_to_watchlist(self, watchlist_id):
            return self._request("POST", f"/v2/watchlists/{watchlist_id}")

        def delete_watchlist_by_id(self, watchlist_id):
            return self._request("DELETE", f"/v2/watchlists/{watchlist_id}")

        def get_watchlist_by_name(self, name):
            return self._request("GET", f"/v2/watchlists:by_name")

        def update_watchlist_by_name(self, name):
            return self._request("PUT", f"/v2/watchlists:by_name")

        def add_asset_to_watchlist_by_name(self, name):
            return self._request("POST", f"/v2/watchlists:by_name")

        def delete_watchlist_by_name(self, name):
            return self._request("DELETE", f"/v2/watchlists:by_name")

        def delete_symbol_from_watchlist(self, watchlist_id, symbol):
            return self._request("DELETE", f"/v2/watchlists/{watchlist_id}/{symbol}")

        # === Orders ===

        def submit_order(self, payload):
            return self._request("POST", "/v2/orders", json = payload)

        def liquidate_order(self, symbol):
            return self._request("DELETE", f"/v2/positions/{symbol}")

        def see_orders(self):
            return self._request("GET", "/v2/orders")

        def get_order(self, order_id):
            return self._request("GET", f"/v2/orders/{order_id}")

        def cancel_order(self, order_id):
            return self._request("DELETE", f"/v2/orders/{order_id}")

        def cancel_all_orders(self):
            return self._request("DELETE", "/v2/orders")

        def replace_order(self, order_id, payload):
            return self._request("PATCH", f"/v2/orders/{order_id}", json = payload)

        def get_last_trade(self, symbol):
            return self._request("GET", f"/v2/stocks/{symbol}/trades/latest")

        def get_last_quote(self, symbol):
            return self._request("GET", f"/v2/stocks/{symbol}/quotes/latest")

        def get_bars(self, symbol, timeframe = "1min", limit = 100):
            return self._request("GET", f"/v2/stocks/{symbol}/bars?timeframe={timeframe}&limit={limit}")

        def get_snapshot(self, symbol):
            return self._request("GET", f"/v2/stocks/{symbol}/snapshot")


alpaca_client = AlpacaClient()
account = alpaca_client.get_account()



