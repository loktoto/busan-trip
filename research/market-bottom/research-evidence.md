# Research Evidence and Design Implications

This note maps external evidence to model design. Evidence that predicts medium-horizon returns is not automatically a precise daily bottom timer.

## 1. Variance risk premium

Federal Reserve research finds that the difference between model-free implied variance and realised variance predicts aggregate equity returns, with especially strong evidence at approximately two-to-four-month horizons. The construction depends on model-free option-implied variance and high-frequency realised variance; simple Black–Scholes IV or daily historical volatility is not equivalent.

Design implication:

- accept genuine model-free VRP/downside VRP as a medium-horizon anticipatory family;
- label simple IV-minus-HV as a low-weight proxy;
- do not let VRP alone declare the exact trough.

Primary references:

- https://www.federalreserve.gov/econres/feds/expected-stock-returns-and-variance-risk-premia.htm
- https://www.federalreserve.gov/econres/feds/downside-variance-risk-premium.htm
- https://www.federalreserve.gov/econres/ifdp/variance-risk-premium-components-and-international-stock-return-predictability.htm

## 2. Market breadth

International evidence reports that market breadth predicts future market and industry returns across 64 countries from 1973–2018. This supports treating breadth as independent information rather than a cosmetic technical indicator.

Design implication:

- test breadth incrementally and point-in-time;
- prioritise price-new-low / breadth-no-new-low divergence for exhaustion;
- build semiconductor breadth from historical constituents where possible;
- do not convert one fixed oversold threshold into a universal rule.

Reference:

- https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3444882

## 3. Volatility-managed leverage

Moreira and Muir document that reducing exposure when volatility is high can improve risk-adjusted results across multiple factors. This supports stronger volatility control for temporary leveraged ETF exposure, but it does not prove that volatility alone identifies the bottom.

Design implication:

- ordinary 1× exposure may use a small anticipatory probe;
- SSO/QLD/USD require falling realised volatility plus price/breadth confirmation;
- leverage exits when volatility reaccelerates.

Reference:

- https://www.nber.org/papers/w22208

## 4. Systemic-stress filters

The OFR Financial Stress Index is a daily composite of 33 variables across credit, valuation, funding, safe assets and volatility. It is designed to identify systemic stress and publishes with data current from two business days prior.

Design implication:

- use OFR FSI as a lagged systemic veto/regime feature;
- never present it as an hourly bottom trigger;
- align the backtest to publication availability.

References:

- https://www.financialresearch.gov/working-papers/2017/10/25/the-ofr-financial-stability-index/
- https://www.financialresearch.gov/financial-stress-index/

## 5. Multiple testing and overfitting

Deflated Sharpe Ratio adjusts performance claims for selection bias, multiple testing and non-normal returns. Probability of Backtest Overfitting uses combinatorially symmetric cross-validation to estimate how often an in-sample winner degrades out of sample.

Design implication:

- archive every candidate, not only winners;
- use purged walk-forward validation for bottom-proximity metrics;
- add formal CSCV/PBO only after a complete candidate-by-fold matrix is persisted;
- use DSR only for return/Sharpe optimisation, not as a substitute for bottom-proximity validation.

References:

- https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551
- https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2326253

## 6. Research hierarchy after this review

| Family | Role | Current status |
|---|---|---|
| unresolved-cycle drawdown | anticipatory price context | retain |
| volatility-normalised decline | cross-regime stress | retain |
| causal back-loaded sizing | capital preservation | retain |
| fresh low + spacing/cooldown | repeated-signal control | retain |
| underwater duration / long-bear throttle | slow-bear defence | retain |
| volume/liquidation divergence | exhaustion | retain, validate |
| point-in-time breadth divergence | exhaustion / confirmation | highest-priority addition |
| genuine downside VRP | medium-horizon anticipatory evidence | high priority, data intensive |
| HY OAS / OFR FSI | systemic veto | retain with publication lag |
| RSI, MACD, absolute VIX | support only | demote |
| falling realised volatility | leveraged-entry control | retain |

## 7. Falsification rule

A feature should be removed when it fails to improve at least one out-of-sample objective without materially damaging the others:

- missed-bottom rate;
- at-least-one-tranche proximity within 5%/8%;
- capital deployed within 5%/8%;
- capital-weighted entry distance;
- post-entry adverse excursion;
- stability across crash, ordinary correction and slow-bear regimes.
