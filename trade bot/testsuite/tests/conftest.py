import pytest
from alpaca_client import AlpacaClient


@pytest.fixture
def client(monkeypatch):
    # Avoid using real env vars in tests
    monkeypatch.setenv("API_KEY", "test_key")
    monkeypatch.setenv("API_SECRET", "test_secret")

    c = AlpacaClient()

    # Replace real session with a dummy one we can control
    class DummySession:
        def __init__(self):
            self.headers = {}
            self.last_request = None
            self.response = None

        def request(self, method, url, **kwargs):
            self.last_request = {"method": method, "url": url, "kwargs": kwargs}
            return self.response

    c.session = DummySession()
    return c
