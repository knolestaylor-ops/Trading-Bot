import pytest

from ingestion import alpaca_client as alpaca_module
from support import DummyResponse, DummySession


@pytest.fixture(autouse=True)
def sleeps(monkeypatch):
    """Make retry backoff instant and record the requested sleep durations."""
    calls = []
    monkeypatch.setattr("utils.decorators.time.sleep", calls.append)
    return calls


@pytest.fixture
def client(monkeypatch):
    # The module reads API_KEY/API_SECRET once at import time, so setting env vars
    # here would have no effect; patch the module-level values instead.
    monkeypatch.setattr(alpaca_module, "api_key", "test_key")
    monkeypatch.setattr(alpaca_module, "api_secret", "test_secret")

    c = alpaca_module.AlpacaClient()
    c.session = DummySession(headers=c.session.headers)
    return c


@pytest.fixture
def respond(client):
    """Set the response every following request on `client` receives."""

    def _respond(json_data=None, status_code=200, text=None):
        client.session.response = DummyResponse(status_code=status_code, text=text, json_data=json_data)

    return _respond
