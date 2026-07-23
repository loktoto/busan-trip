from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

OUT = Path(__file__).resolve().parent / "results_v3"
OUT.mkdir(parents=True, exist_ok=True)
TICKERS = ["SMH", "SOXX", "USD", "SOXL"]
COST = 0.001
START_CAPITAL = 10_000.0


def dl(ticker: str) -> pd.DataFrame:
    x = yf.download(ticker, period="max", interval="1d", auto_adjust=True,
                    actions=False, progress=False, threads=False)
    if isinstance(x.columns, pd.MultiIndex):
        x.columns = x.columns.get_level_values(0)
    x = x.rename(columns=str.title)[["Open", "High", "Low", "Close", "Volume"]]
    x.index = pd.to_datetime(x.index).tz_localize(None)
    return x.dropna().sort_index()


def rsi(close: pd.Series, n: int = 2) -> pd.Series:
    d = close.diff()
    up = d.clip(lower=0)
    dn = -d.clip(upper=0)
    au = up.ewm(alpha=1/n, adjust=False, min_periods=n).mean()
    ad = dn.ewm(alpha=1/n, adjust=False, min_periods=n).mean()
    out = 100 - 100/(1 + au/ad.replace(0, np.nan))
    return out.where(ad != 0, 100).where(au != 0, 0)


def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    pc = df.Close.shift(1)
    tr = pd.concat([(df.High-df.Low), (df.High-pc).abs(), (df.Low-pc).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1/n, adjust=False, min_periods=n).mean()


def feat(df: pd.DataFrame) -> pd.DataFrame:
    f = pd.DataFrame(index=df.index)
    f["c"] = df.Close
    f["rsi2"] = rsi(df.Close, 2)
    f["atr14"] = atr(df, 14)
    f["atrp"] = f.atr14 / f.c
    f["vol20"] = df.Close.pct_change().rolling(20).std() * math.sqrt(252)
    for n in [5, 10, 15, 20, 30, 40, 50, 63, 100, 150, 200, 250]:
        f[f"sma{n}"] = df.Close.rolling(n).mean()
    for n in [20, 50, 63, 100, 126]:
        f[f"ret{n}"] = df.Close.pct_change(n)
        f[f"high{n}"] = df.Close.shift(1).rolling(n).max()
    return f


def event_state(entry: pd.Series, exit_: pd.Series) -> pd.Series:
    e, x = entry.fillna(False).to_numpy(bool), exit_.fillna(False).to_numpy(bool)
    out = np.zeros(len(e)); state = 0
    for i in range(len(e)):
        if state == 0 and e[i]: state = 1
        elif state == 1 and x[i]: state = 0
        out[i] = state
    return pd.Series(out, index=entry.index)


def hold_state(entry: pd.Series, hold: int) -> pd.Series:
    e = entry.fillna(False).to_numpy(bool); out = np.zeros(len(e)); left = 0
    for i, flag in enumerate(e):
        if left == 0 and flag: left = hold
        if left > 0:
            out[i] = 1; left -= 1
    return pd.Series(out, index=entry.index)


def trade(product: pd.DataFrame, weight: pd.Series) -> tuple[pd.Series, pd.Series]:
    idx = product.index.intersection(weight.index)
    p = product.loc[idx]
    w = weight.reindex(idx).ffill().fillna(0).clip(0, 1)
    pos = w.shift(1).fillna(0)
    r = p.Open.shift(-1).div(p.Open).sub(1)
    turnover = pos.diff().abs().fillna(pos.abs())
    ret = (pos*r - COST*turnover).dropna()
    return ret, pos.reindex(ret.index)


def metrics(ret: pd.Series, pos: pd.Series) -> dict:
    ret = ret.dropna(); pos = pos.reindex(ret.index).fillna(0)
    if len(ret) < 100: return {}
    eq = (1+ret).cumprod(); years = len(ret)/252
    cagr = eq.iloc[-1]**(1/years)-1
    vol = ret.std(ddof=0)*math.sqrt(252)
    shp = ret.mean()/ret.std(ddof=0)*math.sqrt(252) if ret.std(ddof=0)>0 else np.nan
    dd = eq/eq.cummax()-1; mdd = dd.min()
    return dict(cagr=cagr, sharpe=shp, maxdd=mdd,
                calmar=cagr/abs(mdd) if mdd<0 else np.nan,
                exposure=pos.mean(), trades=pos.diff().abs().sum()/2,
                end_value=START_CAPITAL*eq.iloc[-1])


def make_candidates(f: pd.DataFrame) -> dict[str, pd.Series]:
    out = {}
    trend = f.c > f.sma200
    for low in [3, 5, 7, 10]:
        for reclaim in [5, 10, 15, 20]:
            cross = (f.c > f[f"sma{reclaim}"]) & (f.c.shift(1) <= f[f"sma{reclaim}"].shift(1))
            trigger = trend & (f.rsi2.rolling(5).min() < low) & cross
            for hold in [20, 30, 40, 50, 60]:
                out[f"PB_RSI{low}_R{reclaim}_H{hold}"] = hold_state(trigger, hold)
                for stop in [0.08, 0.12, 0.16]:
                    # trailing exit proxied on signal asset close from entry peak
                    base = hold_state(trigger, hold)
                    peak = f.c.where(base>0).groupby((base.diff().fillna(base)!=0).cumsum()).cummax()
                    stopped = base * (f.c >= peak*(1-stop))
                    out[f"PB_RSI{low}_R{reclaim}_H{hold}_TS{int(stop*100)}"] = stopped
    for fast in [20, 30, 40, 50, 63]:
        for slow in [150, 200, 250]:
            reg = event_state(f.c > f[f"sma{fast}"], f.c < f[f"sma{slow}"])
            out[f"TREND_{fast}_{slow}"] = reg
            for target in [0.25, 0.35, 0.45]:
                volw = (target/f.vol20).clip(0.25,1.0)
                out[f"TREND_{fast}_{slow}_VT{int(target*100)}"] = reg*volw
    score = ((f.c>f.sma20).astype(int)+(f.c>f.sma50).astype(int)+(f.c>f.sma100).astype(int)+
             (f.ret20>0).astype(int)+(f.ret63>0).astype(int)+(f.ret126>0).astype(int))
    for ent in [4,5,6]:
        for ex in [1,2,3]:
            if ex < ent:
                out[f"MHT_{ent}_{ex}"] = event_state(score>=ent, score<=ex)
    # Hybrid: long trend with increased weight on oversold reclaim.
    for fast in [40, 50, 63]:
        reg = event_state(f.c > f[f"sma{fast}"], f.c < f.sma200)
        for low in [5, 7, 10]:
            cross = (f.c>f.sma10)&(f.c.shift(1)<=f.sma10.shift(1))
            pulse = hold_state((f.rsi2.rolling(5).min()<low)&cross&trend, 40)
            for base in [0.35, 0.5, 0.65]:
                out[f"HYB_F{fast}_L{low}_B{int(base*100)}"] = (base*reg + (1-base)*pulse).clip(0,1)
    return out


def windows(index: pd.DatetimeIndex) -> dict[str, pd.Timestamp]:
    end=index.max(); ans={"MAX":index.min()}
    for y in [3,5,10]: ans[f"{y}Y"] = index[index.searchsorted(end-pd.DateOffset(years=y))]
    return ans


def rolling(ret: pd.Series, pos: pd.Series, years: int) -> list[dict]:
    rows=[]; start=ret.index.min(); end=ret.index.max()
    while start+pd.DateOffset(years=years)<=end:
        stop=start+pd.DateOffset(years=years); m=(ret.index>=start)&(ret.index<=stop)
        z=metrics(ret[m],pos[m])
        if z: rows.append({"start":start,"end":stop,"years":years,**z})
        start += pd.DateOffset(months=3)
    return rows


def main():
    data={t:dl(t) for t in TICKERS}; end=min(x.index.max() for x in data.values())
    data={k:v.loc[:end] for k,v in data.items()}; rows=[]; cache={}
    for signal in ["SMH","SOXX"]:
        candidates=make_candidates(feat(data[signal]))
        for product in ["USD","SOXL"]:
            for name,w in candidates.items():
                ret,pos=trade(data[product],w); cache[(product,signal,name)]=(ret,pos)
                for win,start in windows(ret.index).items():
                    z=metrics(ret.loc[start:],pos.loc[start:])
                    if z: rows.append({"product":product,"signal":signal,"strategy":name,"window":win,**z})
    res=pd.DataFrame(rows); res.to_csv(OUT/"all_results.csv",index=False)
    base=res[res.window.isin(["3Y","5Y","10Y","MAX"])]
    rank=base.groupby(["product","signal","strategy"],as_index=False).agg(
        median_cagr=("cagr","median"),worst_cagr=("cagr","min"),median_sharpe=("sharpe","median"),
        worst_sharpe=("sharpe","min"),median_calmar=("calmar","median"),worst_maxdd=("maxdd","min"),
        median_exposure=("exposure","median"),trades=("trades","sum"))
    rank["score"]=(rank.median_sharpe.clip(-1,3)+rank.median_calmar.clip(-1,3)+
                   .5*rank.worst_cagr.clip(-1,1)+.25*rank.worst_sharpe.clip(-1,2)-
                   .25*(rank.worst_maxdd.abs()>0.65))
    rank=rank.sort_values(["product","score"],ascending=[True,False]); rank.to_csv(OUT/"robust_rank.csv",index=False)
    rr=[]
    for product in ["USD","SOXL"]:
        top=rank[rank.product==product].head(10)
        for _,r in top.iterrows():
            ret,pos=cache[(r.product,r.signal,r.strategy)]
            for y in [3,5]:
                for x in rolling(ret,pos,y): rr.append({"product":r.product,"signal":r.signal,"strategy":r.strategy,**x})
    pd.DataFrame(rr).to_csv(OUT/"top10_rolling.csv",index=False)
    meta={"generated_utc":pd.Timestamp.utcnow().isoformat(),"data_end":str(end.date()),
          "method":"actual adjusted ETF OHLC; completed close signal; next-open execution; 10bps changes",
          "families":["pullback reclaim","trailing stop","trend","vol targeting","MHT","trend-pullback hybrid"]}
    (OUT/"methodology.json").write_text(json.dumps(meta,indent=2),encoding="utf-8")
    lines=["# Semiconductor Leverage V3 Challenger Search","",f"Data through {end.date()}.","",
           "|Product|Signal|Strategy|Median CAGR|Worst CAGR|Median Sharpe|Median Calmar|Worst DD|Exposure|",
           "|---|---|---|---:|---:|---:|---:|---:|---:|"]
    for product in ["USD","SOXL"]:
        for _,r in rank[rank.product==product].head(10).iterrows():
            lines.append(f"|{r.product}|{r.signal}|{r.strategy}|{r.median_cagr:.1%}|{r.worst_cagr:.1%}|{r.median_sharpe:.2f}|{r.median_calmar:.2f}|{r.worst_maxdd:.1%}|{r.median_exposure:.1%}|")
    (OUT/"REPORT.md").write_text("\n".join(lines),encoding="utf-8")
    print("\n".join(lines))

if __name__=="__main__": main()
