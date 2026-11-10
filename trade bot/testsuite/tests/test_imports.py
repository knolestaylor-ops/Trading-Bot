"""Every module in src must import cleanly: no errors, no printing, no network calls.

Each import runs in a fresh interpreter (so results don't depend on test order), from a
temporary working directory (so log files don't land in the repo), with proxies pointed
at a closed port (so any network call at import time fails instead of reaching Alpaca).
"""
import os
import subprocess
import sys

import pytest

from support import SRC

KNOWN_BROKEN = {
    "dataframe.marketdataframe": "demo code at import time appends an invalid sample bar (low > high)",
    "errors.strategy": "uses `from base import` instead of `from errors.base import`",
    "features.indicators.base": "features/indicators.py shadows the features/indicators/ package",
    "features.indicators.sma": "features/indicators.py shadows the features/indicators/ package",
    "ingestion.data_loader": "imports `alpaca_client` instead of `ingestion.alpaca_client`, "
                             "and calls the live API at import time",
    "strategy.strats.SMACrossover": "crossover() has no body (IndentationError)",
}


def discover_modules():
    for path in sorted(SRC.rglob("*.py")):
        parts = list(path.relative_to(SRC).with_suffix("").parts)
        if parts[-1] == "__init__":
            parts.pop()
        yield ".".join(parts)


MODULES = [
    pytest.param(name, marks=pytest.mark.xfail(reason=KNOWN_BROKEN[name])) if name in KNOWN_BROKEN else name
    for name in discover_modules()
]


def test_known_broken_list_is_up_to_date():
    assert set(KNOWN_BROKEN) <= set(discover_modules())


@pytest.mark.parametrize("module", MODULES)
def test_module_imports_cleanly(module, tmp_path):
    closed_port = "http://127.0.0.1:9"
    env = {
        **os.environ,
        "PYTHONPATH": str(SRC),
        "PYTHONDONTWRITEBYTECODE": "1",
        "HTTP_PROXY": closed_port, "HTTPS_PROXY": closed_port,
        "http_proxy": closed_port, "https_proxy": closed_port,
        "NO_PROXY": "", "no_proxy": "",
    }

    proc = subprocess.run(
        [sys.executable, "-c", f"import {module}"],
        cwd=tmp_path, env=env, capture_output=True, text=True, timeout=60,
    )

    assert proc.returncode == 0, proc.stderr
    assert proc.stdout == "", f"{module} printed at import time:\n{proc.stdout}"
