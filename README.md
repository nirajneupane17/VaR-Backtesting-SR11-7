# Backtesting Value-at-Risk Models Under SR 11-7

**Author:** Niraj Neupane, CA (ICAI): Quantitative Developer & Founder, Korvane & Calderyn Institute
**Paper:** *Backtesting Value-at-Risk Models Under SR 11-7: A Comparative Analysis of Kupiec, Christoffersen, and Basel Traffic-Light Tests Applied to S&P 500 Returns (2018–2024)*
**Series:** Korvane Research Series No. 1
**SSRN:** 

This repository contains the full data, code, and results underlying the paper above, so every table can be independently reproduced from the raw data in one command.

## Summary

The paper backtests three Value-at-Risk (VaR) models — Historical Simulation, Parametric (Normal), and Student-t — against S&P 500 daily returns from January 2018 through December 2024, using a genuine **walk-forward** design: every model is re-estimated daily on a strictly trailing 250-day window and evaluated against the next day's realized return (no look-ahead), yielding 1,509 out-of-sample forecast days. Models are evaluated with the Kupiec (1995) Proportion of Failures test, the Christoffersen (1998) Conditional Coverage test, and the Basel Committee Traffic Light test, under the SR 11-7 model-risk-management framework (and its April 2026 successor, SR 26-2).

Headline finding: at the 99% confidence level, all three models formally fail unconditional coverage, but by very different margins — Parametric Normal fails worst by far, while Historical Simulation and Student-t come much closer to adequate. Violation clustering is close to universal across all three models, and the 2022 rate-hiking regime produced *larger* proportional violation clustering than the sharper COVID-19 shock for every model tested. See the paper for full discussion.

## Repository structure
VaR-Backtesting-SR11-7/
├── data/
│ └── sp500_returns_2018_2024.csv # Raw S&P 500 daily closing levels + log returns
├── code/
│ └── walk_forward_backtest.py # Full reproducible pipeline (data -> all 7 tables)
├── results/
│ ├── table1_descriptive_stats.csv
│ ├── table3_var_estimates.csv
│ ├── table4_kupiec_results.csv
│ ├── table5_christoffersen_results.csv
│ ├── table6_basel_traffic_light.csv
│ └── table7_subperiod_analysis.csv
├── paper/
│ └── Neupane_2026_Backtesting_VaR_SR11-7.pdf
├── requirements.txt
└── README.md

## Data

`data/sp500_returns_2018_2024.csv` contains daily S&P 500 closing levels from **January 3, 2018 through December 30, 2024** (1,759 trading days), sourced from Yahoo Finance, with log returns pre-computed:

| Column | Description |
|---|---|
| `Date` | Trading date |
| `Price` | S&P 500 closing level |
| `Log_Return` | Daily log return, `ln(P_t / P_t-1)` |
| `Log_Return_%` | Same, expressed in percent |

## Reproducing the results

```bash
pip install -r requirements.txt
cd code
python walk_forward_backtest.py
```

This regenerates all six result tables in `results/` from the raw data in `data/`. Runtime is roughly 90 seconds — the Student-t distribution is refit by maximum likelihood on every one of the 1,509 out-of-sample days, which is the dominant cost.

**Every number in the paper is produced by this script.** No table, statistic, or figure in the paper was computed by hand or outside this pipeline.

## Methodology notes

- **Walk-forward, not full-sample.** All three models are re-estimated *daily* on a strictly trailing 250-day window (`WINDOW = 250` in the script) and tested only against information that would have been available at the time. This is a meaningfully more demanding design than the single-calibration approach used in several precedent studies (see the paper's Section 2.5), and is why results here differ from a naive full-sample backtest.
- **Out-of-sample window.** The first 250 observations (all of calendar 2018) are consumed as the initial estimation window, so the out-of-sample test period runs January 2, 2019 – December 30, 2024 (1,509 days).
- **Basel Traffic Light** (Table 6) is evaluated on the trailing 250 out-of-sample days only (calendar year 2024), per Basel Committee convention.
- **Subperiod analysis** (Table 7) decomposes the out-of-sample violations by market regime (Pre-COVID 2019, COVID Crisis 2020, Post-COVID Bull 2021, Rate Hike Bear 2022, Recovery 2023–2024).

## AI use disclosure

Generative AI (Claude, Anthropic) was used to assist with implementation of the backtesting code and documentation in this repository, and with drafting/editing of the accompanying paper. The author designed the research question and empirical methodology, sourced and independently verified the underlying data and all reported statistical results, and is solely responsible for the analysis, interpretation, and conclusions presented. See the AI Disclosure Statement in the paper itself for the full statement.

## Citation

If you use this data or code, please cite:

> Neupane, N. (2026). Backtesting Value-at-Risk Models Under SR 11-7: A Comparative Analysis of Kupiec, Christoffersen, and Basel Traffic-Light Tests Applied to S&P 500 Returns (2018–2024). *Korvane Research Series No. 1.* SSRN. [link]

## License

Code in this repository is released under the MIT License (see `LICENSE`). The paper itself (`paper/`) is the author's own copyrighted work; SSRN posting does not transfer copyright. The underlying market data is sourced from Yahoo Finance and is subject to their terms of use.

## Related work

This is Paper 1 of the Korvane Research Series. Paper 2 will introduce ML-LiqVaR, a regime-aware, machine-learning-augmented VaR model motivated directly by the violation-clustering findings in this paper.

---
Niraj Neupane · [korvane.com](https://korvane.com) · nirajneupane17@gmail.com
