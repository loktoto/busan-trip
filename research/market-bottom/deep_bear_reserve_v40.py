#!/usr/bin/env python3
"""Causal deep-bear capital-reservation overlay.

The baseline engine is useful for staged participation in ordinary corrections,
but its largest historical errors occur when a correction develops into a
structural bear market.  This module does not claim to predict the final low.
Instead, it tests whether simple completed-bar indicators can preserve capital
while price is still accelerating lower, then release only a bounded amount near
a mature/deep bottom zone.

All signals use completed close ``t`` and execute at next open ``t+1`` plus the
same costs as the baseline engine.  Future troughs are used by evaluation only.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from backtest import (
    Config,
    episode_catalog,
    episode_ids,
    evaluate,
    indicators,
    load_config,
    load_prices,
    target_deployment,
)


@dataclass(frozen=True)
class ReservePolicy:
    """Small, pre-declared policy surface for robustness testing."""

    name: str = "RESERVE_10"
    enabled: bool = True
    structural_votes: int = 3
    structural_min_underwater: int = 20
    falling_knife_votes: int = 3
    reserve_cap: float = 0.10
    deep_fraction: float = 0.40
    deep_cap: float = 0.25
    maturity_votes: int = 5
    maturity_cap: float = 0.20
    combined_cap: float = 0.35
    maturity_min_age: int = 2
    maturity_max_age: int = 20
    maturity_atr_multiple: float = 3.0

    def validate(self, cfg: Config) -> None:
        if self.structural_votes not in range(1, 6):
            raise ValueError("structural_votes must be between 1 and 5")
        if self.falling_knife_votes not in range(1, 6):
            raise ValueError("falling_knife_votes must be between 1 and 5")
        if self.maturity_votes not in range(1, 8):
            raise ValueError("maturity_votes must be between 1 and 7")
        if not 0 <= self.deep_fraction <= 1:
            raise ValueError("deep_fraction must be in [0, 1]")
        caps = (
            self.reserve_cap,
            self.deep_cap,
            self.maturity_cap,
            self.combined_cap,
        )
        if any(c < 0 or c > cfg.max_deploy for c in caps):
            raise ValueError("reserve caps must be within the deployment limit")
        if self.deep_cap < self.reserve_cap:
            raise ValueError("deep_cap cannot be below reserve_cap")
        if self.maturity_cap < self.reserve_cap:
            raise ValueError("maturity_cap cannot be below reserve_cap")
        if self.combined_cap < max(self.deep_cap, self.maturity_cap):
            raise ValueError("combined_cap must be the largest reserve cap")
        if not 0 <= self.maturity_min_age <= self.maturity_max_age:
            raise ValueError("invalid maturity age window")


def add_reserve_features(
    frame: pd.DataFrame, cfg: Config, policy: ReservePolicy
) -> pd.DataFrame:
    """Add completed-bar structural-risk and bottom-maturity indicators."""
    policy.validate(cfg)
    x = frame.copy()

    structural_parts = pd.concat(
        [
            x.Close < x.sma200,
            x.sma200_slope < 0,
            x.sma50 < x.sma200,
            x.r63 < 0,
            x.underwater >= policy.structural_min_underwater,
        ],
        axis=1,
    ).fillna(False)
    x["reserve_structural_votes"] = structural_parts.sum(axis=1)
    x["reserve_structural_risk"] = (
        x.reserve_structural_votes >= policy.structural_votes
    )

    sell_q75 = x.sell_pressure.shift(1).rolling(63, min_periods=20).quantile(0.75)
    falling_parts = pd.concat(
        [
            x.r5z <= -0.5,
            x.rv20 > x.rv20.shift(5),
            x.sell_pressure >= sell_q75,
            x.close_loc <= 0.35,
            x.sma10_slope < 0,
        ],
        axis=1,
    ).fillna(False)
    x["reserve_falling_knife_votes"] = falling_parts.sum(axis=1)
    x["reserve_falling_knife"] = (
        x.reserve_falling_knife_votes >= policy.falling_knife_votes
    )

    latest_new_low_index: int | None = None
    ages: list[float] = []
    for i, flag in enumerate(x.newlow20.fillna(False).astype(bool)):
        if flag:
            latest_new_low_index = i
        ages.append(
            np.nan if latest_new_low_index is None else i - latest_new_low_index
        )
    x["reserve_sessions_since_low"] = ages

    low5 = x.Low.rolling(5).min()
    prior_low5 = x.Low.shift(5).rolling(5).min()
    sell_now = x.sell_pressure.rolling(3).mean()
    sell_prior = x.sell_pressure.shift(3).rolling(10).mean()
    close_now = x.close_loc.rolling(3).mean()
    close_prior = x.close_loc.shift(3).rolling(10).mean()
    maturity_parts = pd.concat(
        [
            x.r5 > 0,
            x.Close > x.sma10,
            x.sma10_slope > 0,
            x.rv20 <= x.rv20.shift(5),
            sell_now < sell_prior,
            close_now > close_prior,
            low5 > prior_low5,
        ],
        axis=1,
    ).fillna(False)
    x["reserve_maturity_votes"] = maturity_parts.sum(axis=1)

    rolling_low20 = x.Low.rolling(20).min()
    distance_from_low = (x.Close - rolling_low20) / x.atr14.replace(0, np.nan)
    x["reserve_atr_from_low"] = distance_from_low
    age_ok = x.reserve_sessions_since_low.between(
        policy.maturity_min_age, policy.maturity_max_age
    )
    price_near_low = distance_from_low <= policy.maturity_atr_multiple
    x["reserve_maturity"] = (
        age_ok
        & price_near_low
        & (x.reserve_maturity_votes >= policy.maturity_votes)
        & (~x.newlow20.astype(bool))
    ).fillna(False)

    deep_threshold = cfg.start_dd + policy.deep_fraction * (
        cfg.max_dd - cfg.start_dd
    )
    x["reserve_deep_threshold"] = deep_threshold
    x["reserve_deep_zone"] = x.cycle_dd <= -deep_threshold
    x["reserve_risk"] = (
        x.reserve_structural_risk | x.reserve_falling_knife
    ).fillna(False)
    return x


def reserve_cap_for_row(
    row: pd.Series,
    cfg: Config,
    policy: ReservePolicy,
    active_risk: bool | None = None,
) -> tuple[float, str]:
    """Return the maximum cumulative deployment authorised at this close."""
    risk = bool(row.reserve_risk) if active_risk is None else bool(active_risk)
    if not policy.enabled or not risk:
        return cfg.max_deploy, "NO_RESERVE_CAP"
    deep = bool(row.reserve_deep_zone)
    mature = bool(row.reserve_maturity)
    if deep and mature:
        return policy.combined_cap, "DEEP_AND_MATURE"
    if deep:
        return policy.deep_cap, "DEEP_ZONE"
    if mature:
        return policy.maturity_cap, "MATURE_RETEST"
    return policy.reserve_cap, "EARLY_STRUCTURAL_RISK"


def run_reserve(
    x: pd.DataFrame, cfg: Config, policy: ReservePolicy
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run the baseline events through the causal reserve state machine."""
    y = add_reserve_features(x, cfg, policy)
    y["episode"] = episode_ids(y, cfg)
    catalog = episode_catalog(y, cfg)
    rows: list[dict[str, Any]] = []
    deployed: dict[int, float] = {}
    last_i: dict[int, int] = {}
    last_px: dict[int, float] = {}
    last_exhaustion: dict[int, bool] = {}
    last_confirmation: dict[int, bool] = {}
    last_maturity: dict[int, bool] = {}
    structural_risk_latched: set[int] = set()

    for i in range(200, len(y) - 1):
        r = y.iloc[i]
        eid = int(r.episode)
        if (
            eid == 0
            or float(r.cycle_dd) > -cfg.start_dd
            or bool(r.credit_veto)
        ):
            continue

        used = deployed.get(eid, 0.0)
        if bool(r.reserve_structural_risk):
            structural_risk_latched.add(eid)
        active_reserve_risk = (
            eid in structural_risk_latched or bool(r.reserve_falling_knife)
        )
        want = target_deployment(float(r.cycle_dd), cfg)
        if bool(r.long_bear) and not bool(r.exhaustion) and not bool(r.confirmation):
            want = min(want, cfg.long_bear_cap)

        exhaustion_transition = bool(r.exhaustion) and not last_exhaustion.get(
            eid, False
        )
        confirmation_transition = bool(r.confirmation) and not last_confirmation.get(
            eid, False
        )
        maturity_transition = bool(r.reserve_maturity) and not last_maturity.get(
            eid, False
        )
        maturity_transition = bool(policy.enabled and maturity_transition)
        if exhaustion_transition:
            want = max(want, used + cfg.exhaustion_bonus)
        if confirmation_transition:
            want = max(want, used + cfg.confirmation_bonus)

        reserve_cap, reserve_reason = reserve_cap_for_row(
            r, cfg, policy, active_reserve_risk
        )
        want = min(want, reserve_cap, cfg.max_deploy)
        # A cap can freeze new deployment but must never imply selling capital
        # that the same episode has already deployed.
        want = max(want, used)

        fresh = bool(r.newlow10 or r.newlow20)
        crash = bool(r.crash)
        cooldown_ok = eid not in last_i or i - last_i[eid] >= cfg.cooldown
        spacing_ok = (
            eid not in last_px
            or float(r.Close) <= last_px[eid] * (1 - cfg.spacing)
        )
        event = (
            fresh
            or crash
            or exhaustion_transition
            or confirmation_transition
            or maturity_transition
        )
        eligible = event and (
            cooldown_ok
            or spacing_ok
            or confirmation_transition
            or maturity_transition
        )

        last_exhaustion[eid] = bool(r.exhaustion)
        last_confirmation[eid] = bool(r.confirmation)
        last_maturity[eid] = bool(r.reserve_maturity)
        if not eligible:
            continue
        if used == 0:
            want = max(want, min(cfg.micro_probe, reserve_cap))
        tranche = min(
            max(0.0, want - used),
            cfg.max_tranche,
            cfg.max_deploy - used,
        )
        if tranche < cfg.min_tranche:
            continue

        nxt = y.iloc[i + 1]
        raw_px = float(nxt.Open)
        px = raw_px * (1 + cfg.all_in_cost_bps / 10_000)
        if maturity_transition:
            state, reason = 4, "RESERVE_MATURITY_RELEASE"
        elif confirmation_transition:
            state, reason = 4, "CONFIRMATION"
        elif exhaustion_transition:
            state, reason = 3, "EXHAUSTION"
        else:
            state, reason = 2, "LEFT_SIDE_EVENT"

        used += tranche
        deployed[eid] = used
        last_i[eid] = i + 1
        last_px[eid] = px
        rows.append(
            {
                "symbol": cfg.symbol,
                "episode": eid,
                "signal_index": i,
                "execution_index": i + 1,
                "signal_date": r.Date.date(),
                "execution_date": nxt.Date.date(),
                "raw_open": raw_px,
                "execution_price": px,
                "cost_bps": cfg.all_in_cost_bps,
                "tranche": tranche,
                "cumulative": used,
                "state": state,
                "reason": reason,
                "cycle_dd": float(r.cycle_dd),
                "dd_52w": float(r.dd_52w),
                "atrp": float(r.atrp),
                "rv20": float(r.rv20),
                "volume_ratio": float(r.vol_ratio),
                "underwater": int(r.underwater),
                "long_bear": bool(r.long_bear),
                "fresh_low": fresh,
                "crash": crash,
                "exhaustion_transition": exhaustion_transition,
                "confirmation_transition": confirmation_transition,
                "reserve_maturity_transition": maturity_transition,
                "reserve_structural_votes": int(r.reserve_structural_votes),
                "reserve_falling_knife_votes": int(
                    r.reserve_falling_knife_votes
                ),
                "reserve_maturity_votes": int(r.reserve_maturity_votes),
                "reserve_sessions_since_low": (
                    None
                    if pd.isna(r.reserve_sessions_since_low)
                    else int(r.reserve_sessions_since_low)
                ),
                "reserve_atr_from_low": float(r.reserve_atr_from_low),
                "reserve_deep_zone": bool(r.reserve_deep_zone),
                "reserve_risk": active_reserve_risk,
                "reserve_structural_risk_latched": (
                    eid in structural_risk_latched
                ),
                "reserve_cap": float(reserve_cap),
                "reserve_reason": reserve_reason,
                "policy": policy.name,
            }
        )
    return pd.DataFrame(rows), catalog


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", type=Path, required=True)
    ap.add_argument("--symbol", required=True)
    ap.add_argument("--config", type=Path, required=True)
    ap.add_argument("--policy-json", type=Path)
    ap.add_argument("--out", type=Path, default=Path("reserve-v40-output"))
    a = ap.parse_args()

    cfg = load_config(a.config, a.symbol)
    raw_policy = (
        {} if a.policy_json is None else json.loads(a.policy_json.read_text())
    )
    policy = ReservePolicy(**raw_policy)
    x = indicators(load_prices(a.csv), cfg)
    trades, catalog = run_reserve(x, cfg, policy)
    detail, episodes, summary = evaluate(x, trades, catalog, cfg)
    summary.update(
        {
            "symbol": a.symbol,
            "policy": asdict(policy),
            "config": asdict(cfg),
            "classification": (
                "DEEP-BEAR RESERVE RESEARCH — NO ORDER OR LEVERAGE AUTHORITY"
            ),
            "signal_time": "completed close t",
            "execution_time": "next open t+1 plus configured costs",
        }
    )

    out = a.out / a.symbol
    out.mkdir(parents=True, exist_ok=True)
    trades.to_csv(out / "trades.csv", index=False)
    detail.to_csv(out / "trade_metrics.csv", index=False)
    episodes.to_csv(out / "episode_metrics.csv", index=False)
    (out / "summary.json").write_text(json.dumps(summary, indent=2, default=str))
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
