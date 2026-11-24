# NOAA Tide Water Level Forecasting

NOAA 관측소의 **조위(water level) 시계열을 48시간 앞까지 예측**하고, 여러 모델을 롤링 오리진 백테스트로 비교한 프로젝트입니다.

한 번 나눈 학습·평가에서 좋아 보이는 모델이 실제로도 강한지 확인하는 데 초점을 맞췄습니다. 학습 구간을 넓혀 가며 다섯 번 다시 평가하고, 리샘플링 주기와 관측소를 바꿔도 결론이 유지되는지 봤습니다.

## 결과

San Francisco 관측소 4시간 평균 계열, 예측 지평 48시간, 5-fold 롤링 오리진 백테스트.

| 모델 | RMSE | MAE |
| --- | --- | --- |
| **AutoReg (4h, lags=12)** | **0.1339** | **0.1049** |
| SARIMA (2,0,1)x(1,0,0,3) | 0.2196 | 0.1702 |
| Seasonal Naive | 0.3962 | 0.3524 |

AutoReg가 Seasonal Naive 대비 **RMSE 66% 감소**. SARIMA보다도 일관되게 우수했습니다.

## 리샘플링 주기 비교

같은 모델군을 30분 / 1시간 / 4시간 세 가지 주기로 비교했습니다.

| 모델 | RMSE | MAE |
| --- | --- | --- |
| AutoReg 4h lags=12 | 0.1339 | 0.1049 |
| AutoReg 30min lags=96 | 0.1399 | 0.1090 |
| AutoReg 1h lags=48 | 0.1407 | 0.1101 |

세 주기 모두 성능이 거의 같습니다. **더 조밀한 샘플링이 예측 정확도를 올리지 않았습니다.** 4시간 계열은 학습 데이터가 1/8 수준인데도 같은 성능을 내므로 연산 비용 면에서 유리합니다.

## 관측소 일반화

한 관측소의 결과가 우연이 아닌지 확인하려고 3개 관측소로 넓혔습니다.

- 9414290 San Francisco
- 8518750 The Battery
- 9447130 Seattle

결과는 [`noaa_station_generalization_results.csv`](noaa_station_generalization_results.csv)에 있습니다.

## 실험 설계

- 기간: 2025-03-01 ~ 2025-03-20
- Product: `water_level` (NOAA CO-OPS API, 6분 간격)
- 예측 지평: fold당 48시간
- Fold: 5 (롤링 오리진, 학습 구간을 누적 확장)

## 파일

```
noaa_tide_forecasting.ipynb              최종 분석 노트북
analysis_summary.md                      분석 정리 (데이터 선택 이유, 분석 흐름, 결론)
dataset_recommendations.md               데이터 선정 기록
noaa_model_search.py / .md               모델 탐색 자동화와 결과 정리
noaa_experiment_log.py / .md             롤링 백테스트·관측소 확장 실험 로그
noaa_model_search_results.csv            모델 탐색 결과
noaa_rolling_backtest_results.csv        롤링 백테스트 fold별 결과
noaa_cross_frequency_rolling_results.csv 리샘플링 주기 비교
noaa_station_generalization_results.csv  관측소 일반화 결과
02_noaa_tides_water_level_colab.ipynb    첫 수집·탐색 노트북
noaa_tides*.ipynb, analysis.ipynb        실험 반복본
01_fred_unrate_forecasting_colab.ipynb   같은 분석 흐름을 FRED 실업률 데이터에 적용한 노트북
```

## 기술 스택

statsmodels (AutoReg · SARIMA) · Pandas · NOAA CO-OPS API · Python
