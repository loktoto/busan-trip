from __future__ import annotations


def apply_guardrails(result: dict) -> dict:
    """Apply non-negotiable execution guardrails after the first-pass model.

    The initial setup calculation may describe R/R from a historical trigger. An alert,
    however, must be judged from the fresh executable price. This pass prevents an old
    trigger from making an extended setup appear to have >=2R.
    """
    confirmed_states = {"BREAKOUT STARTER", "BREAKOUT CONFIRMED", "RE-ENTRY CONFIRMED", "ADD ON RETEST"}
    actionable_states = confirmed_states | {"PULLBACK READY", "RE-ENTRY PULLBACK READY"}

    for row in result.get("results", []):
        try:
            price = float(row["price"])
            tactical = float(row["tactical"])
            tp1 = float(row["tp1"])
            tp2 = float(row["tp2"])
            trigger = float(row["trigger"])
        except (KeyError, TypeError, ValueError):
            continue

        risk = price - tactical
        executable_rr = (tp2 - price) / risk if risk > 0 and tp2 > price else 0.0
        tp1_r = (tp1 - price) / risk if risk > 0 and tp1 > price else 0.0
        row["rr2_trigger"] = row.get("rr2")
        row["rr2_executable"] = round(executable_rr, 2)
        row["tp1_distance_r"] = round(tp1_r, 2)

        reasons = []
        if executable_rr < 2.0:
            reasons.append("fresh executable R/R below 2R")
        if tp1_r < 0.75:
            reasons.append("next target/resistance inside 0.75R")
        if price < trigger and row.get("state") in confirmed_states:
            reasons.append("fresh price below stated trigger")
        if abs(float(row.get("live_week_atr") or 0)) > 0.5:
            reasons.append("live week extended beyond 0.5 weekly ATR")

        if reasons:
            deductions = 0.5 * len(reasons)
            row["score"] = round(max(0.0, min(float(row.get("score", 0)) - deductions, 6.9)), 2)
            if row.get("state") in confirmed_states:
                row["state"] = "RE-ENTRY WATCH" if row.get("counter_trend") else "BREAKOUT PENDING"
            elif row.get("state") in actionable_states and executable_rr < 2.0:
                row["state"] = "WATCH"
            row["validation"] = "GUARDRAIL DOWNGRADED — NO ENTRY ALERT"
            row["action"] = "Wait for a new base/retest and fresh executable R/R >=2R"
            row.setdefault("penalties", []).extend(reasons)

    result["results"].sort(key=lambda x: float(x.get("score", 0)), reverse=True)
    for rank, row in enumerate(result["results"], 1):
        row["rank"] = rank
    result["raw_7_plus"] = [r["ticker"] for r in result["results"] if float(r.get("score", 0)) >= 7]
    result["validated_7_plus"] = []
    valid_now = {
        "BREAKOUT STARTER", "BREAKOUT CONFIRMED", "PULLBACK READY",
        "RE-ENTRY CONFIRMED", "RE-ENTRY PULLBACK READY", "ADD ON RETEST",
    }
    result["best_setup_now"] = next(
        (r["ticker"] for r in result["results"] if r.get("state") in valid_now and float(r.get("score", 0)) >= 6.5),
        None,
    )
    result["best_if_triggered"] = next(
        (r["ticker"] for r in result["results"] if r.get("state") in {"BREAKOUT PENDING", "RE-ENTRY BREAKOUT PENDING", "WATCH", "RE-ENTRY WATCH"}),
        None,
    )
    return result
