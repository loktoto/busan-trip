#!/usr/bin/env python3
"""Causal bottom-zone backtest.

Input CSV columns: Date,Open,High,Low,Close,Volume.
Signals use completed close t; entries use next open t+1. Future prices are used
only by evaluation. The model is a research candidate, not an optimal strategy.
"""
from __future__ import annotations

import argparse, json, math
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd

HORIZONS = (42, 63, 84)


@dataclass
class Config:
    symbol: str
    watch_dd: float = .05
    start_dd: float = .05
    max_dd: float = .50
    max_deploy: float = .60
    power: float = 1.8
    micro_probe: float = .01
    min_tranche: float = .01
    max_tranche: float = .08
    cooldown: int = 10
    spacing: float = .025
    long_bear_days: int = 60
    long_bear_cap: float = .20
    crash_z: float = -2.0
    crash_volume: float = 1.25
    exhaustion_bonus: float = .075
    confirmation_bonus: float = .125


def load_config(path: Path | None, symbol: str) -> Config:
    raw = {} if path is None else json.loads(path.read_text())
    values = raw.get(symbol, raw.get("default", raw)) if isinstance(raw, dict) else {}
    values = {k: v for k, v in values.items() if k != "symbol"}
    cfg = Config(symbol=symbol, **values)
    if not (0 < cfg.start_dd < cfg.max_dd <= 1):
        raise ValueError("Require 0 < start_dd < max_dd <= 1")
    if not (0 < cfg.max_deploy <= 1 and 0 <= cfg.long_bear_cap <= cfg.max_deploy):
        raise ValueError("Invalid deployment limits")
    return cfg


def load_csv(path: Path) -> pd.DataFrame:
    required = ["Date", "Open", "High", "Low", "Close", "Volume"]
    df = pd.read_csv(path)
    missing = set(required) - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")
    df = df[required].copy()
    df["Date"] = pd.to_datetime(df["Date"])
    for c in required[1:]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna().sort_values("Date").drop_duplicates("Date").reset_index(drop=True)
    if len(df) < 260:
        raise ValueError("At least 260 daily rows are required")
    return df


def indicators(df: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    x = df.copy(); c=x.Close; h=x.High; l=x.Low; v=x.Volume
    x["cycle_high"] = c.cummax()
    x["cycle_dd"] = c/x.cycle_high-1
    x["dd_52w"] = c/c.rolling(252, min_periods=20).max()-1
    x["r1"],x["r5"],x["r10"] = c.pct_change(),c.pct_change(5),c.pct_change(10)
    x["rv20"] = np.log(c).diff().rolling(20).std(ddof=0)*math.sqrt(252)
    pc=c.shift(); tr=pd.concat([h-l,(h-pc).abs(),(l-pc).abs()],axis=1).max(axis=1)
    x["atrp"] = tr.rolling(14).mean()/c
    x["sma10"],x["sma20"],x["sma200"] = c.rolling(10).mean(),c.rolling(20).mean(),c.rolling(200).mean()
    x["sma200_slope"] = x.sma200/x.sma200.shift(20)-1
    x["newlow10"] = c <= c.rolling(10).min()
    x["newlow20"] = c <= c.rolling(20).min()
    x["vol_ratio"] = v/v.rolling(20).mean()
    x["close_loc"] = ((c-l)/(h-l).replace(0,np.nan)).fillna(.5)
    mean=x.r5.rolling(252,min_periods=60).mean(); sd=x.r5.rolling(252,min_periods=60).std(ddof=0)
    x["r5z"] = (x.r5-mean)/sd.replace(0,np.nan)
    uw=[]; n=0
    for price,peak in zip(c,x.cycle_high):
        n=0 if price >= peak*(1-1e-12) else n+1; uw.append(n)
    x["underwater"] = uw
    x["long_bear"] = (c<x.sma200)&(x.sma200_slope<0)&(x.underwater>=cfg.long_bear_days)
    votes=pd.concat([
        x.r5>x.r5.shift(5),
        x.vol_ratio<x.vol_ratio.shift(5),
        x.rv20<x.rv20.shift(5),
        x.close_loc>x.close_loc.shift(5)],axis=1).fillna(False).sum(axis=1)
    x["exhaustion"] = x.newlow20 & (votes>=2)
    low5=l.rolling(5).min()
    x["confirmation"] = (low5>low5.shift(5))&(c>x.sma10)&(x.atrp<x.atrp.shift(5))
    x["crash"] = (x.r5z<=cfg.crash_z)&(x.vol_ratio>=cfg.crash_volume)
    return x


def target(dd: float, cfg: Config) -> float:
    depth=abs(min(dd,0))
    if depth<cfg.start_dd: return 0
    z=np.clip((depth-cfg.start_dd)/(cfg.max_dd-cfg.start_dd),0,1)
    return float(cfg.max_deploy*z**cfg.power)


def episode_ids(x: pd.DataFrame, cfg: Config) -> pd.Series:
    out=[]; eid=0; active=False
    for dd in x.cycle_dd:
        if not active and dd<=-cfg.watch_dd: eid+=1; active=True
        out.append(eid if active else 0)
        if active and dd>=-.002: active=False
    return pd.Series(out,index=x.index)


def run(x: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    x=x.copy(); x["episode"]=episode_ids(x,cfg)
    rows=[]; deployed={}; last_i={}; last_px={}
    for i in range(200,len(x)-1):
        r=x.iloc[i]; eid=int(r.episode)
        if eid==0 or r.cycle_dd>-cfg.start_dd: continue
        used=deployed.get(eid,0.0); want=target(r.cycle_dd,cfg)
        if bool(r.long_bear) and not bool(r.exhaustion) and not bool(r.confirmation):
            want=min(want,cfg.long_bear_cap)
        if bool(r.exhaustion): want=max(want,used+cfg.exhaustion_bonus)
        if bool(r.confirmation): want=max(want,used+cfg.confirmation_bonus)
        want=min(want,cfg.max_deploy)
        fresh=bool(r.newlow10 or r.newlow20); crash=bool(r.crash)
        cooldown=eid not in last_i or i-last_i[eid]>=cfg.cooldown
        spacing=eid not in last_px or r.Close<=last_px[eid]*(1-cfg.spacing)
        eligible=(fresh or crash or bool(r.exhaustion) or bool(r.confirmation)) and (cooldown or spacing or bool(r.confirmation))
        if not eligible: continue
        if used==0: want=max(want,cfg.micro_probe)
        tranche=min(max(0,want-used),cfg.max_tranche,cfg.max_deploy-used)
        if tranche<cfg.min_tranche: continue
        nxt=x.iloc[i+1]; px=float(nxt.Open)
        state=4 if r.confirmation else 3 if r.exhaustion else 2
        used+=tranche; deployed[eid]=used; last_i[eid]=i+1; last_px[eid]=px
        rows.append(dict(symbol=cfg.symbol,episode=eid,signal_date=r.Date.date(),execution_date=nxt.Date.date(),
            execution_price=px,tranche=tranche,cumulative=used,state=state,cycle_dd=r.cycle_dd,
            dd_52w=r.dd_52w,atrp=r.atrp,rv20=r.rv20,volume_ratio=r.vol_ratio,
            underwater=int(r.underwater),long_bear=bool(r.long_bear),fresh_low=fresh,
            crash=crash,exhaustion=bool(r.exhaustion),confirmation=bool(r.confirmation)))
    return pd.DataFrame(rows)


def evaluate(x: pd.DataFrame, trades: pd.DataFrame) -> tuple[pd.DataFrame,pd.DataFrame,dict]:
    if trades.empty: return trades,pd.DataFrame(),{"trade_count":0,"episode_count":0}
    pos={d.date():i for i,d in enumerate(x.Date)}; detail=[]
    for _,t in trades.iterrows():
        rec=t.to_dict(); i=pos[t.execution_date]
        for h in HORIZONS:
            f=x.iloc[i:min(i+h,len(x)-1)+1]; j=int(f.Close.to_numpy().argmin()); low=float(f.iloc[j].Close)
            dist=t.execution_price/low-1
            rec.update({f"trough_{h}":low,f"days_to_trough_{h}":j,f"distance_{h}":dist,f"downside_{h}":low/t.execution_price-1})
            for p in (3,5,8): rec[f"within_{p}_{h}"]=dist<=p/100
        detail.append(rec)
    detail=pd.DataFrame(detail); episodes=[]
    for eid,g in detail.groupby("episode"):
        g=g.sort_values("execution_date"); first=pos[g.iloc[0].execution_date]; last=min(pos[g.iloc[-1].execution_date]+84,len(x)-1)
        trough=float(x.iloc[first:last+1].Close.min()); w=g.tranche.to_numpy(); p=g.execution_price.to_numpy()
        avg=float(np.average(p,weights=w)); dist=avg/trough-1
        r=dict(episode=int(eid),trade_count=len(g),total_deployment=float(w.sum()),trough=trough,
               weighted_entry=avg,weighted_distance=dist,max_additional_downside=trough/p.max()-1)
        for q in (3,5,8):
            d=p/trough-1; r[f"any_within_{q}"]=bool((d<=q/100).any()); r[f"weighted_within_{q}"]=dist<=q/100; r[f"capital_within_{q}"]=float(w[d<=q/100].sum())
        episodes.append(r)
    ep=pd.DataFrame(episodes)
    summary={"classification":"RESEARCH CANDIDATE — NOT GUARANTEED OR OPTIMAL","trade_count":len(detail),"episode_count":len(ep),
             "mean_deployment":float(ep.total_deployment.mean()),"mean_weighted_distance":float(ep.weighted_distance.mean())}
    for q in (3,5,8):
        summary[f"any_within_{q}_rate"]=float(ep[f"any_within_{q}"].mean()); summary[f"weighted_within_{q}_rate"]=float(ep[f"weighted_within_{q}"].mean())
    return detail,ep,summary


def main() -> None:
    ap=argparse.ArgumentParser(); ap.add_argument("--csv",type=Path,required=True); ap.add_argument("--symbol",required=True)
    ap.add_argument("--config",type=Path); ap.add_argument("--out",type=Path,default=Path("backtest-output")); a=ap.parse_args()
    cfg=load_config(a.config,a.symbol); x=indicators(load_csv(a.csv),cfg); trades=run(x,cfg); detail,episodes,summary=evaluate(x,trades)
    out=a.out/a.symbol; out.mkdir(parents=True,exist_ok=True)
    x.to_csv(out/"indicators.csv",index=False); trades.to_csv(out/"trades.csv",index=False)
    detail.to_csv(out/"trade_metrics.csv",index=False); episodes.to_csv(out/"episode_metrics.csv",index=False)
    summary.update({"symbol":a.symbol,"config":asdict(cfg),"signal_time":"close t","execution_time":"open t+1"})
    (out/"summary.json").write_text(json.dumps(summary,indent=2,default=str)); print(json.dumps(summary,indent=2,default=str))


if __name__=="__main__": main()
