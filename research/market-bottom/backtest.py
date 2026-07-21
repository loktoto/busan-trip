#!/usr/bin/env python3
"""Causal market-bottom-zone backtest.

Input price CSV columns: Date,Open,High,Low,Close,Volume.
Optional point-in-time feature CSV columns are documented in feature-schema.md.

Design constraints:
- signals use completed close t;
- entries execute at next session open t+1 plus configured costs;
- all drawdown episodes are evaluated, including episodes with no trades;
- future prices are used only by evaluation;
- no ex-post tranche re-normalisation.
"""
from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass, fields
from pathlib import Path

import numpy as np
import pandas as pd

HORIZONS = (42, 63, 84)
PROXIMITY_LEVELS = (3, 5, 8)


@dataclass(frozen=True)
class Config:
    symbol: str
    watch_dd: float = 0.05
    start_dd: float = 0.05
    max_dd: float = 0.50
    max_deploy: float = 0.60
    power: float = 1.80
    micro_probe: float = 0.01
    min_tranche: float = 0.01
    max_tranche: float = 0.08
    cooldown: int = 10
    spacing: float = 0.025
    long_bear_days: int = 60
    long_bear_cap: float = 0.20
    crash_z: float = -2.0
    crash_volume: float = 1.25
    exhaustion_bonus: float = 0.075
    confirmation_bonus: float = 0.125
    exhaustion_votes: int = 2
    confirmation_votes: int = 3
    recovery_dd: float = 0.002
    episode_eval_max_days: int = 252
    transaction_cost_bps: float = 1.0
    slippage_bps: float = 2.0
    credit_veto_z: float = 2.0
    feature_z_window: int = 252
    feature_min_periods: int = 60

    @property
    def all_in_cost_bps(self) -> float:
        return self.transaction_cost_bps + self.slippage_bps


def load_config(path: Path | None, symbol: str) -> Config:
    raw = {} if path is None else json.loads(path.read_text())
    values: dict = {}
    if isinstance(raw, dict):
        if isinstance(raw.get("default"), dict):
            values.update(raw["default"])
        if isinstance(raw.get(symbol), dict):
            values.update(raw[symbol])
        elif "default" not in raw:
            values.update(raw)
    allowed = {f.name for f in fields(Config)} - {"symbol"}
    unknown = set(values) - allowed
    if unknown:
        raise ValueError(f"Unknown config fields: {sorted(unknown)}")
    cfg = Config(symbol=symbol, **values)
    if not (0 < cfg.watch_dd <= cfg.start_dd < cfg.max_dd <= 1):
        raise ValueError("Require 0 < watch_dd <= start_dd < max_dd <= 1")
    if not (0 < cfg.max_deploy <= 1 and 0 <= cfg.long_bear_cap <= cfg.max_deploy):
        raise ValueError("Invalid deployment limits")
    if not (0 <= cfg.micro_probe <= cfg.max_tranche <= cfg.max_deploy):
        raise ValueError("Invalid tranche limits")
    if cfg.cooldown < 0 or cfg.episode_eval_max_days < max(HORIZONS):
        raise ValueError("Invalid time controls")
    return cfg


def load_prices(path: Path) -> pd.DataFrame:
    required = ["Date", "Open", "High", "Low", "Close", "Volume"]
    df = pd.read_csv(path)
    missing = set(required) - set(df.columns)
    if missing:
        raise ValueError(f"Missing price columns: {sorted(missing)}")
    df = df[required].copy()
    df["Date"] = pd.to_datetime(df["Date"], utc=False).dt.tz_localize(None)
    for c in required[1:]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna().sort_values("Date").drop_duplicates("Date").reset_index(drop=True)
    if len(df) < 260:
        raise ValueError("At least 260 daily rows are required")
    if (df[["Open", "High", "Low", "Close"]] <= 0).any().any():
        raise ValueError("Prices must be positive")
    if (df["High"] < df[["Open", "Close", "Low"]].max(axis=1)).any():
        raise ValueError("High is inconsistent with OHLC")
    if (df["Low"] > df[["Open", "Close", "High"]].min(axis=1)).any():
        raise ValueError("Low is inconsistent with OHLC")
    return df


def load_features(path: Path | None) -> pd.DataFrame | None:
    if path is None:
        return None
    f = pd.read_csv(path)
    if "Date" not in f.columns:
        raise ValueError("Feature CSV requires Date")
    f["Date"] = pd.to_datetime(f["Date"], utc=False).dt.tz_localize(None)
    for c in f.columns:
        if c != "Date":
            f[c] = pd.to_numeric(f[c], errors="coerce")
    return f.sort_values("Date").drop_duplicates("Date", keep="last")


def causal_zscore(s: pd.Series, window: int, min_periods: int) -> pd.Series:
    mean = s.rolling(window, min_periods=min_periods).mean()
    std = s.rolling(window, min_periods=min_periods).std(ddof=0)
    return (s - mean) / std.replace(0, np.nan)


def merge_features(x: pd.DataFrame, f: pd.DataFrame | None, cfg: Config) -> pd.DataFrame:
    if f is None:
        return x
    x = x.merge(f, on="Date", how="left")
    numeric = [c for c in f.columns if c != "Date"]
    x[numeric] = x[numeric].ffill()
    for c in numeric:
        x[f"{c}_z"] = causal_zscore(x[c], cfg.feature_z_window, cfg.feature_min_periods)
    return x


def indicators(df: pd.DataFrame, cfg: Config, features: pd.DataFrame | None = None) -> pd.DataFrame:
    x = merge_features(df.copy(), features, cfg)
    c, h, l, v = x.Close, x.High, x.Low, x.Volume
    pc = c.shift(1)

    x["cycle_high"] = c.cummax()
    x["cycle_dd"] = c / x.cycle_high - 1
    x["dd_52w"] = c / c.rolling(252, min_periods=20).max() - 1
    x["r1"] = c.pct_change()
    for n in (3, 5, 10, 20, 63, 126):
        x[f"r{n}"] = c.pct_change(n)

    log_r = np.log(c).diff()
    x["rv20"] = log_r.rolling(20).std(ddof=0) * math.sqrt(252)
    tr = pd.concat([h - l, (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
    x["atr14"] = tr.rolling(14).mean()
    x["atrp"] = x.atr14 / c
    for n in (10, 20, 50, 100, 200):
        x[f"sma{n}"] = c.rolling(n).mean()
    x["sma200_slope"] = x.sma200 / x.sma200.shift(20) - 1
    x["sma10_slope"] = x.sma10 / x.sma10.shift(5) - 1

    x["prior_low10"] = c.shift(1).rolling(10).min()
    x["prior_low20"] = c.shift(1).rolling(20).min()
    x["newlow10"] = c <= x.prior_low10
    x["newlow20"] = c <= x.prior_low20
    x["vol_ratio"] = v / v.rolling(20).mean()
    x["close_loc"] = ((c - l) / (h - l).replace(0, np.nan)).fillna(0.5)
    x["down_volume_ratio"] = v.where(x.r1 < 0, 0) / v.rolling(20).mean()
    x["sell_pressure"] = (-x.r1.clip(upper=0)) * x.vol_ratio * (1 - x.close_loc)
    x["r5z"] = causal_zscore(x.r5, 252, 60)

    underwater: list[int] = []
    n = 0
    for price, peak in zip(c, x.cycle_high):
        n = 0 if price >= peak * (1 - 1e-12) else n + 1
        underwater.append(n)
    x["underwater"] = underwater
    x["long_bear"] = (
        (c < x.sma200)
        & (x.sma200_slope < 0)
        & (x.underwater >= cfg.long_bear_days)
    )

    prior_r5z_min = x.r5z.shift(1).rolling(20).min()
    prior_vol_max = x.vol_ratio.shift(1).rolling(20).max()
    prior_rv_max = x.rv20.shift(1).rolling(20).max()
    prior_sp_max = x.sell_pressure.shift(1).rolling(20).max()
    exhaustion_parts = pd.concat(
        [
            x.r5z > prior_r5z_min,
            x.vol_ratio < prior_vol_max,
            x.rv20 < prior_rv_max,
            x.sell_pressure < prior_sp_max,
            x.close_loc > x.close_loc.shift(5),
        ],
        axis=1,
    ).fillna(False)
    x["exhaustion_score"] = exhaustion_parts.sum(axis=1)

    if "breadth_score_z" in x:
        x["breadth_divergence"] = x.newlow20 & (
            x.breadth_score_z > x.breadth_score_z.shift(1).rolling(20).min()
        )
    else:
        x["breadth_divergence"] = False
    if "downside_vrp_z" in x:
        x["vrp_divergence"] = x.newlow20 & (
            x.downside_vrp_z < x.downside_vrp_z.shift(1).rolling(20).max()
        )
    else:
        x["vrp_divergence"] = False

    x["exhaustion_score"] = x.exhaustion_score + x[["breadth_divergence", "vrp_divergence"]].sum(axis=1)
    x["exhaustion"] = x.newlow20 & (x.exhaustion_score >= cfg.exhaustion_votes)

    breadth = x.get("breadth_score_z", pd.Series(np.nan, index=x.index))
    low5 = l.rolling(5).min()
    confirmation_parts = pd.concat(
        [
            low5 > low5.shift(5),
            c > x.sma10,
            x.sma10_slope > 0,
            x.atrp < x.atrp.shift(5),
            x.r5 > 0,
            breadth > breadth.shift(5),
        ],
        axis=1,
    ).fillna(False)
    x["confirmation_score"] = confirmation_parts.sum(axis=1)
    x["confirmation"] = x.confirmation_score >= cfg.confirmation_votes
    x["crash"] = (x.r5z <= cfg.crash_z) & (x.vol_ratio >= cfg.crash_volume)

    credit_z = None
    if "hy_oas_z" in x:
        credit_z = x.hy_oas_z
    if "ofr_fsi_z" in x:
        credit_z = x.ofr_fsi_z if credit_z is None else pd.concat([credit_z, x.ofr_fsi_z], axis=1).max(axis=1)
    x["credit_veto"] = False if credit_z is None else ((credit_z >= cfg.credit_veto_z) & (credit_z > credit_z.shift(5)))
    return x


def target_deployment(dd: float, cfg: Config) -> float:
    depth = abs(min(dd, 0.0))
    if depth < cfg.start_dd:
        return 0.0
    z = np.clip((depth - cfg.start_dd) / (cfg.max_dd - cfg.start_dd), 0, 1)
    return float(cfg.max_deploy * z**cfg.power)


def episode_ids(x: pd.DataFrame, cfg: Config) -> pd.Series:
    out: list[int] = []
    eid = 0
    active = False
    for dd in x.cycle_dd:
        if not active and dd <= -cfg.watch_dd:
            eid += 1
            active = True
        out.append(eid if active else 0)
        if active and dd >= -cfg.recovery_dd:
            active = False
    return pd.Series(out, index=x.index, dtype=int)


def episode_catalog(x: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    records = []
    for eid, g in x.loc[x.episode > 0].groupby("episode"):
        start_i, end_i = int(g.index.min()), int(g.index.max())
        complete = bool(x.loc[end_i, "cycle_dd"] >= -cfg.recovery_dd)
        trough_i = int(g.Close.idxmin())
        records.append(
            {
                "episode": int(eid),
                "start_index": start_i,
                "end_index": end_i,
                "start_date": x.loc[start_i, "Date"].date(),
                "end_date": x.loc[end_i, "Date"].date(),
                "trough_index": trough_i,
                "trough_date": x.loc[trough_i, "Date"].date(),
                "trough": float(x.loc[trough_i, "Close"]),
                "max_drawdown": float(g.cycle_dd.min()),
                "complete": complete,
            }
        )
    return pd.DataFrame(records)


def run(x: pd.DataFrame, cfg: Config) -> tuple[pd.DataFrame, pd.DataFrame]:
    x = x.copy()
    x["episode"] = episode_ids(x, cfg)
    catalog = episode_catalog(x, cfg)
    rows: list[dict] = []
    deployed: dict[int, float] = {}
    last_i: dict[int, int] = {}
    last_px: dict[int, float] = {}
    last_exhaustion: dict[int, bool] = {}
    last_confirmation: dict[int, bool] = {}

    for i in range(200, len(x) - 1):
        r = x.iloc[i]
        eid = int(r.episode)
        if eid == 0 or r.cycle_dd > -cfg.start_dd or bool(r.credit_veto):
            continue
        used = deployed.get(eid, 0.0)
        want = target_deployment(float(r.cycle_dd), cfg)
        if bool(r.long_bear) and not bool(r.exhaustion) and not bool(r.confirmation):
            want = min(want, cfg.long_bear_cap)

        exhaustion_transition = bool(r.exhaustion) and not last_exhaustion.get(eid, False)
        confirmation_transition = bool(r.confirmation) and not last_confirmation.get(eid, False)
        if exhaustion_transition:
            want = max(want, used + cfg.exhaustion_bonus)
        if confirmation_transition:
            want = max(want, used + cfg.confirmation_bonus)
        want = min(want, cfg.max_deploy)

        fresh = bool(r.newlow10 or r.newlow20)
        crash = bool(r.crash)
        cooldown_ok = eid not in last_i or i - last_i[eid] >= cfg.cooldown
        spacing_ok = eid not in last_px or r.Close <= last_px[eid] * (1 - cfg.spacing)
        event = fresh or crash or exhaustion_transition or confirmation_transition
        eligible = event and (cooldown_ok or spacing_ok or confirmation_transition)

        last_exhaustion[eid] = bool(r.exhaustion)
        last_confirmation[eid] = bool(r.confirmation)
        if not eligible:
            continue
        if used == 0:
            want = max(want, cfg.micro_probe)
        tranche = min(max(0.0, want - used), cfg.max_tranche, cfg.max_deploy - used)
        if tranche < cfg.min_tranche:
            continue

        nxt = x.iloc[i + 1]
        raw_px = float(nxt.Open)
        px = raw_px * (1 + cfg.all_in_cost_bps / 10_000)
        state = 4 if confirmation_transition else 3 if exhaustion_transition else 2
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
            }
        )
    return pd.DataFrame(rows), catalog


def _trade_metrics(x: pd.DataFrame, trades: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        return trades.copy()
    detail = []
    for _, t in trades.iterrows():
        rec = t.to_dict()
        i = int(t.execution_index)
        for h in HORIZONS:
            f = x.iloc[i : min(i + h, len(x) - 1) + 1]
            j_rel = int(f.Close.to_numpy().argmin())
            low = float(f.iloc[j_rel].Close)
            dist = float(t.execution_price / low - 1)
            rec.update(
                {
                    f"trough_{h}": low,
                    f"days_to_trough_{h}": j_rel,
                    f"distance_{h}": dist,
                    f"downside_{h}": low / float(t.execution_price) - 1,
                }
            )
            for p in PROXIMITY_LEVELS:
                rec[f"within_{p}_{h}"] = dist <= p / 100
        detail.append(rec)
    return pd.DataFrame(detail)


def evaluate(
    x: pd.DataFrame, trades: pd.DataFrame, catalog: pd.DataFrame, cfg: Config
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    detail = _trade_metrics(x, trades)
    episodes = []
    for _, e in catalog.iterrows():
        eid = int(e.episode)
        g = detail.loc[detail.episode == eid].sort_values("execution_index") if not detail.empty else pd.DataFrame()
        eval_end = min(int(e.start_index) + cfg.episode_eval_max_days, int(e.end_index), len(x) - 1)
        window = x.iloc[int(e.start_index) : eval_end + 1]
        trough = float(window.Close.min())
        row = e.to_dict()
        row.update(
            {
                "evaluation_end_index": eval_end,
                "evaluation_trough": trough,
                "trade_count": int(len(g)),
                "missed": bool(g.empty),
                "total_deployment": 0.0,
                "weighted_entry": np.nan,
                "weighted_distance": np.nan,
                "worst_additional_downside": np.nan,
            }
        )
        for q in PROXIMITY_LEVELS:
            row[f"any_within_{q}"] = False
            row[f"weighted_within_{q}"] = False
            row[f"capital_within_{q}"] = 0.0
        if not g.empty:
            w = g.tranche.to_numpy(dtype=float)
            p = g.execution_price.to_numpy(dtype=float)
            avg = float(np.average(p, weights=w))
            d = p / trough - 1
            adverse = []
            for _, t in g.iterrows():
                ti = int(t.execution_index)
                post = x.iloc[ti : eval_end + 1]
                adverse.append(float(post.Close.min() / t.execution_price - 1))
            row.update(
                {
                    "total_deployment": float(w.sum()),
                    "weighted_entry": avg,
                    "weighted_distance": avg / trough - 1,
                    "worst_additional_downside": float(min(adverse)),
                }
            )
            for q in PROXIMITY_LEVELS:
                row[f"any_within_{q}"] = bool((d <= q / 100).any())
                row[f"weighted_within_{q}"] = bool(avg / trough - 1 <= q / 100)
                row[f"capital_within_{q}"] = float(w[d <= q / 100].sum())
        episodes.append(row)

    ep = pd.DataFrame(episodes)
    if ep.empty:
        summary = {
            "classification": "RESEARCH CANDIDATE — NOT GUARANTEED OR OPTIMAL",
            "trade_count": int(len(detail)),
            "episode_count_all": 0,
            "episode_count_complete": 0,
            "missed_rate_complete": np.nan,
            "mean_deployment_complete": np.nan,
            "mean_weighted_distance_complete": np.nan,
            "mean_worst_additional_downside_complete": np.nan,
        }
        for q in PROXIMITY_LEVELS:
            summary[f"any_within_{q}_rate_complete"] = np.nan
            summary[f"weighted_within_{q}_rate_traded_complete"] = np.nan
            summary[f"mean_capital_within_{q}_complete"] = np.nan
        return detail, ep, summary

    eligible = ep.loc[ep.complete].copy()
    summary: dict = {
        "classification": "RESEARCH CANDIDATE — NOT GUARANTEED OR OPTIMAL",
        "trade_count": int(len(detail)),
        "episode_count_all": int(len(ep)),
        "episode_count_complete": int(len(eligible)),
        "missed_rate_complete": float(eligible.missed.mean()) if len(eligible) else np.nan,
        "mean_deployment_complete": float(eligible.total_deployment.mean()) if len(eligible) else np.nan,
        "mean_weighted_distance_complete": float(eligible.weighted_distance.dropna().mean()) if len(eligible) else np.nan,
        "mean_worst_additional_downside_complete": float(eligible.worst_additional_downside.dropna().mean()) if len(eligible) else np.nan,
    }
    for q in PROXIMITY_LEVELS:
        summary[f"any_within_{q}_rate_complete"] = float(eligible[f"any_within_{q}"].mean()) if len(eligible) else np.nan
        denom = eligible.loc[~eligible.missed]
        summary[f"weighted_within_{q}_rate_traded_complete"] = float(denom[f"weighted_within_{q}"].mean()) if len(denom) else np.nan
        summary[f"mean_capital_within_{q}_complete"] = float(eligible[f"capital_within_{q}"].mean()) if len(eligible) else np.nan
    return detail, ep, summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", type=Path, required=True)
    ap.add_argument("--symbol", required=True)
    ap.add_argument("--config", type=Path)
    ap.add_argument("--features-csv", type=Path)
    ap.add_argument("--out", type=Path, default=Path("backtest-output"))
    a = ap.parse_args()

    cfg = load_config(a.config, a.symbol)
    x = indicators(load_prices(a.csv), cfg, load_features(a.features_csv))
    trades, catalog = run(x, cfg)
    detail, episodes, summary = evaluate(x, trades, catalog, cfg)

    out = a.out / a.symbol
    out.mkdir(parents=True, exist_ok=True)
    x.to_csv(out / "indicators.csv", index=False)
    trades.to_csv(out / "trades.csv", index=False)
    catalog.to_csv(out / "episode_catalog.csv", index=False)
    detail.to_csv(out / "trade_metrics.csv", index=False)
    episodes.to_csv(out / "episode_metrics.csv", index=False)
    summary.update(
        {
            "symbol": a.symbol,
            "config": asdict(cfg),
            "signal_time": "completed close t",
            "execution_time": "next open t+1 plus configured costs",
        }
    )
    (out / "summary.json").write_text(json.dumps(summary, indent=2, default=str))
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
