# NOAA Experiment Log

## Experiment Scope
- Date range: `20250301` to `20250320`
- Product: `water_level`
- Stations: `9414290 (San Francisco), 8518750 (The Battery), 9447130 (Seattle)`
- Goal: test whether the current best models remain strong under rolling-origin validation and across multiple stations.

## Experiment 1: Rolling-Origin Backtest (San Francisco, 4h series)
- Series: 4-hour mean water level
- Horizon: 48 hours per fold
- Folds: 5
- Compared models: Seasonal Naive, AutoReg(12), SARIMA

### Fold-Level Results
|   station_id | station_name   |   fold |   train_points |   test_points | model                       |   rmse |    mae |
|-------------:|:---------------|-------:|---------------:|--------------:|:----------------------------|-------:|-------:|
|      9414290 | San Francisco  |      1 |             60 |            12 | AutoReg 4h lags=12          | 0.184  | 0.1202 |
|      9414290 | San Francisco  |      1 |             60 |            12 | SARIMA 4h (2,0,1)x(1,0,0,3) | 0.243  | 0.1659 |
|      9414290 | San Francisco  |      1 |             60 |            12 | Seasonal Naive 4h           | 0.5701 | 0.532  |
|      9414290 | San Francisco  |      2 |             72 |            12 | AutoReg 4h lags=12          | 0.1581 | 0.133  |
|      9414290 | San Francisco  |      2 |             72 |            12 | SARIMA 4h (2,0,1)x(1,0,0,3) | 0.2134 | 0.1765 |
|      9414290 | San Francisco  |      2 |             72 |            12 | Seasonal Naive 4h           | 0.2915 | 0.2672 |
|      9414290 | San Francisco  |      3 |             84 |            12 | Seasonal Naive 4h           | 0.1572 | 0.1236 |
|      9414290 | San Francisco  |      3 |             84 |            12 | AutoReg 4h lags=12          | 0.1576 | 0.1276 |
|      9414290 | San Francisco  |      3 |             84 |            12 | SARIMA 4h (2,0,1)x(1,0,0,3) | 0.2412 | 0.1796 |
|      9414290 | San Francisco  |      4 |             96 |            12 | AutoReg 4h lags=12          | 0.1185 | 0.0967 |
|      9414290 | San Francisco  |      4 |             96 |            12 | SARIMA 4h (2,0,1)x(1,0,0,3) | 0.2266 | 0.1854 |
|      9414290 | San Francisco  |      4 |             96 |            12 | Seasonal Naive 4h           | 0.3979 | 0.3577 |
|      9414290 | San Francisco  |      5 |            108 |            12 | AutoReg 4h lags=12          | 0.0513 | 0.0471 |
|      9414290 | San Francisco  |      5 |            108 |            12 | SARIMA 4h (2,0,1)x(1,0,0,3) | 0.1737 | 0.1439 |
|      9414290 | San Francisco  |      5 |            108 |            12 | Seasonal Naive 4h           | 0.5643 | 0.4815 |

### Mean Performance By Model
| model                       |   rmse |    mae |
|:----------------------------|-------:|-------:|
| AutoReg 4h lags=12          | 0.1339 | 0.1049 |
| SARIMA 4h (2,0,1)x(1,0,0,3) | 0.2196 | 0.1702 |
| Seasonal Naive 4h           | 0.3962 | 0.3524 |

## Experiment 1B: Cross-Frequency Rolling Backtest (San Francisco)
- Models compared: top AutoReg candidates from the search report
- Horizon: 48 hours per fold
- Folds: 5

### Fold-Level Results
|   station_id | station_name   | freq_rule   |   fold |   train_points |   test_points | model                 |   rmse |    mae |
|-------------:|:---------------|:------------|-------:|---------------:|--------------:|:----------------------|-------:|-------:|
|      9414290 | San Francisco  | 1h          |      1 |            240 |            48 | AutoReg 1h lags=48    | 0.2089 | 0.1498 |
|      9414290 | San Francisco  | 1h          |      2 |            288 |            48 | AutoReg 1h lags=48    | 0.1582 | 0.1232 |
|      9414290 | San Francisco  | 1h          |      3 |            336 |            48 | AutoReg 1h lags=48    | 0.1623 | 0.1366 |
|      9414290 | San Francisco  | 1h          |      4 |            384 |            48 | AutoReg 1h lags=48    | 0.1196 | 0.0979 |
|      9414290 | San Francisco  | 1h          |      5 |            432 |            48 | AutoReg 1h lags=48    | 0.0542 | 0.0427 |
|      9414290 | San Francisco  | 30min       |      1 |            480 |            96 | AutoReg 30min lags=96 | 0.2033 | 0.1441 |
|      9414290 | San Francisco  | 30min       |      2 |            576 |            96 | AutoReg 30min lags=96 | 0.1613 | 0.1251 |
|      9414290 | San Francisco  | 30min       |      3 |            672 |            96 | AutoReg 30min lags=96 | 0.1636 | 0.1378 |
|      9414290 | San Francisco  | 30min       |      4 |            768 |            96 | AutoReg 30min lags=96 | 0.1196 | 0.0981 |
|      9414290 | San Francisco  | 30min       |      5 |            864 |            96 | AutoReg 30min lags=96 | 0.0517 | 0.04   |
|      9414290 | San Francisco  | 4h          |      1 |             60 |            12 | AutoReg 4h lags=12    | 0.184  | 0.1202 |
|      9414290 | San Francisco  | 4h          |      2 |             72 |            12 | AutoReg 4h lags=12    | 0.1581 | 0.133  |
|      9414290 | San Francisco  | 4h          |      3 |             84 |            12 | AutoReg 4h lags=12    | 0.1576 | 0.1276 |
|      9414290 | San Francisco  | 4h          |      4 |             96 |            12 | AutoReg 4h lags=12    | 0.1185 | 0.0967 |
|      9414290 | San Francisco  | 4h          |      5 |            108 |            12 | AutoReg 4h lags=12    | 0.0513 | 0.0471 |

### Mean Performance By Model
| model                 |   rmse |    mae |
|:----------------------|-------:|-------:|
| AutoReg 4h lags=12    | 0.1339 | 0.1049 |
| AutoReg 30min lags=96 | 0.1399 | 0.109  |
| AutoReg 1h lags=48    | 0.1407 | 0.1101 |

## Experiment 2: Station Generalization
- Holdout: last 48 hours at each model frequency
- Compared candidate models from the previous search report

### Station-Level Results
|   station_id | station_name   | freq_rule   |   test_points | model                       |   rmse |    mae |
|-------------:|:---------------|:------------|--------------:|:----------------------------|-------:|-------:|
|      9414290 | San Francisco  | 4h          |            12 | AutoReg 4h lags=12          | 0.0513 | 0.0471 |
|      9414290 | San Francisco  | 30min       |            96 | AutoReg 30min lags=96       | 0.0517 | 0.04   |
|      9414290 | San Francisco  | 1h          |            48 | AutoReg 1h lags=48          | 0.0542 | 0.0427 |
|      9414290 | San Francisco  | 4h          |            12 | SARIMA 4h (2,0,1)x(1,0,0,3) | 0.1737 | 0.1439 |
|      9414290 | San Francisco  | 4h          |            12 | Seasonal Naive 4h           | 0.5643 | 0.4815 |
|      9447130 | Seattle        | 1h          |            48 | AutoReg 1h lags=48          | 0.1789 | 0.1366 |
|      9447130 | Seattle        | 30min       |            96 | AutoReg 30min lags=96       | 0.1798 | 0.1375 |
|      9447130 | Seattle        | 4h          |            12 | AutoReg 4h lags=12          | 0.2059 | 0.1553 |
|      9447130 | Seattle        | 4h          |            12 | SARIMA 4h (2,0,1)x(1,0,0,3) | 0.3311 | 0.2563 |
|      9447130 | Seattle        | 4h          |            12 | Seasonal Naive 4h           | 1.2292 | 1.063  |
|      8518750 | The Battery    | 4h          |            12 | AutoReg 4h lags=12          | 0.1618 | 0.1329 |
|      8518750 | The Battery    | 1h          |            48 | AutoReg 1h lags=48          | 0.1697 | 0.1412 |
|      8518750 | The Battery    | 30min       |            96 | AutoReg 30min lags=96       | 0.1722 | 0.1444 |
|      8518750 | The Battery    | 4h          |            12 | Seasonal Naive 4h           | 0.2105 | 0.187  |
|      8518750 | The Battery    | 4h          |            12 | SARIMA 4h (2,0,1)x(1,0,0,3) | 0.2186 | 0.1778 |

### Mean Performance Across Stations
| model                       |   rmse |    mae |
|:----------------------------|-------:|-------:|
| AutoReg 1h lags=48          | 0.1343 | 0.1069 |
| AutoReg 30min lags=96       | 0.1346 | 0.1073 |
| AutoReg 4h lags=12          | 0.1397 | 0.1117 |
| SARIMA 4h (2,0,1)x(1,0,0,3) | 0.2411 | 0.1927 |
| Seasonal Naive 4h           | 0.668  | 0.5772 |

### Best Model Per Station
| station_name   | model              | freq_rule   |   rmse |    mae |
|:---------------|:-------------------|:------------|-------:|-------:|
| San Francisco  | AutoReg 4h lags=12 | 4h          | 0.0513 | 0.0471 |
| The Battery    | AutoReg 4h lags=12 | 4h          | 0.1618 | 0.1329 |
| Seattle        | AutoReg 1h lags=48 | 1h          | 0.1789 | 0.1366 |

## Current Interpretation
- Rolling-origin backtest winner: `AutoReg 4h lags=12`
- Cross-frequency rolling winner: `AutoReg 4h lags=12`
- Cross-station mean RMSE winner: `AutoReg 1h lags=48`
- If the rolling and cross-station winners differ, prefer the model that is easier to explain and stable across folds.

## Next Candidates
- Add rolling-origin backtest results to the Colab notebook summary.
- Check one more station in a different tidal regime if generalization is still unclear.
- Compare recursive AutoReg with direct-horizon regression if more experimentation is needed.
