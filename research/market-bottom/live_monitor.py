#!/usr/bin/env python3
"""Deterministic live market-bottom calculation from a normalized IBKR payload.

The caller supplies completed daily OHLCV and an optional current snapshot.  The
engine reuses the audited research indicators and configuration, calculates the
official completed-close state, and writes machine-readable JSON plus Markdown.
It never connects to IBKR and never places orders.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from backtest import (
    Config,
    episode_ids,
    indicators,
    load_config,
    run,
    target_deployment,
)

PRIMARY = ("SPY", "QQQ", "SOXX")
REFERENCE = "SMH"
REQUIRED = PRIMARY + (REFERENCE,)
SCHEMA_VERSION = "1.0"
STATE_NAMES = {
    0: "NO_SETUP",
    1: "BOTTOM_WATCH",
    2: "CLOSE_TO_BOTTOM_CANDIDATE",
    3: "EXHAUSTION_ZONE",
    4: "BOTTOM_ZONE_CONFIRMED",
    5: "RECOVERY_UNDERWAY",
    6: "FAILED_SETUP",
}


def _finite(value: Any) -> float | None:
    try:
        x = float(value)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


def _canonical_hash(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _validate_payload(payload: dict[str, Any]) -> None:
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"schema_version must be {SCHEMA_VERSION}")
    if payload.get("source") != "IBKR":
        raise ValueError("source must be IBKR")
    assets = payload.get("assets")
    if not isinstance(assets, dict):
        raise ValueError("assets must be an object")
    missing = set(REQUIRED) - set(assets)
    extra = set(assets) - set(REQUIRED)
    if missing or extra:
        raise ValueError(f"assets must be exactly {REQUIRED}; missing={sorted(missing)} extra={sorted(extra)}")
    for symbol in REQUIRED:
        bars = assets[symbol].get("bars")
        if not isinstance(bars, list) or len(bars) < 260:
            raise ValueError(f"{symbol} requires at least 260 completed daily bars")


def _bars_frame(rows: list[dict[str, Any]]) -> pd.DataFrame:
    cols = ["Date", "Open", "High", "Low", "Close", "Volume"]
    df = pd.DataFrame(rows)
    missing = set(cols) - set(df.columns)
    if missing:
        raise ValueError(f"missing OHLCV columns: {sorted(missing)}")
    df = df[cols].copy()
    df["Date"] = pd.to_datetime(df["Date"], utc=True).dt.tz_convert(None)
    for col in cols[1:]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna().sort_values("Date").drop_duplicates("Date", keep="last").reset_index(drop=True)
    if len(df) < 260:
        raise ValueError("fewer than 260 valid rows after normalization")
    if (df[["Open", "High", "Low", "Close"]] <= 0).any().any():
        raise ValueError("prices must be positive")
    if (df["Volume"] < 0).any():
        raise ValueError("volume cannot be negative")
    if (df["High"] < df[["Open", "Close", "Low"]].max(axis=1)).any():
        raise ValueError("inconsistent high")
    if (df["Low"] > df[["Open", "Close", "High"]].min(axis=1)).any():
        raise ValueError("inconsistent low")
    return df


def _features_frame(rows: Any) -> pd.DataFrame | None:
    if not rows:
        return None
    if not isinstance(rows, list):
        raise ValueError("features must be a list when supplied")
    f = pd.DataFrame(rows)
    if "Date" not in f:
        raise ValueError("features require Date")
    f["Date"] = pd.to_datetime(f["Date"], utc=True).dt.tz_convert(None)
    for col in f.columns:
        if col != "Date":
            f[col] = pd.to_numeric(f[col], errors="coerce")
    return f.sort_values("Date").drop_duplicates("Date", keep="last")


def _state(latest: pd.Series, prior: pd.Series, cfg: Config) -> int:
    dd = float(latest.cycle_dd)
    if bool(latest.credit_veto) and dd <= -cfg.watch_dd:
        return 6
    if dd > -cfg.watch_dd:
        return 0
    if dd > -cfg.start_dd:
        return 1
    if bool(latest.confirmation):
        recovery = (
            _finite(latest.get("r20")) is not None
            and float(latest.r20) > 0
            and _finite(latest.get("sma20")) is not None
            and float(latest.Close) > float(latest.sma20)
            and _finite(prior.get("atrp")) is not None
            and float(latest.atrp) <= float(prior.atrp)
        )
        return 5 if recovery else 4
    if bool(latest.exhaustion):
        return 3
    if bool(latest.newlow10 or latest.newlow20 or latest.crash):
        return 2
    return 1


def _candidate(x: pd.DataFrame, trades: pd.DataFrame, cfg: Config) -> dict[str, Any]:
    i = len(x) - 1
    latest = x.iloc[i]
    prior = x.iloc[i - 1]
    eid = int(latest.episode)
    episode_trades = trades.loc[trades.episode == eid].sort_values("execution_index") if eid and not trades.empty else pd.DataFrame()
    used = float(episode_trades.tranche.sum()) if not episode_trades.empty else 0.0
    result: dict[str, Any] = {
        "current_episode": eid,
        "cumulative_model_deployment": used,
        "candidate_tranche": 0.0,
        "candidate_target_cumulative": used,
        "candidate_reason": "NONE",
        "eligible_at_next_open": False,
    }
    if eid == 0 or float(latest.cycle_dd) > -cfg.start_dd or bool(latest.credit_veto):
        return result

    want = target_deployment(float(latest.cycle_dd), cfg)
    if bool(latest.long_bear) and not bool(latest.exhaustion) and not bool(latest.confirmation):
        want = min(want, cfg.long_bear_cap)

    exhaustion_transition = bool(latest.exhaustion) and not bool(prior.exhaustion)
    confirmation_transition = bool(latest.confirmation) and not bool(prior.confirmation)
    if exhaustion_transition:
        want = max(want, used + cfg.exhaustion_bonus)
    if confirmation_transition:
        want = max(want, used + cfg.confirmation_bonus)
    want = min(want, cfg.max_deploy)

    fresh = bool(latest.newlow10 or latest.newlow20)
    crash = bool(latest.crash)
    if episode_trades.empty:
        cooldown_ok = spacing_ok = True
    else:
        last = episode_trades.iloc[-1]
        cooldown_ok = i - int(last.execution_index) >= cfg.cooldown
        spacing_ok = float(latest.Close) <= float(last.execution_price) * (1 - cfg.spacing)
    event = fresh or crash or exhaustion_transition or confirmation_transition
    eligible = event and (cooldown_ok or spacing_ok or confirmation_transition)
    if not eligible:
        result["candidate_target_cumulative"] = float(want)
        result["candidate_reason"] = "WAIT_COOLDOWN_OR_PRICE_SPACING" if event else "NO_NEW_EVENT"
        return result

    if used == 0:
        want = max(want, cfg.micro_probe)
    tranche = min(max(0.0, want - used), cfg.max_tranche, cfg.max_deploy - used)
    if tranche < cfg.min_tranche:
        result["candidate_target_cumulative"] = float(want)
        result["candidate_reason"] = "BELOW_MINIMUM_TRANCHE"
        return result

    reasons = []
    if fresh:
        reasons.append("FRESH_LOW")
    if crash:
        reasons.append("CRASH_OVERRIDE")
    if exhaustion_transition:
        reasons.append("EXHAUSTION_TRANSITION")
    if confirmation_transition:
        reasons.append("CONFIRMATION_TRANSITION")
    result.update(
        {
            "candidate_tranche": float(tranche),
            "candidate_target_cumulative": float(used + tranche),
            "candidate_reason": "+".join(reasons),
            "eligible_at_next_open": True,
        }
    )
    return result


def _asset_result(symbol: str, item: dict[str, Any], config_path: Path) -> tuple[dict[str, Any], pd.DataFrame]:
    cfg = load_config(config_path, symbol)
    df = _bars_frame(item["bars"])
    features = _features_frame(item.get("features"))
    x = indicators(df, cfg, features)
    x["episode"] = episode_ids(x, cfg)
    trades, _ = run(x, cfg)
    latest, prior = x.iloc[-1], x.iloc[-2]
    state = _state(latest, prior, cfg)
    c = _candidate(x, trades, cfg)
    cycle_high = float(latest.cycle_high)
    atr = float(latest.atr14)
    prior_low20 = _finite(latest.prior_low20)
    result = {
        "symbol": symbol,
        "official_bar_date": latest.Date.date().isoformat(),
        "official_close": float(latest.Close),
        "state": state,
        "state_name": STATE_NAMES[state],
        "cycle_high": cycle_high,
        "cycle_drawdown": float(latest.cycle_dd),
        "drawdown_52w": float(latest.dd_52w),
        "returns": {f"r{n}": _finite(latest.get(f"r{n}")) for n in (1, 3, 5, 10, 20, 63)},
        "atr14": atr,
        "atr_percent": float(latest.atrp),
        "realized_vol_20d": float(latest.rv20),
        "volume_ratio_20d": float(latest.vol_ratio),
        "close_location": float(latest.close_loc),
        "sell_pressure": float(latest.sell_pressure),
        "underwater_days": int(latest.underwater),
        "long_bear": bool(latest.long_bear),
        "new_low_10d": bool(latest.newlow10),
        "new_low_20d": bool(latest.newlow20),
        "crash": bool(latest.crash),
        "exhaustion": bool(latest.exhaustion),
        "exhaustion_score": int(latest.exhaustion_score),
        "confirmation": bool(latest.confirmation),
        "confirmation_score": int(latest.confirmation_score),
        "credit_veto": bool(latest.credit_veto),
        "levels": {
            "watch": cycle_high * (1 - cfg.watch_dd),
            "probe_start": cycle_high * (1 - cfg.start_dd),
            "prior_low_20d": prior_low20,
            "reclaim_sma10": _finite(latest.sma10),
            "reclaim_sma20": _finite(latest.sma20),
            "provisional_failure_close": None if prior_low20 is None else prior_low20 - atr,
        },
        "model": asdict(cfg),
        "snapshot": item.get("snapshot", {}),
        **c,
    }
    return result, x


def _pair(soxx: dict[str, Any], smh: dict[str, Any], frames: dict[str, pd.DataFrame]) -> dict[str, Any]:
    sx, mh = frames["SOXX"].iloc[-1], frames["SMH"].iloc[-1]
    if bool(mh.newlow20) and float(mh.rv20) > float(frames["SMH"].iloc[-6].rv20) and float(mh.sell_pressure) > float(frames["SMH"].iloc[-6].sell_pressure):
        label = "VETO_LIKE_DETERIORATION"
    elif bool(sx.newlow20) and not bool(mh.newlow20) and float(mh.rv20) < float(frames["SMH"].iloc[-6].rv20):
        label = "POSITIVE_DIVERGENCE"
    elif soxx["state"] >= 3 and smh["state"] >= 3 and abs(soxx["state"] - smh["state"]) <= 1:
        label = "CONFIRMS"
    elif abs(soxx["state"] - smh["state"]) >= 2:
        label = "DIVERGES"
    else:
        label = "NEUTRAL"
    return {
        "classification": label,
        "production_weight": 0.0,
        "governance": "INFORMATIONAL_ONLY_NOT_PROMOTED",
        "soxx_state": soxx["state"],
        "smh_state": smh["state"],
        "drawdown_gap": float(smh["cycle_drawdown"] - soxx["cycle_drawdown"]),
    }


def _material_changes(previous: dict[str, Any] | None, current: dict[str, Any]) -> list[dict[str, Any]]:
    if not previous:
        return [{"type": "INITIAL_RESULT"}]
    changes: list[dict[str, Any]] = []
    old_assets = previous.get("assets", {})
    for symbol in PRIMARY:
        old, new = old_assets.get(symbol, {}), current["assets"][symbol]
        if old.get("state") != new.get("state"):
            changes.append({"type": "STATE", "symbol": symbol, "old": old.get("state"), "new": new.get("state")})
        if bool(old.get("eligible_at_next_open")) != bool(new.get("eligible_at_next_open")) or not math.isclose(float(old.get("candidate_tranche", 0.0)), float(new.get("candidate_tranche", 0.0)), abs_tol=1e-12):
            changes.append({"type": "TRANCHE", "symbol": symbol, "old": old.get("candidate_tranche", 0.0), "new": new.get("candidate_tranche", 0.0)})
    old_pair = previous.get("semiconductor_pair", {}).get("classification")
    new_pair = current.get("semiconductor_pair", {}).get("classification")
    if old_pair != new_pair:
        changes.append({"type": "PAIR", "old": old_pair, "new": new_pair})
    return changes


def _markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Bottom Zone Monitor — GitHub deterministic result",
        "",
        f"- Request: `{result['request_id']}`",
        f"- Input source: `{result['source']}`",
        f"- Input created: `{result['input_created_at']}`",
        f"- Model commit: `{result['model_commit']}`",
        f"- Input SHA256: `{result['input_sha256']}`",
        "",
        "| Asset | Close | Cycle DD | 52W DD | State | Candidate tranche | Cumulative |",
        "|---|---:|---:|---:|---|---:|---:|",
    ]
    for symbol in PRIMARY:
        a = result["assets"][symbol]
        lines.append(
            f"| {symbol} | {a['official_close']:.2f} | {a['cycle_drawdown']:.2%} | {a['drawdown_52w']:.2%} | {a['state']} {a['state_name']} | {a['candidate_tranche']:.2%} | {a['cumulative_model_deployment']:.2%} |"
        )
    smh = result["assets"]["SMH"]
    lines.extend(
        [
            "",
            "## SMH reference",
            f"SMH close {smh['official_close']:.2f}; cycle drawdown {smh['cycle_drawdown']:.2%}; state {smh['state']} {smh['state_name']}. No tranche is assigned.",
            "",
            "## Semiconductor pair",
            f"`{result['semiconductor_pair']['classification']}` — informational only; production weight remains zero.",
            "",
            "## Material changes",
        ]
    )
    if result["material_changes"]:
        lines.extend(f"- `{json.dumps(c, ensure_ascii=False, sort_keys=True)}`" for c in result["material_changes"])
    else:
        lines.append("- None")
    lines.extend(["", "> Research signal only. No order is created or transmitted."])
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--config", type=Path, required=True)
    ap.add_argument("--previous", type=Path)
    ap.add_argument("--result", type=Path, required=True)
    ap.add_argument("--report", type=Path, required=True)
    args = ap.parse_args()

    payload = json.loads(args.input.read_text())
    _validate_payload(payload)
    previous = None
    if args.previous and args.previous.exists():
        previous = json.loads(args.previous.read_text())

    assets: dict[str, Any] = {}
    frames: dict[str, pd.DataFrame] = {}
    for symbol in REQUIRED:
        assets[symbol], frames[symbol] = _asset_result(symbol, payload["assets"][symbol], args.config)
    assets["SMH"]["candidate_tranche"] = 0.0
    assets["SMH"]["eligible_at_next_open"] = False
    assets["SMH"]["candidate_reason"] = "REFERENCE_ONLY"

    result: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "request_id": payload.get("request_id", "UNSPECIFIED"),
        "source": "IBKR",
        "input_created_at": payload.get("created_at"),
        "calculated_at": datetime.now(timezone.utc).isoformat(),
        "bar_status": payload.get("bar_status", "LATEST_RTH_CLOSE"),
        "model_commit": os.environ.get("GITHUB_SHA", payload.get("model_commit", "LOCAL")),
        "input_sha256": _canonical_hash(payload),
        "classification": "AUDITED_PROVISIONAL_RESEARCH_SIGNAL",
        "assets": assets,
        "semiconductor_pair": _pair(assets["SOXX"], assets["SMH"], frames),
    }
    result["material_changes"] = _material_changes(previous, result)
    result["material_change"] = bool(result["material_changes"])

    args.result.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.result.write_text(json.dumps(result, indent=2, ensure_ascii=False, default=str) + "\n")
    args.report.write_text(_markdown(result))
    print(json.dumps({"request_id": result["request_id"], "material_change": result["material_change"], "states": {s: assets[s]["state"] for s in PRIMARY}}, sort_keys=True))


if __name__ == "__main__":
    main()
