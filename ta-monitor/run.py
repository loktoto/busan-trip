from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from engine import run
from post_validate import apply_guardrails


def f(v, n=2):
    try:
        return f"{float(v):.{n}f}"
    except (TypeError, ValueError):
        return "N/A"


def normalize_snapshot(snapshot_path: str) -> tuple[str, list[str]]:
    data = json.loads(Path(snapshot_path).read_text())
    adjustments: list[str] = []
    for ticker, quote in data.get("quotes", {}).items():
        last = quote.get("price")
        mark = quote.get("mark")
        bid = quote.get("bid")
        ask = quote.get("ask")
        quality = str(quote.get("quality", ""))
        outside_nbbo = False
        try:
            outside_nbbo = (
                last is not None and bid is not None and ask is not None
                and (float(last) < float(bid) or float(last) > float(ask))
            )
        except (TypeError, ValueError):
            outside_nbbo = False
        stale = "stale" in quality or outside_nbbo
        if stale and mark is not None:
            quote["raw_last"] = last
            quote["price"] = mark
            quote["price_source"] = "IBKR mark (stale/outside-NBBO last)"
            adjustments.append(ticker)
        else:
            quote["price_source"] = "IBKR last"
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    with tmp:
        json.dump(data, tmp, ensure_ascii=False, indent=2)
    return tmp.name, adjustments


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--snapshot", required=True)
    p.add_argument("--out", default="ta-monitor/output")
    a = p.parse_args()
    normalized_path, quote_adjustments = normalize_snapshot(a.snapshot)
    result = apply_guardrails(run(normalized_path))
    result["quote_adjustments"] = quote_adjustments
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
        "- Guardrail: alerts use fresh executable-price R/R, not historical trigger-price R/R.",
        f"- Stale-last normalization: **{', '.join(quote_adjustments) if quote_adjustments else 'none'}**",
        "",
        f"## BEST SETUP NOW: {result['best_setup_now'] or 'NONE'}",
        f"## BEST SETUP IF TRIGGERED: {result['best_if_triggered'] or 'NONE'}",
        f"## VALIDATED 7+: {', '.join(result['validated_7_plus']) or 'NONE'}",
        "",
        "|#|Ticker|Score|Tier|Weekly|Daily|1H|State|Price|Trigger|SL tactical/structural|TP1/TP2|R/R trigger|R/R executable|Validation|Action|",
        "|---:|---|---:|:---:|---|---|---|---|---:|---:|---|---|---:|---:|---|---|",
    ]
    for x in rows:
        lines.append(
            f"|{x['rank']}|{x['ticker']}|{x['score']:.2f}|{x.get('tier', 'D')}|{x['weekly']}|{x['daily']}|{x['hourly']}|"
            f"{x['state']}|{f(x.get('price'))}|{f(x.get('trigger'))}|{f(x.get('tactical'))}/{f(x.get('structural'))}|"
            f"{f(x.get('tp1'))}/{f(x.get('tp2'))}|{f(x.get('rr2_trigger', x.get('rr2')))}|{f(x.get('rr2_executable'))}|"
            f"{x['validation']}|{x['action']}|"
        )
    lines += ["", "## Raw 7+ requiring fresh IBKR PASS 2", ""]
    if result["raw_7_plus"]:
        for t in result["raw_7_plus"]:
            x = next(r for r in rows if r["ticker"] == t)
            lines.append(f"- **{t}** — guardrailed PASS 1 {x['score']:.2f}; second IBKR snapshot required.")
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
        lines.append("No validated entry. Do not chase overnight prices; wait for completed-bar confirmation, acceptable spread and fresh executable R/R of at least 2R.")
    text = "\n".join(lines) + "\n"
    (out / "latest.md").write_text(text)
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())