# Trading-Bot
A modular algorithmic trading system built with Python, Polars, and the Alpaca API.

Features:
Market data ingestion
Data validation
Technical indicators
Strategy engine
Risk Management
Order execution


```mermaid
flowchart TD

    A[Alpaca Client] --> B[Market Data Fetcher]
    B --> C[Bar Validation]

    C --> D[Trading DataFrame]

    D --> E[Indicator Engine]

    E --> F[SMA]
    E --> G[Golden Cross]
    E --> H[Triple SMA]

    F --> I[Feature Store]
    G --> I
    H --> I

    D --> I

    I --> J[Target Generator]

    J --> K[Training Dataset]

    K --> L[ML Model]
    L --> M[Predictions]

    M --> N[Strategy Engine]

    N --> O[Risk Management]

    O --> P[Order Manager]

    P --> Q[Alpaca Trading API]
```






## Running the tests

```bash
cd "trade bot"
pip install -r requirements-dev.txt
pytest
```

Known bugs are covered by tests marked `xfail` with the reason. To list them, run
`pytest -rx`. `xfail_strict` is on, so when a bug is fixed its test reports `XPASS`
and fails the run until the marker is removed.
