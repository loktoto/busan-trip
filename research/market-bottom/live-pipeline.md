# IBKR → GitHub deterministic live pipeline

## Production flow

1. The hourly monitor retrieves market-only data from Interactive Brokers for `SPY`, `QQQ`, `SOXX` and the informational `SMH` reference.
2. The monitor normalises the payload to `live-input.schema.json` and replaces `runtime/market-bottom/latest-input.json` on branch `agent/market-bottom-strategy`.
3. That single input-path update triggers `.github/workflows/market-bottom-live.yml`.
4. GitHub Actions runs `live_monitor.py` with the repository-pinned Python code and `config.example.json`.
5. The workflow archives the exact input and output, then publishes:
   - `runtime/market-bottom/latest-result.json`;
   - `runtime/market-bottom/latest-report.md`.
6. The monitor reads the GitHub-produced result. It does not independently recalculate the official state.
7. The monitor sends at 10:00 and 21:00 HKT, or immediately when the GitHub result reports a material change.

## Input rule

The repository is public. The runtime payload may contain public-market OHLCV, volatility fields, timestamps, source/status labels and approved point-in-time market features only.

It must never contain:

- account identifiers;
- NAV, cash, positions, orders or executions;
- cookies, tokens, credentials or session material;
- user identity or personal information;
- private analyst notes or licensed datasets that prohibit redistribution.

## Determinism and audit

Every output records:

- request ID;
- input timestamp and bar status;
- input SHA-256;
- GitHub model commit SHA;
- official completed-bar date;
- asset state and model inputs;
- model candidate tranche and cumulative model deployment;
- SMH/SOXX informational pair classification;
- material differences from the previous GitHub result.

Signals use completed daily bars. Intraday snapshots are context and cannot silently overwrite the official completed-close state.

## Governance

- Primary targets: `SPY`, `QQQ`, `SOXX`.
- `SMH` is a displayed semiconductor reference only; its production weight is fixed at zero until a leakage-safe paired test promotes it.
- No GitHub workflow places or transmits an order.
- A failed or stale GitHub run means `NO FRESH OFFICIAL RESULT`; the monitor must not substitute a prompt-calculated state.
- Backtests are not rerun hourly.
