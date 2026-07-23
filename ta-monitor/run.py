from __future__ import annotations

import argparse
import json
from pathlib import Path

from engine import run


def f(v, n=2):
    try:
        return f"{float(v):.{n}f}"
    except (TypeError, ValueError):
        return "N/A"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--snapshot", required=True)
    p.add_argument("--out", default="ta-monitor/output")
    a = p.parse_args()
    result = run(a.snapshot)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "latest.json").write_text(json.dumps(result, indent=2, ensure_ascii=False))

    rows = result["results"]
    last_week = next((x.get("last_completed_week") for x in rows if x.get("last_completed_week")), "N/A")
    lines = [
        "# Fresh Multi-Timeframe TA Monitor",
        "",
        f"- As of: **{result['as_of_hkt']} / {result['as_of_et']}**",
        f"- Session: **{result['session']}**",
        f"- Source: **{result['source']}**",
        f"- Last completed weekly bar: **{last_week}**",
        f"- Limitation: {result['bar_limitations']}",
        "",
        f"## BEST SETUP NOW: {result['best_setup_now'] or 'NONE'}",
        f"## BEST SETUP IF TRIGGERED: {result['best_if_triggered'] or 'NONE'}",
        f"## VALIDATED 7+: {', '.join(result['validated_7_plus']) or 'NONE'}",
        "",
        "|#|Ticker|Score|Tier|Weekly|Daily|1H|State|Price|Trigger|SL tactical/structural|TP1/TP2|R/R2|Validation|Action|",
        "|---:|---|---:|:---:|---|---|---|---|---:|---:|---|---|---:|---|---|",
    ]
    for x in rows:
        lines.append(
            f"|{x['rank']}|{x['ticker']}|{x['score']:.2f}|{x['tier']}|{x['weekly']}|{x['daily']}|{x['hourly']}|"
            f"{x['state']}|{f(x.get('price'))}|{f(x.get('trigger'))}|{f(x.get('tactical'))}/{f(x.get('structural'))}|"
            f"{f(x.get('tp1'))}/{f(x.get('tp2'))}|{f(x.get('rr2'))}|{x['validation']}|{x['action']}|"
        )
    lines += ["", "## Raw 7+ requiring fresh IBKR PASS 2", ""]
    if result["raw_7_plus"]:
        for t in result["raw_7_plus"]:
            x = next(r for r in rows if r["ticker"] == t)
            lines.append(f"- **{t}** — PASS 1 {x['score']:.2f}; second IBKR snapshot required.")
    else:
        lines.append("- None.")
    lines += [
        "", "## Group checks", "",
        f"- Photonics compatible completed 1H: **{result['photonics_1h_up']}/7**",
        f"- Miners compatible completed 1H: **{result['miners_1h_up']}/4**; BTC compatible: **{result['btc_1h_up']}**",
        f"- SOXX compatible completed 1H: **{result['soxx_1h_up']}**",
        "", "## Boss Action", "",
    ]
    if result["best_setup_now"]:
        lines.append(f"Only consider {result['best_setup_now']} under its stated starter-size and stop rules; any raw 7+ still requires fresh IBKR PASS 2.")
    else:
        lines.append("No validated entry. Do not chase overnight prices; wait for completed-bar confirmation and acceptable spread.")
    text = "\n".join(lines) + "\n"
    (out / "latest.md").write_text(text)
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
