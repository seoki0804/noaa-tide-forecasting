# 해양 시계열 데이터 선정 결과

## 선정 기준
- 서비스키 없이 바로 호출 가능
- Colab에서 인증 없이 재현 가능
- 기존 실습과 같은 분석 흐름 적용 가능

## 최종 선택
- 데이터: `NOAA Tides & Currents - water_level`
- 관측소: `9414290` (San Francisco)
- 호출 방식: 공식 API 직접 호출
- 주기: 6분 간격
- 단위: meter

## 선택 근거
- `00_OpenMeteo_HourlyWeather_Seoul_Busan_NewYork.ipynb`는 `공개 API -> 시간 인덱스 정리 -> STL/ACF -> Seasonal Naive` 흐름을 사용한다.
- `00_OPSD_TimeSeries_Energy_DE.ipynb`는 `고빈도 시계열 -> 집계 시각화 -> 마지막 구간 테스트` 흐름을 사용한다.
- `NOAA water_level`은 같은 흐름을 그대로 적용할 수 있다.
- 조위 데이터는 반일주조 패턴이 뚜렷하다.

## 선정 방향
- 주제: 샌프란시스코 조위 시계열 분석
- 데이터 수집: NOAA API 직접 호출
- 분석 순서: 원시 시계열 확인 -> 재집계 시각화 -> STL / ACF / PACF -> Seasonal Naive -> AutoReg / SARIMA 비교
