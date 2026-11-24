# NOAA 조위 예측 분석 정리

## 1. 주제
- 주제: NOAA 조위(`water_level`) 데이터를 이용한 시계열 분석 및 예측
- 관측소: `9414290` (San Francisco)
- 데이터 출처: NOAA Tides & Currents API
- 엔드포인트: `https://api.tidesandcurrents.noaa.gov/api/prod/datagetter`

## 2. 데이터 선택 이유
- 서비스키 없이 바로 호출할 수 있다.
- 6분 간격 시계열이다.
- 조위 데이터는 반일주조 패턴이 나타난다.

## 3. 분석 흐름
1. NOAA API에서 조위 데이터를 직접 수집한다.
2. 6분 간격 시계열을 정리하고 결측을 보간한다.
3. 전체 시계열, 최근 구간, 시간 평균, 일별 요약, 평균 조석 패턴을 시각화한다.
4. `STL`, `ACF`, `PACF`로 반복 구조를 확인한다.
5. `Seasonal Naive`, `AutoReg`, `SARIMA`를 비교한다.

## 4. 실험 기록 요약

### 4-1. 단일 탐색 결과
- 탐색 파일: [noaa_model_search.md](noaa_model_search.md)
- 탐색 범위: `30min`, `1h`, `90min`, `2h`, `3h`, `4h` 집계 시계열
- 비교 모델: `Seasonal Naive`, `AutoReg`, `SARIMA`, `ETS`
- 동일 조건: 마지막 `48시간` holdout
- 단일 탐색 최적: `AutoReg 4h lags=12`
- 성능: `RMSE=0.0513`, `MAE=0.0471`

### 4-2. Rolling-origin backtest
- 기록 파일: [noaa_experiment_log.md](noaa_experiment_log.md)
- 설정: San Francisco, `4h` 시계열, 48시간 horizon, 5 folds
- 평균 성능:
  - `AutoReg 4h lags=12`: `RMSE=0.1339`, `MAE=0.1049`
  - `SARIMA 4h (2,0,1)x(1,0,0,3)`: `RMSE=0.2196`, `MAE=0.1702`
  - `Seasonal Naive 4h`: `RMSE=0.3962`, `MAE=0.3524`
- 최저 오차 모델: `AutoReg 4h lags=12`

### 4-3. Cross-frequency rolling 비교
- 비교 후보: `AutoReg 30min lags=96`, `AutoReg 1h lags=48`, `AutoReg 4h lags=12`
- 설정: San Francisco, 48시간 horizon, 5 folds
- 평균 성능:
  - `AutoReg 4h lags=12`: `RMSE=0.1339`, `MAE=0.1049`
  - `AutoReg 30min lags=96`: `RMSE=0.1399`, `MAE=0.1090`
  - `AutoReg 1h lags=48`: `RMSE=0.1407`, `MAE=0.1101`
- 최저 오차 모델: `AutoReg 4h lags=12`

### 4-4. 관측소 일반화 확인
- 관측소: `San Francisco`, `The Battery`, `Seattle`
- 비교 후보:
  - `AutoReg 30min lags=96`
  - `AutoReg 1h lags=48`
  - `AutoReg 4h lags=12`
  - `SARIMA 4h (2,0,1)x(1,0,0,3)`
  - `Seasonal Naive 4h`
- 평균 성능:
  - `AutoReg 1h lags=48`: `RMSE=0.1343`, `MAE=0.1069`
  - `AutoReg 30min lags=96`: `RMSE=0.1346`, `MAE=0.1073`
  - `AutoReg 4h lags=12`: `RMSE=0.1397`, `MAE=0.1117`
- 해석:
  - 관측소 평균 기준 최저 오차 모델은 `1h AutoReg lags=48`이다.
  - rolling-origin과 cross-frequency rolling 기준 최저 오차 모델은 `4h AutoReg lags=12`이다.

## 5. 최종 선택 모델
- 최종 기본 모델: `AutoReg 4h lags=12`

## 6. 최종 선택 이유
- 단일 탐색에서 최적이었다.
- rolling-origin backtest에서 가장 낮은 평균 오차를 기록했다.
- cross-frequency rolling 비교에서도 가장 낮은 평균 오차를 기록했다.

## 7. 보조 해석
- 다중 관측소 평균에서는 `1h AutoReg lags=48`이 가장 낮은 오차를 기록했다.
- 현재 실험 범위에서는 `4h AutoReg lags=12`가 단일 탐색, rolling-origin, cross-frequency rolling에서 모두 앞섰다.

## 8. 산출물 구성
- 데이터 선정 문서: [dataset_recommendations.md](dataset_recommendations.md)
- 첫 수집 · 탐색 노트북: [02_noaa_tides_water_level_colab.ipynb](02_noaa_tides_water_level_colab.ipynb)
- 모델 탐색 리포트: [noaa_model_search.md](noaa_model_search.md)
- 추가 실험 로그: [noaa_experiment_log.md](noaa_experiment_log.md)

## 9. 한계
- 분석 기간이 `2025-03-01` ~ `2025-03-20`으로 짧다.
- 관측소 수가 3개라 일반화 판단에는 제한이 있다.
- 서로 다른 집계 주파수 비교에서는 더 부드러운 시계열이 유리할 수 있다.

## 10. 결론
- 최종 분석은 `NOAA Tides & Currents`의 조위 데이터를 사용하는 것으로 정리한다.
- 실험 결과를 종합하면, 기본 예측 모델은 `AutoReg 4h lags=12`가 가장 적절하다.
- 이 선택은 단일 탐색, rolling-origin backtest, cross-frequency rolling 결과를 반영한 결론이다.
