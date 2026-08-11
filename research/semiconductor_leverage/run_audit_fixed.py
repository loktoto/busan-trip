from __future__ import annotations

import json
from pathlib import Path
import pandas as pd

import semiconductor_leverage_audit as m

OUT = Path(__file__).resolve().parent / "results"
OUT.mkdir(parents=True, exist_ok=True)


def select_candidates(agg: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for product in ["USD", "SOXL"]:
        pa = agg[agg["product"] == product]
        groups = [
            ("ROBUST_OVERALL", pa),
            ("BEST_MA_REGIME", pa[pa["family"] == "MA_REGIME"]),
            ("BEST_BREAKOUT", pa[pa["family"] == "BREAKOUT_RSI"]),
            ("BEST_PULLBACK", pa[pa["family"] == "PULLBACK_RECLAIM"]),
            ("BEST_MHT", pa[pa["family"] == "MHT"]),
        ]
        seen = set()
        for label, subset in groups:
            if subset.empty:
                continue
            r = subset.iloc[0]
            ident = (r["product"], r["signal"], r["strategy"])
            if ident in seen:
                continue
            seen.add(ident)
            rows.append({"selection": label, **r.to_dict()})
    return pd.DataFrame(rows)


def slice_metrics(series: pd.DataFrame, start: str, end: str) -> dict:
    x = series.loc[pd.Timestamp(start):pd.Timestamp(end)]
    if len(x) < 100:
        return {}
    return m.metrics(x["ret"], x["pos"])


def main() -> None:
    raw = m.download_data()
    for ticker, df in raw.items():
        df.to_csv(OUT / f"input_{ticker}_adjusted_ohlc.csv")

    results, agg, cache = m.evaluate()
    results.to_csv(OUT / "all_strategy_windows.csv", index=False)
    agg.to_csv(OUT / "robust_rank.csv", index=False)
    selected = select_candidates(agg)
    selected.to_csv(OUT / "selected_strategies.csv", index=False)

    compare_rows = []
    for _, r in selected.iterrows():
        q = results[(results["product"] == r["product"]) &
                    (results["signal"] == r["signal"]) &
                    (results["strategy"] == r["strategy"])]
        for _, x in q.iterrows():
            compare_rows.append({"selection": r["selection"], **x.to_dict()})
    for product in ["USD", "SOXL"]:
        q = results[(results["product"] == product) &
                    (results["family"] == "BUY_HOLD")]
        for _, x in q.iterrows():
            compare_rows.append({"selection": "BUY_HOLD", **x.to_dict()})
    pd.DataFrame(compare_rows).to_csv(OUT / "selected_10000_comparison.csv", index=False)

    rolling_rows = []
    split_rows = []
    split_defs = [
        ("EARLY", "2007-01-01", "2015-12-31"),
        ("MID", "2016-01-01", "2020-12-31"),
        ("COVID_TO_2023", "2021-01-01", "2023-12-31"),
        ("RECENT", "2024-01-01", "2099-12-31"),
    ]
    for _, r in selected.iterrows():
        key = f"{r['product']}|{r['signal']}|{r['strategy']}"
        series = cache[key]
        for years in [3, 5]:
            for x in m.rolling_metrics(series, years):
                rolling_rows.append({"product": r["product"], "signal": r["signal"],
                                     "family": r["family"], "strategy": r["strategy"], **x})
        for label, start, end in split_defs:
            met = slice_metrics(series, start, end)
            if met:
                split_rows.append({"product": r["product"], "signal": r["signal"],
                                   "family": r["family"], "strategy": r["strategy"],
                                   "period": label, "start": start, "end": end, **met})
    pd.DataFrame(rolling_rows).to_csv(OUT / "selected_rolling_windows.csv", index=False)
    pd.DataFrame(split_rows).to_csv(OUT / "selected_time_splits.csv", index=False)

    platform_rows = []
    for product in ["USD", "SOXL"]:
        for family in ["MA_REGIME", "BREAKOUT_RSI", "PULLBACK_RECLAIM", "MHT"]:
            sub = agg[(agg["product"] == product) & (agg["family"] == family)].head(10)
            if sub.empty:
                continue
            platform_rows.append({
                "product": product,
                "family": family,
                "top10_median_robust_score": sub["robust_score"].median(),
                "top10_median_cagr": sub["median_cagr"].median(),
                "top10_worst_of_worst_cagr": sub["worst_cagr"].min(),
                "top10_median_sharpe": sub["median_sharpe"].median(),
                "top10_median_calmar": sub["median_calmar"].median(),
                "top10_worst_maxdd": sub["worst_maxdd"].min(),
                "dominant_signal": sub["signal"].mode().iloc[0],
            })
    pd.DataFrame(platform_rows).to_csv(OUT / "family_platform_summary.csv", index=False)

    roll = pd.DataFrame(rolling_rows)
    roll_summary = []
    if not roll.empty:
        for keys, sub in roll.groupby(["product", "signal", "family", "strategy", "roll_years"]):
            roll_summary.append({
                "product": keys[0], "signal": keys[1], "family": keys[2],
                "strategy": keys[3], "roll_years": keys[4], "windows": len(sub),
                "positive_cagr_pct": (sub["cagr"] > 0).mean(),
                "median_cagr": sub["cagr"].median(), "worst_cagr": sub["cagr"].min(),
                "median_sharpe": sub["sharpe"].median(), "worst_sharpe": sub["sharpe"].min(),
                "median_maxdd": sub["max_drawdown"].median(), "worst_maxdd": sub["max_drawdown"].min(),
            })
    pd.DataFrame(roll_summary).to_csv(OUT / "selected_rolling_summary.csv", index=False)

    metadata = {
        "generated_utc": pd.Timestamp.utcnow().isoformat(),
        "data_end": str(min(df.index.max() for df in raw.values()).date()),
        "method": "Adjusted daily OHLC; completed-close signal; next-open execution; 10 bps each position change; 0% cash return.",
        "selection": "Robust score uses 3Y/5Y/10Y/MAX; 1Y excluded due exceptional 2025-26 semiconductor rally.",
        "important": "USD and SOXL track different benchmarks. SOXL results use actual SOXL history only.",
    }
    (OUT / "methodology.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    def pct(x):
        return "n/a" if pd.isna(x) else f"{x:.1%}"
    lines = ["# Semiconductor Leveraged ETF Daily Audit", "",
             f"Data through **{metadata['data_end']}**.", "", "## Method",
             "- Completed daily close generates the signal; execution occurs at the next open.",
             "- 10 bps per position change; no cash yield; adjusted OHLC.",
             "- SOXX and SMH tested independently as signals; USD and SOXL tested independently as products.",
             "- 1Y results are reported but excluded from model selection.", "",
             "## Robust selected candidates", "",
             "| Product | Selection | Signal | Family | Strategy | Median CAGR | Worst CAGR | Median Sharpe | Median Calmar | Worst MaxDD | Exposure |",
             "|---|---|---|---|---|---:|---:|---:|---:|---:|---:|"]
    for _, r in selected.iterrows():
        lines.append(f"| {r['product']} | {r['selection']} | {r['signal']} | {r['family']} | {r['strategy']} | "
                     f"{pct(r['median_cagr'])} | {pct(r['worst_cagr'])} | {r['median_sharpe']:.2f} | "
                     f"{r['median_calmar']:.2f} | {pct(r['worst_maxdd'])} | {pct(r['median_exposure'])} |")
    lines += ["", "## Guardrails",
              "- The exact top parameter is not adopted unless its neighboring parameter family is also robust.",
              "- SOXL benchmark history changed; no pre-inception synthetic SOXL is used here.",
              "- These are historical results, not guaranteed alpha."]
    (OUT / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
