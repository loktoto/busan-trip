# V5 hotfixes loaded after the frozen V4.1 core and V5 challenger source.
# Keep changes explicit so audit history can distinguish model logic from bug fixes.

_v5_base_indicator_cache = indicator_cache


def indicator_cache(signal: pd.DataFrame) -> dict[str, Any]:
    cache = _v5_base_indicator_cache(signal)
    if "ema5" not in cache:
        cache["ema5"] = signal.Close.ewm(span=5, adjust=False, min_periods=5).mean()
    return cache


def _choose_diverse(pool: pd.DataFrame, state_cache: dict[tuple, pd.Series], mode: str,
                    maximum: int = 6) -> list[tuple]:
    """Choose one low-correlation component per entry family using absolute quality.

    V5 keeps percentile scores for diagnostics, but component identity must not be
    determined by ranks that change when unrelated candidates move. Prefer candidates
    that pass development, stressed-cost and purged-block stability. Small tolerances
    absorb adjusted-price noise; they do not relax the final production gates.
    """
    chosen: list[tuple] = []
    families: set[str] = set()
    subset = pool[pool["mode"] == mode].copy()
    if subset.empty:
        return chosen

    if "stable_quality" not in subset:
        subset["stable_quality"] = subset["development_score"].round(4)
    subset["robust_component"] = (
        subset["development_pass"].fillna(False).astype(bool)
        & (subset["block_excess_worst"] >= -0.001)
        & (subset["block_dd_worst"] >= -0.015)
        & (subset["stress_dev_excess"] > 0.0)
    )
    subset["stable_quality"] = subset["stable_quality"].round(4)
    subset["stable_block_excess"] = subset["block_excess_worst"].round(4)
    subset["stable_block_dd"] = subset["block_dd_worst"].round(4)
    subset = subset.sort_values(
        [
            "robust_component", "development_pass", "stable_quality",
            "stable_block_excess", "stable_block_dd", "entry_family",
            "entry_id", "exit_id", "overlay", "stop",
        ],
        ascending=[False, False, False, False, False, True, True, True, True, True],
    )
    for row in subset.itertuples():
        key = (int(row.entry_id), int(row.exit_id), row.mode, row.overlay, row.stop)
        if key not in state_cache or row.entry_family in families:
            continue
        state = state_cache[key].astype(float)
        acceptable = True
        for existing in chosen:
            corr = state.corr(state_cache[existing].astype(float))
            if pd.notna(corr) and corr > 0.90:
                acceptable = False
                break
        if acceptable:
            chosen.append(key)
            families.add(row.entry_family)
        if len(chosen) >= maximum:
            break
    return chosen
