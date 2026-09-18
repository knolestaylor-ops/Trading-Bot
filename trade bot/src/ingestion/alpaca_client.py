# REST/Websocket client for Alpaca
import pandas as pd
import requests
from utils.config_loader import logger
from utils.decorators import retry, safe_api_call
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetAssetsRequest, MarketOrderRequest, GetOrdersRequest
from alpaca.trading.enums import AssetClass, OrderSide, TimeInForce, QueryOrderStatus


"""
1. Configuration
API key + secret (loaded from environment variables)
Optional: logging setup

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

Account





get_activities
get_account_config
update_account_config

Market
get_clock
is_market_open
get_calendar
Assets
get_asset(symbol)
list_assets
tradable_assets
validate_symbol(symbol)
Positions
get_all_positions
get_position(symbol)
close_position(symbol)
close_all_positions
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


api_key = "PKOZXTHYCD7VTBXATV5WOBVDCB"
api_secret = "8MMU6kSyGfebWUYmZYKNQkegNfPhMqRS1QkPBTh7JoQ6"


class AlpacaClient:
    def __init__(self):
        self.key = api_key
        self.secret = api_secret
        self.trading_client = TradingClient(api_key=api_key, secret_key=api_secret, paper=True)
        self.session = requests.Session()
        self.session.headers.update({
            "APCA-API-KEY-ID": self.key,
            "APCA-API-SECRET-KEY": self.secret})

        self.base_url = "https://paper-api.alpaca.com"

    @retry
    @safe_api_call
    def _request(self, method: str, endpoint: str, **kwargs):
        """
        Internal reliability gateway for all Alpaca REST calls.
        Handles:
        - URL building
        - HTTP request dispatch
        - JSON parsing
        - Error raising (caught by decorators)
        """

        # 1. Build full URL
        url = f"{self.base_url}{endpoint}"


        response = self.session.request(method, url, **kwargs)

        # 3. Raise HTTP errors (safe_api_call will catch these)
        response.raise_for_status()

        # 4. Parse JSON (safe_api_call will catch JSON errors)
        try:
            data = response.json()
        except ValueError:
            raise ValueError("Failed to parse JSON response from Alpaca")

        # 5. Return parsed JSON to public methods
        return data


    def get_account(self):
        return self._request("GET", "/v2/account")

    def get_buying_power(self):
        return self._request("GET", "/v2/buying_power")

    def get_equity(self):
        return self._request("GET", "/v2/equity")

    def get_balance_change(self, account):
        return float(account.equity) - float(account.last_equity)

    def get_cash(self, account):
        return self._request("GET", "/v2/cash", params={"account": account})


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


    def list_assets(self):
        logger.info("Listing assets")

        try:
            search_params = GetAssetsRequest(asset_class=AssetClass.US_EQUITY)
            assets = self.trading_client.get_all_assets(search_params)

            logger.info(f"assets found: {len(assets)}")
            logger.info(f"assets: {assets}")

            return assets

        except Exception as e:
            logger.error(f"Failed to list assets: {e}")
            raise

    def tradable_assets(self, assets):
        for asset in assets:
            if asset.tradable:
                logger.info(f"Tradable assets: {asset}")

    def prep_order(self):
        logger.info("Preparing order")

        try:
            market_order_data = MarketOrderRequest(symbol="AAPL", qty=1, side=OrderSide.BUY, time_in_force=TimeInForce.DAY)
            logger.info(f"Market order: {market_order_data}")

            return market_order_data

        except Exception as e:
            logger.error(f"Failed to prepare order: {e}")
            raise

    def place_market_order(self, market_order_data):
        logger.info("Placing market order")

        try:
            market_order = self.trading_client.submit_order(order_data=market_order_data)
            logger.info(f"Market order: {market_order}")
            return market_order

        except Exception as e:
            logger.error(f"Failed to place market order: {e}")
            raise

    def prepare_sell_order(self):
        logger.info("Preparing sell order")

        try:
            sell_order_data = MarketOrderRequest(symbol="AAPL", qty=1, side=OrderSide.SELL, time_in_force=TimeInForce.GTC)
            logger.info(f"Sell order: {sell_order_data}")

            return sell_order_data

        except Exception as e:
            logger.error(f"Failed to prepare sell order: {e}")
            raise


    def sell_order(self, sell_order_data):
        logger.info("Selling order")

        try:
            response = self.trading_client.submit_order(order_data=sell_order_data)
            logger.info(f"Sell order: {response}")

            return response

        except Exception as e:
            logger.error(f"Failed to sell order: {e}")
            raise

    def liquidate_order(self):
        pass

    def see_orders(self):
        logger.info("Seeing orders")

        try:
            get_orders_data = GetOrdersRequest(status=QueryOrderStatus.OPEN, limit=100, nested=True)
            orders = self.trading_client.get_orders(filter=get_orders_data)
            logger.info(f"Orders found: {len(orders)}")
            logger.info(f"Orders: {orders}")

        except Exception as e:
            logger.error(f"Failed to get orders: {e}")
            raise


alpaca_client = AlpacaClient()

account = alpaca_client.get_account()
alpaca_client.get_buying_power(account)

