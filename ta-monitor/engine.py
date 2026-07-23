from __future__ import annotations

import json
import math
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import quote
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import requests

from config import BASELINES, EVENTS, MEMORY, MINERS, PHOTONICS, UNIVERSE

ET = ZoneInfo("America/New_York")
HEADERS = {"User-Agent": "Mozilla/5.0 TA-monitor/1.0"}


def num(v: Any) -> float | None:
    try:
        x = float(v)
        return x if math.isfinite(x) else None
    except (TypeError, ValueError):
        return None


def fetch(symbol: str, interval: str, range_: str, prepost: bool) -> pd.DataFrame:
    url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/{quote(symbol)}"
        f"?range={range_}&interval={interval}&includePrePost={'true' if prepost else 'false'}"
        "&events=div%2Csplits"
    )
    err = None
    for n in range(4):
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
            r.raise_for_status()
            result = r.json()["chart"]["result"][0]
            ts = result.get("timestamp") or []
            q = (result.get("indicators", {}).get("quote") or [{}])[0]
            if not ts:
                return pd.DataFrame()
            df = pd.DataFrame(
                {
                    "Open": q.get("open", [None] * len(ts)),
                    "High": q.get("high", [None] * len(ts)),
                    "Low": q.get("low", [None] * len(ts)),
                    "Close": q.get("close", [None] * len(ts)),
                    "Volume": q.get("volume", [None] * len(ts)),
                },
                index=pd.to_datetime(ts, unit="s", utc=True).tz_convert(ET),
            )
            return (
                df.apply(pd.to_numeric, errors="coerce")
                .dropna(subset=["Open", "High", "Low", "Close"])
                .loc[lambda x: ~x.index.duplicated(keep="last")]
                .sort_index()
            )
        except Exception as exc:
            err = exc
            time.sleep(2**n)
    raise RuntimeError(f"{symbol} {interval}: {err}")


def rsi(s: pd.Series, n: int = 14) -> pd.Series:
    d = s.diff()
    g = d.clip(lower=0).ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    l = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    return (100 - 100 / (1 + g / l.replace(0, np.nan))).fillna(100).clip(0, 100)


def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    p = df.Close.shift(1)
    tr = pd.concat([(df.High - df.Low), (df.High - p).abs(), (df.Low - p).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / n, adjust=False, min_periods=n).mean()


def enrich(df: pd.DataFrame, weekly: bool = False) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    for n in ([5, 10, 20, 40] if weekly else [5, 10, 20, 50]):
        out[f"SMA{n}"] = out.Close.rolling(n).mean()
    out["EMA20"] = out.Close.ewm(span=20, adjust=False).mean()
    out["EMA50"] = out.Close.ewm(span=50, adjust=False).mean()
    out["RSI14"] = rsi(out.Close)
    out["ATR14"] = atr(out)
    out["ATR_pct"] = out.ATR14 / out.Close * 100
    return out


def structure(df: pd.DataFrame, n: int = 5) -> str:
    if len(df) < n * 2:
        return "INSUFFICIENT"
    a, b = df.iloc[-2 * n : -n], df.iloc[-n:]
    if b.High.max() > a.High.max() and b.Low.min() > a.Low.min():
        return "HH/HL"
    if b.High.max() < a.High.max() and b.Low.min() < a.Low.min():
        return "LH/LL"
    return "MIXED"


def trend(df: pd.DataFrame, tf: str) -> tuple[str, float]:
    if df.empty or len(df) < 20:
        return "DATA GAP", 0.0
    x, s = df.iloc[-1], structure(df)
    if tf == "weekly":
        fast, slow = x.SMA10, x.SMA20
    elif tf == "daily":
        fast, slow = x.SMA20, x.SMA50
    else:
        fast, slow = x.EMA20, x.EMA50
    if x.Close > fast > slow and s == "HH/HL":
        return "UP", 1.0
    if x.Close > fast and s != "LH/LL":
        return "RECOVERY", 0.7
    if x.Close < fast < slow and s == "LH/LL":
        return "DOWN", 0.0
    return ("BEARISH/MIXED", 0.25) if s == "LH/LL" else ("MIXED", 0.5)


def complete_daily(df: pd.DataFrame, now: datetime) -> pd.DataFrame:
    return df[df.index.date < now.date()]


def complete_intraday(df: pd.DataFrame, now: datetime, mins: int) -> pd.DataFrame:
    return df[df.index <= pd.Timestamp(now) - pd.Timedelta(minutes=mins)]


def weekly(daily: pd.DataFrame, now: datetime) -> pd.DataFrame:
    w = daily.resample("W-FRI").agg({"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}).dropna()
    friday = (now + timedelta(days=(4 - now.weekday()) % 7)).date()
    return w[w.index.date < friday]


def vwap(df: pd.DataFrame) -> float | None:
    if df.empty:
        return None
    day = df[df.index.date == df.index[-1].date()]
    vol = day.Volume.fillna(0)
    return None if vol.sum() <= 0 else float((((day.High + day.Low + day.Close) / 3) * vol).sum() / vol.sum())


def higher_low(df: pd.DataFrame) -> bool:
    return len(df) >= 6 and df.Low.tail(3).min() > df.Low.tail(6).head(3).min()


def levels(t: str, d: pd.DataFrame, h: pd.DataFrame) -> dict[str, Any]:
    if t in BASELINES:
        return dict(BASELINES[t])
    x = d.iloc[-1]
    a = float(x.ATR14) if pd.notna(x.ATR14) else float(x.Close) * 0.06
    res = max(float(d.High.tail(10).max()), float(h.High.tail(20).max()))
    sup = float(d.Low.tail(10).min())
    mid = min(float(x.Close), float(x.EMA20))
    return {
        "pullback": [max(0.01, mid - 0.2 * a), mid + 0.1 * a],
        "tactical": max(sup, mid - 0.6 * a),
        "structural": max(0.01, min(sup, mid - a)),
        "trigger": res,
        "tp": [res + 0.75 * a, res + 1.5 * a, res + 2.25 * a],
    }


def sessions_to(date: str, now: datetime) -> int:
    return int(np.busday_count(now.date(), pd.Timestamp(date).date()))


def run(snapshot_path: str) -> dict[str, Any]:
    snap = json.loads(Path(snapshot_path).read_text())
    now_hkt = datetime.fromisoformat(snap["as_of_hkt"])
    now = now_hkt.astimezone(ET)
    quotes = snap["quotes"]
    frames: dict[str, dict[str, pd.DataFrame]] = {}
    errors: dict[str, list[str]] = {}

    for t in UNIVERSE + ["SOXX", "BTC-USD"]:
        errors[t] = []
        try:
            d = enrich(complete_daily(fetch(t, "1d", "1y", False), now))
            h = enrich(complete_intraday(fetch(t, "1h", "3mo", True), now, 60))
            m = enrich(complete_intraday(fetch(t, "15m", "5d", True), now, 15))
            w = enrich(weekly(d[["Open", "High", "Low", "Close", "Volume"]], now), True)
            frames[t] = {"d": d, "h": h, "m": m, "w": w}
        except Exception as exc:
            errors[t].append(str(exc))
            frames[t] = {k: pd.DataFrame() for k in ("d", "h", "m", "w")}

    hup = {}
    for t, f in frames.items():
        h = f["h"]
        hup[t] = bool(not h.empty and len(h) >= 20 and h.iloc[-1].Close > h.iloc[-1].EMA20 and structure(h) != "LH/LL")
    pcount = sum(hup.get(t, False) for t in PHOTONICS)
    mcount = sum(hup.get(t, False) for t in MINERS)
    btc, soxx = hup.get("BTC-USD", False), hup.get("SOXX", False)

    out = []
    for t in UNIVERSE:
        q, f = quotes[t], frames[t]
        d, h, m, w = f["d"], f["h"], f["m"], f["w"]
        if any(x.empty for x in (d, h, m, w)):
            out.append({"ticker": t, "score": 0.0, "tier": "D", "weekly": "DATA GAP", "daily": "DATA GAP", "hourly": "DATA GAP", "state": "NO SETUP", "price": q.get("price"), "validation": "DATA DEGRADED", "action": "No entry; missing OHLCV", "errors": errors[t]})
            continue
        wt, ws = trend(w, "weekly")
        dt, ds = trend(d, "daily")
        ht, hs = trend(h, "hourly")
        lv = levels(t, d, h)
        price = float(q["price"])
        bid, ask = num(q.get("bid")), num(q.get("ask"))
        spread = ((ask - bid) / ((ask + bid) / 2) * 100) if bid and ask and ask > bid else None
        trig = float(lv["trigger"])
        trig15 = float(lv.get("trigger15", trig))
        tac, struct = float(lv["tactical"]), float(lv["structural"])
        tp1, tp2, tp3 = map(float, lv["tp"])
        pl, ph = map(float, lv["pullback"])
        c15, c1h = float(m.iloc[-1].Close), float(h.iloc[-1].Close)
        ok15, ok1h = c15 > trig15, c1h > trig
        pv, hl = vwap(m), higher_low(m)
        pull = pl <= price <= ph and hl and (pv is None or c15 >= pv)
        rr = (tp2 - trig) / max(0.01, trig - tac) if tp2 > trig > tac else 0.0
        ad = float(d.iloc[-1].ATR14) if pd.notna(d.iloc[-1].ATR14) else price * 0.06
        aw = float(w.iloc[-1].ATR14) if pd.notna(w.iloc[-1].ATR14) else price * 0.12
        live_w = (price - float(w.iloc[-1].Close)) / max(aw, 0.01)
        below = price < w.iloc[-1].SMA10 and price < w.iloc[-1].SMA20

        tc = 1.0 if ok15 and ok1h else 0.65 if price > trig else 0.5 if abs(price / trig - 1) <= 0.01 else 0.35 if abs(price / trig - 1) <= 0.03 else 0.8 if pull else 0.15
        if pl <= price <= ph:
            loc = 1.0
        elif price <= trig:
            z = (trig - price) / max(ad, 0.01)
            loc = 0.85 if z <= 0.5 else 0.55 if z <= 1 else 0.3
        else:
            z = (price - trig) / max(ad, 0.01)
            loc = 0.8 if z <= 0.25 else 0.5 if z <= 0.5 else 0.2
        rrq = min(max(rr / 2, 0), 1)
        liq = 0.2 if spread is None else 1.0 if spread <= 0.1 else 0.8 if spread <= 0.25 else 0.6 if spread <= 0.5 else 0.3 if spread <= 1 else 0.1
        if q.get("quality") != "live":
            liq = min(liq, 0.2)
        event = EVENTS.get(t)
        ses = sessions_to(event["date"], now) if event else None
        eq = 0.0 if ses == 0 else 0.2 if ses is not None and 0 < ses <= 5 else 1.0
        iv = num(q.get("iv52"))
        iq = 1.0 if iv is None else 0.2 if iv >= 0.97 else 0.5 if iv >= 0.9 else 0.7 if iv >= 0.8 else 1.0
        score = 10 * (0.1 * ws + 0.1 * ds + 0.05 * hs + 0.2 * tc + 0.2 * rrq + 0.15 * loc + 0.1 * liq + 0.1 * min(eq, iq))
        penalties = []
        if (ws <= 0.25 < ds) or (ds <= 0.25 < ws):
            score -= 0.5; penalties.append("weekly/daily conflict")
        if abs(live_w) > 0.5:
            score -= 0.5; penalties.append(">0.5 weekly ATR")
        if price > trig and not ok1h:
            score -= 0.4; penalties.append("incomplete breakout")
        if spread is not None and spread > 1:
            score -= 0.7; penalties.append("abnormal spread")
        if t in PHOTONICS and pcount < 3:
            score -= 0.4; penalties.append(f"photonics {pcount}/7")
        if t in MINERS and (not btc or mcount < 2):
            score -= 0.4; penalties.append(f"miners {mcount}/4 BTC={btc}")
        if t in MEMORY and not (hup.get("MU") and hup.get("SNDK") and soxx):
            score -= 0.4; penalties.append("memory/SOXX weak")
        if ses == 0:
            score = min(score, 4.9); penalties.append("same-day earnings block")
        score = round(max(0, min(10, score)), 2)

        normal = ws >= 0.5 and ds >= 0.5
        opposing = below or ws <= 0.25
        counter = opposing and ds >= 0.5
        if ses == 0:
            state, action = "NO SETUP", "Event block; no normal entry"
        elif price >= tp3:
            state, action = "POST-TP EXTENDED", "Do not chase; wait for new base"
        elif pull:
            state, action = ("RE-ENTRY PULLBACK READY" if counter else "PULLBACK READY"), "Starter only after RTH confirmation"
        elif ok15 and ok1h and rr >= 2 and normal and not (opposing and below):
            state, action = "BREAKOUT STARTER", "25–40% starter; portfolio risk 0.25–0.40%"
        elif ok15 and ok1h and counter:
            state, action = "RE-ENTRY CONFIRMED", "Counter-trend starter 10–20% only"
        elif price > trig or abs(price / trig - 1) <= 0.02:
            state, action = ("RE-ENTRY BREAKOUT PENDING" if counter else "BREAKOUT PENDING"), "Wait completed 1H and retest"
        elif counter:
            state, action = "RE-ENTRY WATCH", "No entry; weekly opposes"
        elif ws <= 0.25 and ds <= 0.25:
            state, action = "NO SETUP", "Stand aside"
        else:
            state, action = "WATCH", "Trigger not developed"

        tier = "A" if score >= 7.5 else "B" if score >= 6.5 else "C" if score >= 5.5 else "D"
        validation = "UNVALIDATED — FRESH IBKR PASS 2 REQUIRED" if score >= 7 else "PASS 1"
        out.append({
            "ticker": t, "score": score, "tier": tier, "weekly": wt, "daily": dt, "hourly": ht,
            "weekly_structure": structure(w), "daily_structure": structure(d), "hourly_structure": structure(h),
            "state": state, "price": price, "bid": bid, "ask": ask, "spread_pct": spread,
            "trigger": trig, "trigger15": trig15, "pullback_low": pl, "pullback_high": ph,
            "tactical": tac, "structural": struct, "tp1": tp1, "tp2": tp2, "tp3": tp3, "rr2": rr,
            "last15_close": c15, "last1h_close": c1h, "vwap": pv, "confirm15": ok15, "confirm1h": ok1h,
            "last_completed_week": str(w.index[-1].date()), "last_week_close": float(w.iloc[-1].Close),
            "sma10w": num(w.iloc[-1].SMA10), "sma20w": num(w.iloc[-1].SMA20),
            "weekly_rsi": num(w.iloc[-1].RSI14), "weekly_atr_pct": num(w.iloc[-1].ATR_pct),
            "daily_rsi": num(d.iloc[-1].RSI14), "daily_atr_pct": num(d.iloc[-1].ATR_pct),
            "live_week_atr": live_w, "counter_trend": counter, "validation": validation,
            "technical_confidence": round(score * 10), "event_adjusted_confidence": round(score * 10 * eq),
            "event": event, "sessions_to_event": ses, "penalties": penalties, "action": action,
            "quote_quality": q.get("quality"),
        })

    out.sort(key=lambda x: x["score"], reverse=True)
    for i, x in enumerate(out, 1):
        x["rank"] = i
    actionable = {"BREAKOUT STARTER", "PULLBACK READY", "RE-ENTRY CONFIRMED", "RE-ENTRY PULLBACK READY"}
    pending = {"BREAKOUT PENDING", "RE-ENTRY BREAKOUT PENDING", "WATCH", "RE-ENTRY WATCH"}
    return {
        "as_of_hkt": snap["as_of_hkt"], "as_of_et": snap["as_of_et"], "session": snap["session"],
        "source": "IBKR snapshot + Yahoo OHLCV fallback",
        "bar_limitations": "Public extended-hours bars do not cover the full 20:00–04:00 ET overnight session.",
        "photonics_1h_up": pcount, "miners_1h_up": mcount, "btc_1h_up": btc, "soxx_1h_up": soxx,
        "best_setup_now": next((x["ticker"] for x in out if x["state"] in actionable), None),
        "best_if_triggered": next((x["ticker"] for x in out if x["state"] in pending), None),
        "raw_7_plus": [x["ticker"] for x in out if x["score"] >= 7], "validated_7_plus": [],
        "results": out,
    }
