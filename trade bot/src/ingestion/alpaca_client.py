# REST/Websocket client for Alpaca
import pandas as pd
import requests
import os
from errors.retryable import *
from errors.unretryable import *
from utils.config_loader import logger
from utils.decorators import retry, safe_api_call


api_key = str(os.getenv("API_KEY"))
api_secret = str(os.getenv("API_SECRET"))

class AlpacaClient:

        # ---------------------------------------------------------------------
        # Section: Initialization
        # ---------------------------------------------------------------------
        ALLOWED_TIFS = {"day", "gtc", "opg", "cls", "ioc", "fok"}

        def __init__(self):
            self.key = api_key
            self.secret = api_secret
            self.session = requests.Session()
            self.session.headers.update({"APCA-API-KEY-ID": self.key, "APCA-API-SECRET-KEY": self.secret})

            self.base_url = "https://paper-api.alpaca.markets"
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

        def prep_market_buy_payload(self, symbol:str, qty=None, notional=None, time_in_force="day"):
            logger.info("Preparing market buy payload")

            if symbol is None:
                raise DataError("Must provide symbol")

            if time_in_force is None:
                raise DataError("Must provide time_in_force")

            if qty is not None and notional is not None:
                raise DataError("Must provide either qty or notional, not both")

            if qty is None and notional is None:
                raise DataError("Must provide either qty or notional")

            payload = {
                "symbol": str(symbol),
                "side": "buy",
                "type": "market",
                "time_in_force": str(time_in_force)
            }

            if qty is not None and float(qty) > 0:
                payload["qty"] = str(qty)
            elif notional is not None and float(notional) > 0:
                payload["notional"] = str(notional)

            return payload

        def prep_limit_buy_payload(self, symbol:str, qty=None, notional=None, time_in_force="day", limit_price: float):
            logger.info("Preparing limit buy payload")

            if symbol is None:
                raise DataError("Must provide symbol")

            if time_in_force is None:
                raise DataError("Must provide time_in_force")

            if limit_price is None:
                raise DataError("Must provide limit_price")

            if notional is not None and time_in_force !=  "day":
                raise DataError("Can only provide notional when time_in_force is day")

            if qty is not None and notional is not None:
                raise DataError("Must provide either qty or notional, not both")

            if qty is None and notional is None:
                raise DataError("Must provide either qty or notional")

            payload = {
                "symbol": str(symbol),
                "side": "buy",
                "type": "limit",
                "time_in_force": str(time_in_force),
            }

            if qty is not None and float(qty) > 0:
                payload["qty"] = str(qty)
            elif notional is not None and float(notional) > 0:
                payload["notional"] = str(notional)

            if limit_price is not None and float(limit_price) > 0:
                payload["limit_price"] = str(limit_price)

            return payload

        def prep_stop_buy_payload(self, symbol:str, qty=None, time_in_force="day", stop_price: float):
            logger.info("Preparing stop buy payload")

            if symbol is None:
                raise DataError("Must provide symbol")

            if time_in_force is None:
                raise DataError("Must provide time_in_force")

            if qty is None:
                raise DataError("Must provide qty, notional not allowed")

            if stop_price is None:
                raise DataError("Must provide stop_price")

            payload = {
                "symbol": str(symbol),
                "side": "buy",
                "type": "stop",
                "time_in_force": str(time_in_force),

            }

            if stop_price is not None and float(stop_price) > 0:
                payload["stop_price"] = str(stop_price)
            if qty is not None and float(qty) > 0:
                payload["qty"] = str(qty)

            return payload

        def prep_stop_limit_buy_payload(self, symbol:str, qty=None, time_in_force="day", limit_price:float, stop_price:float):
            logger.info("Preparing stop limit buy payload")

            if symbol is None:
                raise DataError("Must provide symbol")

            if time_in_force is None:
                raise DataError("Must provide time_in_force")

            if qty is None:
                raise DataError("Must provide qty, notional not allowed")

            if stop_price is None:
                raise DataError("Must provide stop_price")

            if limit_price is None:
                raise DataError("Must provide limit_price")

            if stop_price >= limit_price:
                raise DataError("Stop price must be smaller than limit price")

            payload = {
                "symbol": str(symbol),
                "side": "buy",
                "type": "stop_limit",
                "time_in_force": str(time_in_force),
            }

            if float(qty) > 0:
                payload["qty"] = str(qty)

            if float(stop_price) > 0:
                payload["stop_price"] = str(stop_price)

            if float(limit_price) > 0:
                payload["limit_price"] = str(limit_price)

            return payload

        def prep_market_sell_payload(self, symbol: str, qty=None, notional=None, time_in_force="day"):
            logger.info("Preparing market sell payload")

            if symbol is None:
                raise DataError("Must provide symbol")

            if time_in_force is None:
                raise DataError("Must provide time_in_force")

            if qty is not None and notional is not None:
                raise DataError("Must provide either qty or notional, not both")

            if qty is None and notional is None:
                raise DataError("Must provide either qty or notional")

            payload = {
                "symbol": str(symbol),
                "side": "sell",
                "type": "market",
                "time_in_force": str(time_in_force)
            }

            if qty is not None and float(qty) > 0:
                payload["qty"] = str(qty)
            elif notional is not None and float(notional) > 0:
                payload["notional"] = str(notional)

            return payload

        def prep_limit_sell_payload(self, symbol:str, qty = None, notional = None, time_in_force = "day", limit_price:float):
            logger.info("Preparing limit sell payload")

            if symbol is None:
                raise DataError("Must provide symbol")

            if time_in_force is None:
                raise DataError("Must provide time_in_force")

            if limit_price is None:
                raise DataError("Must provide limit_price")

            if notional is not None and time_in_force != "day":
                raise DataError("Can only provide notional when time_in_force is day")

            if qty is not None and notional is not None:
                raise DataError("Must provide either qty or notional, not both")

            if qty is None and notional is None:
                raise DataError("Must provide either qty or notional")

            payload = {
                "symbol": str(symbol),
                "side": "sell",
                "type": "limit",
                "time_in_force": str(time_in_force),
                "limit_price": str(limit_price)
            }

            if qty is not None:
                payload["qty"] = str(qty)
            elif notional is not None:
                payload["notional"] = str(notional)

            return payload


    def prep_stop_sell_payload(self, symbol:str, qty = None, time_in_force = "day", stop_price:float):
        logger.info("Preparing stop sell payload")

        if symbol is None:
            raise DataError("Must provide symbol")

        if time_in_force is None:
            raise DataError("Must provide time_in_force")

        if qty is None:
            raise DataError("Must provide qty, notional not allowed")

        if stop_price is None:
            raise DataError("Must provide stop_price")

        payload = {
            "symbol": str(symbol),
            "side": "sell",
            "type": "stop",
            "time_in_force": str(time_in_force),
        }

        if stop_price is not None and float(stop_price) > 0:
            payload["stop_price"] = str(stop_price)

        if qty is not None and float(qty) > 0:
            payload["qty"] = str(qty)

        return payload


    def prep_stop_limit_sell_payload(self, symbol:str, qty = None, time_in_force = "day", stop_price:float, limit_price:float):
        logger.info("Preparing stop limit sell payload")

        if symbol is None:
            raise DataError("Must provide symbol")

        if time_in_force is None:
            raise DataError("Must provide time_in_force")

        if qty is None:
            raise DataError("Must provide qty, notional not allowed")

        if stop_price is None:
            raise DataError("Must provide stop_price")

        if limit_price is None:
            raise DataError("Must provide limit_price")

        if limit_price <= 0:
            raise DataError("Must provide positive limit price")

        if stop_price <= 0:
            raise DataError("Must provide positive stop price")

        if stop_price <= limit_price:
            raise DataError("Stop price must be larger than limit price")

        payload = {
            "symbol": str(symbol),
            "side": "sell",
            "type": "stop_limit",
            "time_in_force": str(time_in_force)
        }

        if float(qty) > 0:
            payload["qty"] = str(qty)

        if float(stop_price) > 0:
            payload["stop_price"] = str(stop_price)

        if float(limit_price) > 0:
            payload["limit_price"] = str(limit_price)

        return payload


    def sell_order(self, payload):
        return self._request("POST", "/v2/market_orders", json=payload)

    def place_market_order(self, payload):
        return self._request("POST", "/v2/market_orders", json=payload)

    def liquidate_order(self, symbol):
        return self._request("DELETE", f"/v2/positions{symbol}")

    def see_orders(self):
        return self._request("GET", "/v2/orders")


alpaca_client = AlpacaClient()
account = alpaca_client.get_account()



