from utils.config_loader import logger


class OrderManager:
    def __init__(self, client):
        self.client = client
        self.payloads = client.payloads
        self.logger = logger

    def market_buy(self, symbol, time_in_force, qty, notional):
        payload = self.payloads.market_buy(symbol, time_in_force, qty, notional)
        return self.client.submit_order(payload)

    def limit_buy(self, symbol, time_in_force, limit_price, qty, notional):
        payload = self.payloads.limit_buy(symbol, time_in_force, limit_price, qty, notional)
        return self.client.submit_order(payload)

    def stop_buy(self, symbol, time_in_force, stop_price, qty):
        payload = self.payloads.stop_buy(symbol, time_in_force, stop_price, qty)
        return self.client.submit_order(payload)

    def stop_limit_buy(self, symbol, time_in_force, limit_price, stop_price, qty):
        payload = self.payloads.stop_limit_buy(symbol, time_in_force, limit_price, stop_price, qty)
        return self.client.submit_order(payload)

    def market_sell(self, symbol, time_in_force, qty, notional):
        payload = self.payloads.market_sell(symbol, time_in_force, qty, notional)
        return self.client.submit_order(payload)

    def limit_sell(self, symbol, time_in_force, limit_price, qty, notional):
        payload = self.payloads.limit_sell(symbol, time_in_force, limit_price, qty, notional)
        return self.client.submit_order(payload)

    def stop_sell(self, symbol, time_in_force, stop_price, qty):
        payload = self.payloads.stop_sell(symbol, time_in_force, stop_price, qty)
        return self.client.submit_order(payload)

    def stop_limit_sell(self, symbol, time_in_force, limit_price, stop_price, qty):
        payload = self.payloads.stop_limit_sell(symbol, time_in_force, limit_price, stop_price, qty)
        return self.client.submit_order(payload)

    def cancel_order(self, order_id):
        return self.client.cancel_order(order_id)

    def cancel_all_orders(self):
        return self.client.cancel_all_orders()

    def liquidate_order(self, symbol):
        return self.client.liquidate_order(symbol)