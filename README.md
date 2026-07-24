# Backtesting Value-at-Risk Models Under SR 11-7

**Author:** Niraj Neupane, CA (ICAI) · Quantitative Developer & Founder, Korvane & Calderyn Institute

**Paper:** *Backtesting Value-at-Risk Models Under SR 11-7: A Comparative Analysis of Kupiec, Christoffersen, and Basel Traffic-Light Tests Applied to S&P 500 Returns (2018–2024)*

**Series:** Korvane Research Series No. 1

**SSRN:** *Forthcoming*

**Keywords:** Value-at-Risk · Backtesting · Kupiec Test · Christoffersen Test · Basel Traffic Light · SR 11-7 · SR 26-2 · Model Validation · Walk-Forward Backtesting · Historical Simulation · Student-t · Fat Tails · Market Risk

---

## Abstract

This paper backtests three Value-at-Risk (VaR) models — Historical Simulation, Parametric (Normal), and Student-t — against S&P 500 daily returns covering January 2018 through December 2024. That seven-year window spans four distinct market regimes: the tail end of pre-COVID growth, the 2020 COVID-19 crash and rapid recovery, the 2022 Fed rate-hike bear market, and the 2023–2024 rebound.

Unlike most backtesting studies that calibrate once over a fixed period, this study uses a **walk-forward design**: each model is recalibrated daily on the previous 250 trading days and tested against the *next* day's actual return — giving 1,509 genuine out-of-sample forecast days from January 2019 through December 2024.

**Three backtesting tests are applied:** Kupiec's Proportion of Failures (1995), Christoffersen's Conditional Coverage (1998), and the Basel Committee Traffic Light test — all within the SR 11-7 model risk management framework, which governed U.S. banks until the Fed's April 2026 switch to SR 26-2.

**Key findings:** At 99% confidence, all three models fail unconditional coverage, but the Parametric Normal is the worst offender by far (44 violations, LR = 36.92, p < 0.0001) versus Historical Simulation (26 violations, LR = 6.55) and Student-t (28 violations, LR = 8.91). Violation clustering is universal — every model fails Christoffersen independence at 95%. The 2022 rate-hiking regime caused *more* proportional violation excess than the sharper COVID crash — because fixed-window estimators absorb sudden shocks faster than slow, grinding regime shifts. None of the models reached Basel's Green zone in the trailing 250-day 2024 window.

---

## Repository Contents

| File | Description |
|:---|:---|
| `Neupane_2026_Backtesting_VaR_SR11-7.pdf` | Full research paper (PDF) |
| `Data_S_P500.csv` | S&P 500 daily prices and log returns (2018–2024, 1,759 days) |
| `Data_python.ipynb` | Python notebook — data preparation, VaR estimation, backtesting |
| `Code.html` | Rendered HTML output of the full analysis notebook |

---

## Data

### `Data_S_P500.csv`

| Column | Description |
|:---|:---|
| `Date` | Trading date (YYYY-MM-DD) |
| `Price` | S&P 500 daily closing price |
| `Log_Return` | Daily log return: ln(Pₜ/Pₜ₋₁) |
| `Log_Return_%` | Log return expressed as percentage |

**Coverage:** January 3, 2018 – December 30, 2024 · 1,759 trading days

**Out-of-sample window:** January 2, 2019 – December 30, 2024 · 1,509 forecast days (first 250 days used for initial calibration)

**Descriptive statistics:**

| Period | Obs | Mean (%) | Std Dev (%) | Min (%) | Max (%) | Skewness | Ex. Kurtosis |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Full Sample (2018–2024) | 1,759 | 0.045 | 1.248 | −12.765 | 8.968 | −0.816 | 14.415 |
| Pre-COVID (2018–2019) | 502 | 0.036 | 0.944 | −4.184 | 4.840 | −0.612 | 3.641 |
| COVID Crisis (2020) | 253 | 0.060 | 2.185 | −12.765 | 8.968 | −0.866 | 8.507 |
| Post-COVID Bull (2021) | 252 | 0.095 | 0.826 | −2.601 | 2.351 | −0.369 | 0.698 |
| Rate Hike Bear (2022) | 251 | −0.086 | 1.524 | −4.420 | 5.395 | −0.009 | 0.336 |
| Recovery (2023–2024) | 501 | 0.086 | 0.811 | −3.043 | 2.498 | −0.285 | 0.734 |

The full-sample excess kurtosis of **14.41** and Jarque–Bera statistic of **15,424.4 (p < 0.0001)** confirm severe non-normality. Negative skewness (−0.816) reflects the well-documented leverage effect in equity returns.

---

## Methodology

### VaR Models

**1. Historical Simulation (HS)**
Uses the empirical (1−α)-th percentile of the trailing 250-day return distribution.
No distributional assumption — captures fat tails, skew, and clustering automatically.
Weakness: lags during regime shifts until the window fills with new data.

**2. Parametric (Normal) VaR**
Assumes returns are normally distributed. Estimates μ and σ from the trailing 250-day window daily.
Fast and interpretable, but severely underestimates tail risk — by design.

**3. Student-t VaR**
Adds a degrees-of-freedom parameter ν, estimated by maximum likelihood daily, to explicitly model fat tails.
Flexible tail thickness; ν is re-estimated every day on the rolling window.

### Walk-Forward Design

Every model is **recalibrated daily** on the previous 250 trading days and tested on the *next* day's return. This gives 1,509 out-of-sample forecasts per model. No look-ahead bias. Each difference in results traces back to model design, not data advantage.

### Backtesting Tests

**Kupiec Proportion of Failures (POF) Test** — Tests whether the observed violation rate equals the theoretical rate (H₀: p̂ = 1−α). Follows χ²(1) under H₀.

**Christoffersen Conditional Coverage Test** — Tests both unconditional coverage *and* violation independence (clustering). Follows χ²(2) under H₀. A model can pass Kupiec but fail Christoffersen if violations cluster in time.

**Basel Traffic Light Test** — Classifies models into Green (0–4 violations), Yellow (5–9), or Red (≥10) zones based on violation count over 250 days at 99% confidence.

---

## Results

### Kupiec Test (T = 1,509 out-of-sample days)

| Model | Confidence | Violations (N) | Expected | p̂ (%) | LR Statistic | p-value | Decision |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Historical Simulation | 95% | 71 | 75.5 | 4.71 | 0.282 | 0.596 | PASS |
| Parametric (Normal) | 95% | 78 | 75.5 | 5.17 | 0.090 | 0.764 | PASS |
| Student-t | 95% | 88 | 75.5 | 5.83 | 2.091 | 0.148 | PASS |
| Historical Simulation | 99% | 26 | 15.1 | 1.72 | 6.551 | 0.010 | **REJECT*** |
| Parametric (Normal) | 99% | 44 | 15.1 | 2.92 | 36.917 | <0.0001 | **REJECT***\*\* |
| Student-t | 99% | 28 | 15.1 | 1.86 | 8.910 | 0.003 | **REJECT**** |

All models pass at 95%. All fail at 99% — Parametric Normal fails by the widest margin.

### Christoffersen Conditional Coverage Test

| Model | Confidence | π₀₁ (%) | π₁₁ (%) | LR Ind. (p) | LR CC (p) | Independence | Cond. Coverage |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Historical Simulation | 95% | 4.24 | 14.08 | 9.989 (0.002) | 10.270 (0.006) | REJECT | REJECT |
| Parametric (Normal) | 95% | 4.69 | 14.10 | 9.526 (0.002) | 9.616 (0.008) | REJECT | REJECT |
| Student-t | 95% | 5.28 | 14.77 | 10.008 (0.002) | 12.099 (0.002) | REJECT | REJECT |
| Historical Simulation | 99% | 1.55 | 11.54 | 6.834 (0.009) | 13.386 (0.001) | REJECT | REJECT |
| Parametric (Normal) | 99% | 2.73 | 9.09 | 4.017 (0.045) | 40.934 (<0.0001) | REJECT | REJECT |
| Student-t | 99% | 1.76 | 7.14 | 2.593 (0.107) | 11.502 (0.003) | **PASS** | REJECT |

π₁₁ is 3× higher than π₀₁ across all models — violations cluster heavily. Student-t passes independence at 99% but still fails joint coverage.

### Basel Traffic Light Test (Trailing 250 Days, 2024)

| Model | Violations | Expected | Zone | Capital Multiplier |
|:---|:---:|:---:|:---:|:---:|
| Historical Simulation | 6 | 2.5 | **Yellow** | 3.50× |
| Parametric (Normal) | 6 | 2.5 | **Yellow** | 3.50× |
| Student-t | 5 | 2.5 | **Yellow** | 3.40× |

No model reaches Green — even in 2024, which was not an abnormally volatile year.

### Subperiod Analysis (99% VaR Violations)

| Period | Obs | Expected | HS Violations | Normal Violations | Student-t Violations |
|:---|:---:|:---:|:---:|:---:|:---:|
| Pre-COVID (2019) | 252 | 2.5 | 1 (−60%) | 4 (+59%) | 1 (−60%) |
| COVID Crisis (2020) | 253 | 2.5 | 8 (+216%) | 14 (+453%) | 8 (+216%) |
| Post-COVID Bull (2021) | 252 | 2.5 | 1 (−60%) | 3 (+19%) | 1 (−60%) |
| Rate Hike Bear (2022) | 251 | 2.5 | 10 (+298%) | 17 (+577%) | 13 (+418%) |
| Recovery (2023–2024) | 501 | 5.0 | 6 (+20%) | 6 (+20%) | 5 (0%) |

**Surprise finding:** The 2022 rate-hike bear market produced *more* proportional excess violations than COVID — because fixed windows absorb sudden shocks quickly but lag behind slow, grinding regime shifts.

---

## Key Findings

**1. All models fail at 99% — but not equally.**
Parametric Normal is catastrophically worse (LR = 36.92) versus Historical Simulation (6.55) and Student-t (8.91). At 95%, all three pass comfortably.

**2. Violation clustering is universal.**
Every model fails Christoffersen independence at 95%. Only Student-t barely passes at 99% — and even that is insufficient because joint coverage still fails. Clustering during stress is a structural problem with fixed-window VaR, not a distributional assumption issue.

**3. Slow regime shifts are harder than sudden shocks.**
The 2022 rate-hiking bear market caused more excess violations than the sharper COVID crash. A fixed 250-day window absorbs a spike in days; a slow regime change takes months to filter through.

**4. None of the models are Basel Green in 2024.**
Even during a calm year, all three land in the Yellow zone. This is an operational concern for any firm using these models without a regime-detection or volatility overlay.

**5. Walk-forward design matters.**
Static, full-sample backtests would tell a meaningfully different story. Most published work still uses static calibration. The walk-forward methodology here is more demanding, more honest, and more aligned with how regulatory validation should work.

---

## SR 11-7 and SR 26-2 Implications

This study sits squarely in the **SR 11-7** era (2011–April 2026), which required independent validation, ongoing monitoring, and regular backtesting for all quantitative models used in capital calculation. The results feed directly into SR 11-7 model risk management requirements:

- Parametric Normal VaR's failure mode must be documented in validation records
- Violation clustering (Table 5) must be investigated and explained — not just counted
- Subperiod backtesting (Table 7) should be standard, not optional, in validation suites
- Basel Yellow zone outcomes require documented management response

The **April 2026 switch to SR 26-2** retains independent validation and backtesting as core requirements but shifts toward materiality-proportionate oversight. For high-capital models, the bar remains unchanged.

---

## Toward AI-Augmented VaR

The structural failure mode identified here — slow regime transitions overwhelming fixed-window estimators — motivates a specific research direction: the **Korvane ML-LiqVaR framework** (Neupane, forthcoming). It combines:

- **GARCH-Markov Switching** — regime detection before the window catches up
- **XGBoost** — nonlinear macro-variable relationships
- **LSTM** — violation clustering patterns over time
- **SHAP explainability** — interpretable forecasts for regulatory review under SR 26-2

The walk-forward three-test methodology established in this paper serves as the validation baseline for ML-LiqVaR.

---

## Citation

```
Neupane, N. (2026). Backtesting value-at-risk models under SR 11-7:
A comparative analysis of Kupiec, Christoffersen, and Basel Traffic-Light
tests applied to S&P 500 returns (2018–2024).
Korvane Research Series No. 1.
```

---

## References

- Artzner, P., Delbaen, F., Eber, J. M., & Heath, D. (1999). Coherent measures of risk. *Mathematical Finance*, 9(3), 203–228.
- Basel Committee on Banking Supervision. (1996). *Supervisory framework for the use of backtesting.* BIS.
- Basel Committee on Banking Supervision. (2019). *Minimum capital requirements for market risk.* BIS.
- Christoffersen, P. F. (1998). Evaluating interval forecasts. *International Economic Review*, 39(4), 841–862.
- Federal Reserve, OCC, & FDIC. (2011). *Supervisory guidance on model risk management (SR 11-7).*
- Federal Reserve, OCC, & FDIC. (2026). *Revised guidance on model risk management (SR 26-2).*
- Halilbegovic, S., Celebic, N., Arapovic, A., & Vehabovic, M. (2019). Back-testing the effectiveness of value at risk model. *Romanian Journal of Economics*, 48(1), 5–33.
- Jorion, P. (2006). *Value at risk: The new benchmark for managing financial risk* (3rd ed.). McGraw-Hill.
- Kupiec, P. H. (1995). Techniques for verifying the accuracy of risk measurement models. *Journal of Derivatives*, 3(2), 73–84.
- McNeil, A. J., Frey, R., & Embrechts, P. (2015). *Quantitative risk management* (Revised ed.). Princeton University Press.
- Zhang, Y., & Nadarajah, S. (2017). A review of backtesting for value at risk. *Communications in Statistics*, 46(22). https://doi.org/10.1080/03610926.2017.1361984

---

<div align="center">

**Niraj Neupane**
Quantitative Developer · Founder, Korvane & Calderyn Institute
MS Financial Economics · University of Wisconsin–Madison
Chartered Accountant (ICAI) · FRM Candidate

[github.com/nirajneupane17](https://github.com/nirajneupane17)

</div>
