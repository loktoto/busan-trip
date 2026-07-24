from __future__ import annotations

import argparse
import json
import tempfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from config import UNIVERSE
from engine import run
from post_validate import apply_guardrails

HKT = ZoneInfo("Asia/Hong_Kong")
ET = ZoneInfo("America/New_York")


def f(v, n=2):
    try:
        return f"{float(v):.{n}f}"
    except (TypeError, ValueError):
        return "N/A"


def default_source_status(reason: str = "No fresh source snapshot") -> dict:
    return {
        "IBKR": {"status": "FAILED", "timestamp": None, "quality": "N/A", "purpose": "Primary equity quote/bar authority", "impact": reason},
        "Alpaca": {"status": "FAILED", "timestamp": None, "quality": "N/A", "purpose": "US-equity parity/fallback", "impact": reason},
        "Binance": {"status": "FAILED", "timestamp": None, "quality": "N/A", "purpose": "Crypto/miner context only", "impact": reason},
        "GitHub": {"status": "SUCCESS", "timestamp": datetime.now(HKT).isoformat(), "quality": "policy/engine only", "purpose": "Model and audit", "impact": "Fresh market calculation unavailable"},
    }


def normalize_source_status(data: dict) -> dict:
    raw = data.get("source_status") or {}
    out = default_source_status("Source not supplied by collector")
    aliases = {"ibkr": "IBKR", "alpaca": "Alpaca", "binance": "Binance", "github": "GitHub"}
    for key, value in raw.items():
        name = aliases.get(str(key).lower(), str(key))
        if name in out and isinstance(value, dict):
            out[name].update(value)
    return out


def normalize_snapshot(snapshot_path: str) -> tuple[str, list[str], dict]:
    data = json.loads(Path(snapshot_path).read_text())
    adjustments: list[str] = []
    for ticker, quote in data.get("quotes", {}).items():
        last = quote.get("price")
        mark = quote.get("mark")
        bid = quote.get("bid")
        ask = quote.get("ask")
        quality = str(quote.get("quality", "")).lower()
        outside_nbbo = False
        try:
            outside_nbbo = last is not None and bid is not None and ask is not None and (float(last) < float(bid) or float(last) > float(ask))
        except (TypeError, ValueError):
            pass
        stale = "stale" in quality or outside_nbbo
        if stale and mark is not None:
            quote["raw_last"] = last
            quote["price"] = mark
            quote["price_source"] = f"{quote.get('source', 'IBKR')} mark (stale/outside-NBBO last)"
            adjustments.append(ticker)
        else:
            quote["price_source"] = quote.get("price_source") or f"{quote.get('source', 'collector')} last"
    data["source_status"] = normalize_source_status(data)
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    with tmp:
        json.dump(data, tmp, ensure_ascii=False, indent=2)
    return tmp.name, adjustments, data["source_status"]


def degraded_result(reason: str, source_status: dict | None = None, snapshot: dict | None = None) -> dict:
    now_hkt = datetime.now(HKT)
    now_et = now_hkt.astimezone(ET)
    snapshot = snapshot or {}
    quotes = snapshot.get("quotes") or {}
    rows = []
    for rank, ticker in enumerate(UNIVERSE, 1):
        q = quotes.get(ticker) or {}
        rows.append({
            "rank": rank,
            "ticker": ticker,
            "score": 0.0,
            "tier": "D",
            "weekly": "DATA GAP",
            "daily": "DATA GAP",
            "hourly": "DATA GAP",
            "state": "NO SETUP",
            "price": q.get("price"),
            "trigger": None,
            "tactical": None,
            "structural": None,
            "tp1": None,
            "tp2": None,
            "rr2_trigger": None,
            "rr2_executable": None,
            "validation": "DATA DEGRADED",
            "action": "No entry — N/A — 未取得可靠資料",
            "errors": [reason],
        })
    return {
        "as_of_hkt": snapshot.get("as_of_hkt", now_hkt.isoformat()),
        "as_of_et": snapshot.get("as_of_et", now_et.isoformat()),
        "session": snapshot.get("session", "UNKNOWN"),
        "source": "MANUAL DEGRADED REPORT",
        "source_status": source_status or default_source_status(reason),
        "bar_limitations": reason,
        "quote_adjustments": [],
        "photonics_1h_up": None,
        "miners_1h_up": None,
        "btc_1h_up": None,
        "soxx_1h_up": None,
        "best_setup_now": None,
        "best_if_triggered": None,
        "raw_7_plus": [],
        "validated_7_plus": [],
        "results": rows,
        "failed_modules": [reason],
    }


def source_table_lines(status: dict) -> list[str]:
    lines = [
        "## Source Status",
        "",
        "|Source|Status|Timestamp / latest bar|Feed / quality|Purpose|Confidence impact|",
        "|---|---|---|---|---|---|",
    ]
    for name in ("IBKR", "Alpaca", "Binance", "GitHub"):
        x = status.get(name, {})
        stamp = x.get("timestamp") or x.get("latest_completed_bar") or "N/A"
        lines.append(f"|{name}|{x.get('status', 'FAILED')}|{stamp}|{x.get('quality', x.get('feed', 'N/A'))}|{x.get('purpose', 'N/A')}|{x.get('impact', 'N/A')}|")
    return lines


def render(result: dict) -> str:
    rows = result["results"]
    last_week = next((x.get("last_completed_week") for x in rows if x.get("last_completed_week")), "N/A")
    degraded = bool(result.get("failed_modules")) or any(x.get("validation") == "DATA DEGRADED" for x in rows)
    headline = "# 🚨 DATA DEGRADED" if degraded else ("# 🚨 NEW ACTION" if result.get("best_setup_now") else "# NO NEW ACTIONABLE TRIGGER THIS HOUR")
    lines = [
        headline,
        "",
        f"- As of: **{result['as_of_hkt']} / {result['as_of_et']}**",
        f"- Session: **{result['session']}**",
        f"- Calculation source: **{result['source']}**",
        f"- Last completed weekly bar: **{last_week}**",
        f"- Live-week / limitation: {result.get('bar_limitations', 'N/A')}",
        f"- Stale-last normalization: **{', '.join(result.get('quote_adjustments', [])) or 'none'}**",
        "",
    ]
    lines += source_table_lines(result.get("source_status", default_source_status()))
    lines += [
        "",
        f"## BEST SETUP NOW: {result.get('best_setup_now') or 'NONE'}",
        f"## BEST SETUP IF TRIGGERED: {result.get('best_if_triggered') or 'NONE'}",
        f"## VALIDATED 7+: {', '.join(result.get('validated_7_plus', [])) or 'NONE'}",
        "",
        "|#|Ticker|Score|Tier|Weekly|Daily|1H|State|Price|Trigger|SL tactical/structural|TP1/TP2|R/R trigger|R/R executable|Validation|Action|",
        "|---:|---|---:|:---:|---|---|---|---|---:|---:|---|---|---:|---:|---|---|",
    ]
    for x in rows:
        lines.append(
            f"|{x.get('rank')}|{x['ticker']}|{float(x.get('score', 0)):.2f}|{x.get('tier', 'D')}|{x.get('weekly', 'N/A')}|{x.get('daily', 'N/A')}|{x.get('hourly', 'N/A')}|"
            f"{x.get('state', 'NO SETUP')}|{f(x.get('price'))}|{f(x.get('trigger'))}|{f(x.get('tactical'))}/{f(x.get('structural'))}|"
            f"{f(x.get('tp1'))}/{f(x.get('tp2'))}|{f(x.get('rr2_trigger', x.get('rr2')))}|{f(x.get('rr2_executable'))}|"
            f"{x.get('validation', 'N/A')}|{x.get('action', 'N/A')}|"
        )
    lines += ["", "## VALIDATED 7+ — PASS 1 / PASS 2", ""]
    if result.get("raw_7_plus"):
        for ticker in result["raw_7_plus"]:
            x = next(r for r in rows if r["ticker"] == ticker)
            lines.append(f"- **{ticker}** — PASS 1 {x['score']:.2f}; {x.get('validation', 'PASS 2 required')}.")
    else:
        lines.append("- None.")
    lines += ["", "## Failed modules / retries", ""]
    failed = result.get("failed_modules") or []
    lines.extend([f"- {item}" for item in failed] or ["- None reported."])
    lines += ["", "## Boss Action", ""]
    if degraded:
        lines.append("資料未完整但報告已照常送出；唔用舊數冒充live，亦唔建立任何未驗證entry。")
    elif result.get("best_setup_now"):
        lines.append(f"只考慮 {result['best_setup_now']} 按既定starter、stop及PASS 2規則；其餘唔追。")
    else:
        lines.append("今個鐘冇validated entry；等completed-bar confirmation、正常spread同至少2R。")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot")
    parser.add_argument("--degraded", action="store_true")
    parser.add_argument("--reason", default="Fresh source snapshot unavailable")
    parser.add_argument("--out", default="ta-monitor/output")
    args = parser.parse_args()

    snapshot_data = None
    source_status = None
    try:
        if args.degraded or not args.snapshot:
            result = degraded_result(args.reason)
        else:
            snapshot_data = json.loads(Path(args.snapshot).read_text())
            normalized_path, adjustments, source_status = normalize_snapshot(args.snapshot)
            result = apply_guardrails(run(normalized_path))
            result["quote_adjustments"] = adjustments
            result["source_status"] = source_status
            result.setdefault("failed_modules", [])
    except Exception as exc:
        result = degraded_result(f"Engine failure after source collection: {type(exc).__name__}: {exc}", source_status, snapshot_data)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "latest.json").write_text(json.dumps(result, indent=2, ensure_ascii=False))
    text = render(result)
    (out / "latest.md").write_text(text)
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
