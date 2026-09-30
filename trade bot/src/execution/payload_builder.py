
from utils.config_loader import logger
from errors.retryable import *


# Refactor with helper functions, not neccessary right now, but will help with readability and testing.


class PayloadBuilder:
    ALLOWED_TIFS = {"day", "gtc", "opg", "cls", "ioc", "fok"}

    def _validate_symbol(self, symbol: str):
        pass
    def _validate_time_in_force(self, time_in_force: str):
        pass
    def _validate_limit_price(self, limit_price: float):
        pass
    def _validate_stop_price(self, stop_price: float):
        pass
    def _validate_qty(self, qty: float):
        pass
    def _validate_notional(self, notional: float):
        pass
    def _validate_mutual_exclusive(self, mutual_exclusive: bool):
        pass


    def market_buy(self, symbol: str, time_in_force, qty=None, notional=None):
        logger.info("Preparing market buy payload")

        if symbol is None:
            raise DataError("Must provide symbol")

        if time_in_force not in PayloadBuilder.ALLOWED_TIFS:
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

        if qty is not None:
            if float(qty) <= 0:
                raise DataError("Must provide positive qty")
            payload["qty"] = str(qty)
        elif notional is not None:
            if float(notional) <= 0:
                raise DataError("Must provide positive notional")
            payload["notional"] = str(notional)

        return payload

    def limit_buy(self, symbol: str, time_in_force, limit_price: float, qty=None, notional=None):
        logger.info("Preparing limit buy payload")

        if symbol is None:
            raise DataError("Must provide symbol")

        if time_in_force not in PayloadBuilder.ALLOWED_TIFS:
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
            "side": "buy",
            "type": "limit",
            "time_in_force": str(time_in_force),
        }

        if qty is not None:
            if float(qty) <= 0:
                raise DataError("Must provide positive qty")
            payload["qty"] = str(qty)
        elif notional is not None:
            if float(notional) <= 0:
                raise DataError("Must provide positive notional")
            payload["notional"] = str(notional)

        if limit_price is not None:
            if float(limit_price) <= 0:
                raise DataError("Must provide positive limit_price")
            payload["limit_price"] = str(limit_price)

        return payload

    def stop_buy(self, symbol: str, time_in_force, stop_price: float, qty=None):
        logger.info("Preparing stop buy payload")

        if symbol is None:
            raise DataError("Must provide symbol")

        if time_in_force not in PayloadBuilder.ALLOWED_TIFS:
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

        if stop_price is not None:
            if float(stop_price) <= 0:
                raise DataError("Must provide positive stop_price")
            payload["stop_price"] = str(stop_price)
        if qty is not None:
            if float(qty) <= 0:
                raise DataError("Must provide positive qty")
            payload["qty"] = str(qty)

        return payload

    def stop_limit_buy(self, symbol: str,time_in_force, limit_price: float,stop_price: float, qty=None):
        logger.info("Preparing stop limit buy payload")

        if symbol is None:
            raise DataError("Must provide symbol")

        if time_in_force not in PayloadBuilder.ALLOWED_TIFS:
            raise DataError("Must provide time_in_force")

        if qty is None:
            raise DataError("Must provide qty, notional not allowed")

        if stop_price is None:
            raise DataError("Must provide stop_price")

        if limit_price is None:
            raise DataError("Must provide limit_price")

        try:
            if qty is not None:
                if float(qty) <= 0:
                    raise DataError("Must provide positive qty")
            if stop_price is not None:
                if float(stop_price) <= 0:
                    raise DataError("Must provide positive stop_price")
            if limit_price is not None:
                if float(limit_price) <= 0:
                    raise DataError("Must provide positive limit_price")
        except ValueError:
            raise DataError("qty, stop_price, limit_price must be numerical")

        if float(stop_price) <= float(limit_price):
            raise DataError("Stop price must be larger than limit price")

        payload = {
            "symbol": str(symbol),
            "side": "buy",
            "type": "stop_limit",
            "time_in_force": str(time_in_force),
            "qty": str(qty),
            "stop_price": str(stop_price),
            "limit_price": str(limit_price)
        }

        return payload

    def market_sell(self, symbol: str, time_in_force, qty=None, notional=None):
        logger.info("Preparing market sell payload")

        if symbol is None:
            raise DataError("Must provide symbol")

        if time_in_force not in PayloadBuilder.ALLOWED_TIFS:
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

        if qty is not None:
            if float(qty) <= 0:
                raise DataError("Must provide positive qty")
            payload["qty"] = str(qty)
        elif notional is not None:
            if float(notional) <= 0:
                raise DataError("Must provide positive notional")
            payload["notional"] = str(notional)

        return payload

    def limit_sell(self, symbol: str, time_in_force, limit_price: float, qty=None, notional=None):
        logger.info("Preparing limit sell payload")

        if symbol is None:
            raise DataError("Must provide symbol")

        if time_in_force not in PayloadBuilder.ALLOWED_TIFS:
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
            if float(qty) <= 0:
                raise DataError("Must provide positive qty")
            payload["qty"] = str(qty)
        elif notional is not None:
            if float(notional) <= 0:
                raise DataError("Must provide positive notional")
            payload["notional"] = str(notional)

        if limit_price is not None:
            if float(limit_price) <= 0:
                raise DataError("Must provide positive limit_price")
            payload["limit_price"] = str(limit_price)

        return payload

    def stop_sell(self, symbol: str, time_in_force, stop_price: float, qty=None):
        logger.info("Preparing stop sell payload")

        if symbol is None:
            raise DataError("Must provide symbol")

        if time_in_force not in PayloadBuilder.ALLOWED_TIFS:
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

        if stop_price is not None:
            if float(stop_price) <= 0:
                raise DataError("Must provide positive stop_price")
            payload["stop_price"] = str(stop_price)
        if qty is not None:
            if float(qty) <= 0:
                raise DataError("Must provide positive qty")
            payload["qty"] = str(qty)

        return payload

    def stop_limit_sell(self, symbol: str, time_in_force, limit_price: float,stop_price: float, qty=None):
        logger.info("Preparing stop limit sell payload")

        if symbol is None:
            raise DataError("Must provide symbol")

        if time_in_force not in PayloadBuilder.ALLOWED_TIFS:
            raise DataError("Must provide time_in_force")

        if qty is None:
            raise DataError("Must provide qty, notional not allowed")

        if stop_price is None:
            raise DataError("Must provide stop_price")

        if limit_price is None:
            raise DataError("Must provide limit_price")

        try:
            if qty is not None:
                if float(qty) <= 0:
                    raise DataError("Must provide positive qty")
            if stop_price is not None:
                if float(stop_price) <= 0:
                    raise DataError("Must provide positive stop_price")
            if limit_price is not None:
                if float(limit_price) <= 0:
                    raise DataError("Must provide positive limit_price")
        except:
            raise DataError("qty, stop_price, limit_price must be numerical")

        if float(stop_price) <= float(limit_price):
            raise DataError("Stop price must be larger than limit price")

        payload = {
            "symbol": str(symbol),
            "side": "sell",
            "type": "stop_limit",
            "time_in_force": str(time_in_force),
            "qty": str(qty),
            "stop_price": str(stop_price),
            "limit_price": str(limit_price)
        }

        return payload