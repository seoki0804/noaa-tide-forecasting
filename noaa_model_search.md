# NOAA Model Search Report

## Setup
- Generated at: `2026-03-24 03:38:18`
- Station: `9414290` (San Francisco)
- Product: `water_level`
- Date range: `20250301` to `20250320`
- Base frequency: `6min`
- Base observations: `4800`
- Test horizon: last `48` hours for every resampled series

## Current Best Overall
- Model: `AutoReg`
- Family: `AutoReg`
- Frequency: `4h`
- Lags: `12`
- Seasonal dummies: `False`
- RMSE: `0.0513`
- MAE: `0.0471`

## Best By Family
| family        | model                        | freq_rule   | lags   | seasonal   |   rmse |    mae |
|:--------------|:-----------------------------|:------------|:-------|:-----------|-------:|-------:|
| AutoReg       | AutoReg                      | 4h          | 12     | False      | 0.0513 | 0.0471 |
| SARIMA        | SARIMA(2, 0, 1)x(1, 0, 0, 3) | 4h          | -      | True       | 0.1737 | 0.1439 |
| ETS           | ETS(add seasonal)            | 4h          | -      | True       | 0.3508 | 0.3159 |
| SeasonalNaive | Seasonal Naive               | 4h          | 3      | False      | 0.5643 | 0.4815 |

## Best By Frequency
| freq_rule   | family   | model   |   lags | seasonal   |   rmse |    mae |
|:------------|:---------|:--------|-------:|:-----------|-------:|-------:|
| 4h          | AutoReg  | AutoReg |     12 | False      | 0.0513 | 0.0471 |
| 30min       | AutoReg  | AutoReg |     96 | False      | 0.0517 | 0.04   |
| 3h          | AutoReg  | AutoReg |     16 | False      | 0.0538 | 0.0475 |
| 1h          | AutoReg  | AutoReg |     48 | False      | 0.0542 | 0.0427 |
| 90min       | AutoReg  | AutoReg |     48 | False      | 0.0567 | 0.0463 |
| 2h          | AutoReg  | AutoReg |     36 | False      | 0.057  | 0.0456 |

## Top 15 Overall
| family   | model   | freq_rule   |   lags | seasonal   |   rmse |    mae |   runtime_sec |
|:---------|:--------|:------------|-------:|:-----------|-------:|-------:|--------------:|
| AutoReg  | AutoReg | 4h          |     12 | False      | 0.0513 | 0.0471 |        0.0012 |
| AutoReg  | AutoReg | 30min       |     96 | False      | 0.0517 | 0.04   |        0.0184 |
| AutoReg  | AutoReg | 4h          |     18 | False      | 0.0519 | 0.0431 |        0.0046 |
| AutoReg  | AutoReg | 30min       |    100 | False      | 0.0521 | 0.0387 |        0.015  |
| AutoReg  | AutoReg | 3h          |     16 | False      | 0.0538 | 0.0475 |        0.0037 |
| AutoReg  | AutoReg | 30min       |    144 | False      | 0.0539 | 0.0426 |        0.0396 |
| AutoReg  | AutoReg | 1h          |     48 | False      | 0.0542 | 0.0427 |        0.0076 |
| AutoReg  | AutoReg | 1h          |     72 | False      | 0.0566 | 0.0461 |        0.01   |
| AutoReg  | AutoReg | 90min       |     48 | False      | 0.0567 | 0.0463 |        0.0043 |
| AutoReg  | AutoReg | 2h          |     36 | False      | 0.057  | 0.0456 |        0.0018 |
| AutoReg  | AutoReg | 3h          |     24 | False      | 0.0579 | 0.0473 |        0.0013 |
| AutoReg  | AutoReg | 2h          |     24 | False      | 0.0581 | 0.0503 |        0.0017 |
| AutoReg  | AutoReg | 90min       |     48 | True       | 0.0585 | 0.0493 |        0.0041 |
| AutoReg  | AutoReg | 1h          |     72 | True       | 0.0589 | 0.0501 |        0.0104 |
| AutoReg  | AutoReg | 3h          |     24 | True       | 0.0589 | 0.0517 |        0.0074 |

## Notes
- RMSE and MAE are in meter units.
- Frequency comparisons use the same 48-hour test horizon, but smoother series may naturally reduce error.
- The current search suggests that long-lag AutoReg models near a 48-hour memory window perform best on this dataset.

## Next Search Candidates
- Test a rolling-origin backtest instead of a single 48-hour holdout.
- Compare direct multi-step forecasting with recursive forecasting.
- Re-run the search on a second station to check whether the best configuration generalizes.
