# Multi-Timeframe TA Performance Ledger

This directory is the permanent audit trail for the 21-ticker hourly multi-timeframe TA monitor.

## Purpose

Record every model-generated **entry, re-entry, add, failed breakout/retest, stop, target hit, invalidation and material setup revision** so the strategy can be evaluated objectively rather than by selective memory.

## Source policy

1. IBKR live or near-live data is primary.
2. Reliable fallback sources may be used when IBKR is unavailable, but the source and data quality must be recorded.
3. No signal may be marked `VALIDATED 7+` without the required second pass.
4. No orders are created or transmitted from this ledger.

## Files

- `signals.csv` — append-only signal/event ledger.
- `performance-methodology.md` — outcome and performance measurement rules.

## Core rule

A signal is recorded when the monitor determines that an entry, re-entry or add **should be taken under its own frozen rules**, regardless of whether the user actually trades it. Actual portfolio trades are tracked separately and must never be substituted for model signals.
