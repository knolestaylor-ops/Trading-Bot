"""Helpers shared by the test modules."""
import ast
import json
import types
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src"

TRADING_URL = "https://paper-api.alpaca.markets"
DATA_URL = "https://data.alpaca.markets"


class DummyResponse:
    """Minimal stand-in for requests.Response."""

    def __init__(self, status_code=200, text=None, json_data=None):
        self.status_code = status_code
        self._json_data = json_data
        if text is None:
            text = "" if json_data is None else json.dumps(json_data)
        self.text = text

    def json(self):
        if self._json_data is None:
            raise ValueError("No JSON")
        return self._json_data


class DummySession:
    """Stand-in for requests.Session that records every call.

    Responses are taken from `queue` first (an item may be an exception to raise),
    then from `response`.
    """

    def __init__(self, headers=None):
        self.headers = dict(headers or {})
        self.calls = []
        self.queue = []
        self.response = None

    @property
    def last_request(self):
        return self.calls[-1] if self.calls else None

    def request(self, method, url, **kwargs):
        self.calls.append({"method": method, "url": url, "kwargs": kwargs})
        item = self.queue.pop(0) if self.queue else self.response
        if isinstance(item, BaseException):
            raise item
        return item


def load_definitions(dotted_name, skip_imports=()):
    """Load a module's imports, classes, functions and literal constants only.

    Some modules run demo code at import time that crashes or calls the live API
    (marketdataframe.py, data_loader.py). This executes everything except that code
    so the classes can still be tested. `skip_imports` drops `from X import ...` lines
    whose module X is listed (for imports that are themselves broken).
    """
    path = SRC.joinpath(*dotted_name.split(".")).with_suffix(".py")
    tree = ast.parse(path.read_text(), filename=str(path))

    kept = []
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module in skip_imports:
            continue
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            kept.append(node)
        elif isinstance(node, ast.Assign):
            try:
                ast.literal_eval(node.value)
            except Exception:
                continue
            kept.append(node)
    tree.body = kept

    module = types.ModuleType(f"{dotted_name}__definitions")
    module.__file__ = str(path)
    exec(compile(tree, str(path), "exec"), module.__dict__)
    return module
