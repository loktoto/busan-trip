# V5 hotfixes loaded after the frozen V4.1 core and V5 challenger source.
# Keep changes explicit so audit history can distinguish model logic from bug fixes.

_v5_base_indicator_cache = indicator_cache


def indicator_cache(signal: pd.DataFrame) -> dict[str, Any]:
    cache = _v5_base_indicator_cache(signal)
    if "ema5" not in cache:
        cache["ema5"] = signal.Close.ewm(span=5, adjust=False, min_periods=5).mean()
    return cache
