from __future__ import annotations

import math
import warnings
from pathlib import Path

import pandas as pd
import requests
from sklearn.metrics import mean_absolute_error, mean_squared_error
from statsmodels.tools.sm_exceptions import ConvergenceWarning
from statsmodels.tsa.ar_model import AutoReg
from statsmodels.tsa.statespace.sarimax import SARIMAX


warnings.filterwarnings("ignore", category=ConvergenceWarning)
warnings.filterwarnings("ignore", category=UserWarning)

BASE_URL = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
OUTPUT_DIR = Path(__file__).resolve().parent
MD_PATH = OUTPUT_DIR / "noaa_experiment_log.md"
ROLLING_CSV = OUTPUT_DIR / "noaa_rolling_backtest_results.csv"
STATION_CSV = OUTPUT_DIR / "noaa_station_generalization_results.csv"
CROSS_FREQ_ROLLING_CSV = OUTPUT_DIR / "noaa_cross_frequency_rolling_results.csv"

BEGIN_DATE = "20250301"
END_DATE = "20250320"
PRODUCT = "water_level"
DATUM = "MLLW"
TIME_ZONE = "lst_ldt"
UNITS = "metric"

STATIONS = {
    "9414290": "San Francisco",
    "8518750": "The Battery",
    "9447130": "Seattle",
}


def fetch_series(station_id: str) -> pd.Series:
    params = {
        "product": PRODUCT,
        "application": "TimeSeriesAnalysis",
        "begin_date": BEGIN_DATE,
        "end_date": END_DATE,
        "station": station_id,
        "datum": DATUM,
        "time_zone": TIME_ZONE,
        "units": UNITS,
        "format": "json",
    }
    response = requests.get(BASE_URL, params=params, timeout=30)
    response.raise_for_status()
    payload = response.json()
    if "data" not in payload:
        raise ValueError(f"API response does not contain data: {payload}")

    df = pd.DataFrame(payload["data"]).copy()
    df["t"] = pd.to_datetime(df["t"], errors="coerce")
    df["v"] = pd.to_numeric(df["v"], errors="coerce").astype("float32")
    series = (
        df.dropna(subset=["t", "v"])
        .set_index("t")["v"]
        .sort_index()
        .asfreq("6min")
        .interpolate(limit_direction="both")
        .astype("float32")
    )
    return series


def score(y_true: pd.Series, y_pred: pd.Series) -> tuple[float, float]:
    rmse = math.sqrt(mean_squared_error(y_true, y_pred))
    mae = mean_absolute_error(y_true, y_pred)
    return rmse, mae


def predict_seasonal_naive(y: pd.Series, horizon: int, lag_steps: int) -> pd.Series:
    test = y.iloc[-horizon:]
    pred = pd.Series(index=test.index, dtype="float64")
    freq = y.index[1] - y.index[0]
    for timestamp in test.index:
        lagged_time = timestamp - (freq * lag_steps)
        if lagged_time in y.index:
            pred.loc[timestamp] = y.loc[lagged_time]
    return pred


def predict_autoreg(train: pd.Series, test_index: pd.Index, lags: int, seasonal: bool = False, period: int | None = None) -> pd.Series:
    model = AutoReg(train, lags=lags, old_names=False, seasonal=seasonal, period=period if seasonal else None).fit()
    pred = model.predict(start=len(train), end=len(train) + len(test_index) - 1, dynamic=False)
    pred.index = test_index
    return pred


def predict_sarima(train: pd.Series, test_index: pd.Index, order: tuple[int, int, int], seasonal_order: tuple[int, int, int, int]) -> pd.Series:
    model = SARIMAX(
        train,
        order=order,
        seasonal_order=seasonal_order,
        enforce_stationarity=False,
        enforce_invertibility=False,
    ).fit(disp=False)
    pred = model.forecast(len(test_index))
    pred.index = test_index
    return pred


def rolling_origin_backtest() -> pd.DataFrame:
    station_id = "9414290"
    y = fetch_series(station_id).resample("4h").mean().astype("float32")
    horizon = 12  # 48 hours at 4h frequency
    n_folds = 5
    initial_train = len(y) - horizon * n_folds
    rows: list[dict] = []

    for fold in range(n_folds):
        train_end = initial_train + fold * horizon
        train = y.iloc[:train_end]
        test = y.iloc[train_end:train_end + horizon]

        preds = {
            "Seasonal Naive 4h": predict_seasonal_naive(pd.concat([train, test]), horizon=horizon, lag_steps=3),
            "AutoReg 4h lags=12": predict_autoreg(train, test.index, lags=12, seasonal=False),
            "SARIMA 4h (2,0,1)x(1,0,0,3)": predict_sarima(train, test.index, order=(2, 0, 1), seasonal_order=(1, 0, 0, 3)),
        }

        for model_name, pred in preds.items():
            rmse, mae = score(test, pred)
            rows.append(
                {
                    "station_id": station_id,
                    "station_name": STATIONS[station_id],
                    "fold": fold + 1,
                    "train_points": len(train),
                    "test_points": len(test),
                    "model": model_name,
                    "rmse": rmse,
                    "mae": mae,
                }
            )
    return pd.DataFrame(rows)


def cross_frequency_rolling_backtest() -> pd.DataFrame:
    station_id = "9414290"
    base = fetch_series(station_id)
    candidates = [
        {"model": "AutoReg 30min lags=96", "rule": "30min", "lags": 96},
        {"model": "AutoReg 1h lags=48", "rule": "1h", "lags": 48},
        {"model": "AutoReg 4h lags=12", "rule": "4h", "lags": 12},
    ]
    rows: list[dict] = []

    for candidate in candidates:
        y = base.resample(candidate["rule"]).mean().astype("float32")
        step_hours = pd.Timedelta(candidate["rule"]).total_seconds() / 3600
        horizon = int(round(48 / step_hours))
        n_folds = 5
        initial_train = len(y) - horizon * n_folds

        for fold in range(n_folds):
            train_end = initial_train + fold * horizon
            train = y.iloc[:train_end]
            test = y.iloc[train_end:train_end + horizon]
            pred = predict_autoreg(train, test.index, lags=candidate["lags"], seasonal=False)
            rmse, mae = score(test, pred)
            rows.append(
                {
                    "station_id": station_id,
                    "station_name": STATIONS[station_id],
                    "freq_rule": candidate["rule"],
                    "fold": fold + 1,
                    "train_points": len(train),
                    "test_points": len(test),
                    "model": candidate["model"],
                    "rmse": rmse,
                    "mae": mae,
                }
            )
    return pd.DataFrame(rows)


def station_generalization() -> pd.DataFrame:
    candidates = [
        {"model": "Seasonal Naive 4h", "rule": "4h", "kind": "naive", "lag_steps": 3},
        {"model": "AutoReg 4h lags=12", "rule": "4h", "kind": "autoreg", "lags": 12, "seasonal": False},
        {"model": "AutoReg 1h lags=48", "rule": "1h", "kind": "autoreg", "lags": 48, "seasonal": False},
        {"model": "AutoReg 30min lags=96", "rule": "30min", "kind": "autoreg", "lags": 96, "seasonal": False},
        {"model": "SARIMA 4h (2,0,1)x(1,0,0,3)", "rule": "4h", "kind": "sarima", "order": (2, 0, 1), "seasonal_order": (1, 0, 0, 3)},
    ]
    rows: list[dict] = []

    for station_id, station_name in STATIONS.items():
        base = fetch_series(station_id)
        for candidate in candidates:
            y = base.resample(candidate["rule"]).mean().astype("float32")
            step_hours = pd.Timedelta(candidate["rule"]).total_seconds() / 3600
            horizon = int(round(48 / step_hours))
            train = y.iloc[:-horizon]
            test = y.iloc[-horizon:]

            if candidate["kind"] == "naive":
                pred = predict_seasonal_naive(y, horizon=horizon, lag_steps=candidate["lag_steps"])
            elif candidate["kind"] == "autoreg":
                pred = predict_autoreg(
                    train,
                    test.index,
                    lags=candidate["lags"],
                    seasonal=candidate["seasonal"],
                )
            else:
                pred = predict_sarima(
                    train,
                    test.index,
                    order=candidate["order"],
                    seasonal_order=candidate["seasonal_order"],
                )

            rmse, mae = score(test, pred)
            rows.append(
                {
                    "station_id": station_id,
                    "station_name": station_name,
                    "freq_rule": candidate["rule"],
                    "test_points": len(test),
                    "model": candidate["model"],
                    "rmse": rmse,
                    "mae": mae,
                }
            )
    return pd.DataFrame(rows)


def format_markdown_table(df: pd.DataFrame) -> str:
    view = df.copy()
    for col in ("rmse", "mae"):
        if col in view.columns:
            view[col] = view[col].map(lambda x: f"{x:.4f}")
    return view.to_markdown(index=False)


def write_markdown(rolling_df: pd.DataFrame, cross_freq_df: pd.DataFrame, station_df: pd.DataFrame) -> None:
    rolling_summary = (
        rolling_df.groupby("model", as_index=False)[["rmse", "mae"]]
        .mean()
        .sort_values(["rmse", "mae"])
    )

    cross_freq_summary = (
        cross_freq_df.groupby("model", as_index=False)[["rmse", "mae"]]
        .mean()
        .sort_values(["rmse", "mae"])
    )

    station_summary = (
        station_df.groupby("model", as_index=False)[["rmse", "mae"]]
        .mean()
        .sort_values(["rmse", "mae"])
    )

    station_best = (
        station_df.sort_values(["station_name", "rmse", "mae"])
        .groupby("station_name", as_index=False)
        .first()
        .sort_values(["rmse", "mae"])
    )

    lines = [
        "# NOAA Experiment Log",
        "",
        "## Experiment Scope",
        f"- Date range: `{BEGIN_DATE}` to `{END_DATE}`",
        f"- Product: `{PRODUCT}`",
        f"- Stations: `{', '.join(f'{sid} ({name})' for sid, name in STATIONS.items())}`",
        "- Goal: test whether the current best models remain strong under rolling-origin validation and across multiple stations.",
        "",
        "## Experiment 1: Rolling-Origin Backtest (San Francisco, 4h series)",
        "- Series: 4-hour mean water level",
        "- Horizon: 48 hours per fold",
        "- Folds: 5",
        "- Compared models: Seasonal Naive, AutoReg(12), SARIMA",
        "",
        "### Fold-Level Results",
        format_markdown_table(rolling_df.sort_values(["fold", "rmse"])),
        "",
        "### Mean Performance By Model",
        format_markdown_table(rolling_summary),
        "",
        "## Experiment 1B: Cross-Frequency Rolling Backtest (San Francisco)",
        "- Models compared: top AutoReg candidates from the search report",
        "- Horizon: 48 hours per fold",
        "- Folds: 5",
        "",
        "### Fold-Level Results",
        format_markdown_table(cross_freq_df.sort_values(["model", "fold"])),
        "",
        "### Mean Performance By Model",
        format_markdown_table(cross_freq_summary),
        "",
        "## Experiment 2: Station Generalization",
        "- Holdout: last 48 hours at each model frequency",
        "- Compared candidate models from the previous search report",
        "",
        "### Station-Level Results",
        format_markdown_table(station_df.sort_values(["station_name", "rmse"])),
        "",
        "### Mean Performance Across Stations",
        format_markdown_table(station_summary),
        "",
        "### Best Model Per Station",
        format_markdown_table(station_best[["station_name", "model", "freq_rule", "rmse", "mae"]]),
        "",
        "## Current Interpretation",
        f"- Rolling-origin backtest winner: `{rolling_summary.iloc[0]['model']}`",
        f"- Cross-frequency rolling winner: `{cross_freq_summary.iloc[0]['model']}`",
        f"- Cross-station mean RMSE winner: `{station_summary.iloc[0]['model']}`",
        "- If the rolling and cross-station winners differ, prefer the model that is easier to explain and stable across folds.",
        "",
        "## Next Candidates",
        "- Add rolling-origin backtest results to the Colab notebook summary.",
        "- Check one more station in a different tidal regime if generalization is still unclear.",
        "- Compare recursive AutoReg with direct-horizon regression if more experimentation is needed.",
    ]
    MD_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    rolling_df = rolling_origin_backtest()
    cross_freq_df = cross_frequency_rolling_backtest()
    station_df = station_generalization()
    rolling_df.to_csv(ROLLING_CSV, index=False)
    cross_freq_df.to_csv(CROSS_FREQ_ROLLING_CSV, index=False)
    station_df.to_csv(STATION_CSV, index=False)
    write_markdown(rolling_df, cross_freq_df, station_df)
    print(f"Saved: {ROLLING_CSV}")
    print(f"Saved: {CROSS_FREQ_ROLLING_CSV}")
    print(f"Saved: {STATION_CSV}")
    print(f"Saved: {MD_PATH}")


if __name__ == "__main__":
    main()
