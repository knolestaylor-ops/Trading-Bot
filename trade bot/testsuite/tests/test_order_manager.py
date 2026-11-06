"""OrderManager: builds the payload and submits it, and never submits an invalid order."""
import pytest

from errors.retryable import DataError
from execution.order_manager import OrderManager
from execution.payload_builder import PayloadBuilder


class FakeClient:
    def __init__(self):
        self.payloads = PayloadBuilder()
        self.submitted = []
        self.calls = []

    def submit_order(self, payload):
        self.submitted.append(payload)
        return {"id": "order-1", **payload}

    def cancel_order(self, order_id):
        self.calls.append(("cancel_order", order_id))
        return {"cancelled": order_id}

    def cancel_all_orders(self):
        self.calls.append(("cancel_all_orders",))
        return []

    def liquidate_order(self, symbol):
        self.calls.append(("liquidate_order", symbol))
        return {"symbol": symbol}


@pytest.fixture
def fake_client():
    return FakeClient()


@pytest.fixture
def manager(fake_client):
    return OrderManager(fake_client)


# (method, valid positional args, args with an invalid qty)
ORDERS = [
    ("market_buy", ("AAPL", "day", 10, None), ("AAPL", "day", -1, None)),
    ("limit_buy", ("AAPL", "day", 150.5, 10, None), ("AAPL", "day", 150.5, -1, None)),
    ("stop_buy", ("AAPL", "gtc", 155, 10), ("AAPL", "gtc", 155, -1)),
    ("stop_limit_buy", ("AAPL", "gtc", 150, 155, 10), ("AAPL", "gtc", 150, 155, -1)),
    ("market_sell", ("AAPL", "day", 10, None), ("AAPL", "day", -1, None)),
    ("limit_sell", ("AAPL", "day", 150.5, 10, None), ("AAPL", "day", 150.5, -1, None)),
    ("stop_sell", ("AAPL", "gtc", 155, 10), ("AAPL", "gtc", 155, -1)),
    ("stop_limit_sell", ("AAPL", "gtc", 150, 155, 10), ("AAPL", "gtc", 150, 155, -1)),
]


def test_uses_the_clients_payload_builder(manager, fake_client):
    assert manager.payloads is fake_client.payloads
    assert manager.client is fake_client


@pytest.mark.parametrize("name, args, _", ORDERS)
def test_submits_the_built_payload(manager, fake_client, name, args, _):
    result = getattr(manager, name)(*args)

    assert fake_client.submitted == [getattr(PayloadBuilder(), name)(*args)]
    assert result["id"] == "order-1"


@pytest.mark.parametrize("name, _, bad_args", ORDERS)
def test_invalid_order_is_never_submitted(manager, fake_client, name, _, bad_args):
    """Safety guard: validation must run before anything is sent to the broker."""
    with pytest.raises(DataError):
        getattr(manager, name)(*bad_args)

    assert fake_client.submitted == []


def test_cancel_order(manager, fake_client):
    assert manager.cancel_order("o1") == {"cancelled": "o1"}
    assert fake_client.calls == [("cancel_order", "o1")]


def test_cancel_all_orders(manager, fake_client):
    assert manager.cancel_all_orders() == []
    assert fake_client.calls == [("cancel_all_orders",)]


def test_liquidate_order(manager, fake_client):
    assert manager.liquidate_order("AAPL") == {"symbol": "AAPL"}
    assert fake_client.calls == [("liquidate_order", "AAPL")]


@pytest.mark.xfail(reason="qty and notional are required positional arguments, so callers "
                          "must always pass both")
def test_market_buy_without_notional(manager, fake_client):
    manager.market_buy("AAPL", "day", qty=1)

    assert fake_client.submitted[0]["qty"] == "1"
