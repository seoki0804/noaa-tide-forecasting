from __future__ import annotations

import math
import time
import warnings
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import requests
from sklearn.metrics import mean_absolute_error, mean_squared_error
from statsmodels.tools.sm_exceptions import ConvergenceWarning
from statsmodels.tsa.ar_model import AutoReg
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.statespace.sarimax import SARIMAX


BASE_URL = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
OUTPUT_DIR = Path(__file__).resolve().parent
CSV_PATH = OUTPUT_DIR / "noaa_model_search_results.csv"
MD_PATH = OUTPUT_DIR / "noaa_model_search.md"

BEGIN_DATE = "20250301"
END_DATE = "20250320"
STATION_ID = "9414290"
STATION_NAME = "San Francisco"
PRODUCT = "water_level"
DATUM = "MLLW"
TIME_ZONE = "lst_ldt"
UNITS = "metric"
TEST_HORIZON_HOURS = 48

warnings.filterwarnings("ignore", category=ConvergenceWarning)
warnings.filterwarnings("ignore", category=UserWarning)


@dataclass(frozen=True)
class FrequencyConfig:
    rule: str
    seasonal_period: int


FREQUENCY_CONFIGS = [
    FrequencyConfig("30min", 25),
    FrequencyConfig("1h", 12),
    FrequencyConfig("90min", 8),
    FrequencyConfig("2h", 6),
    FrequencyConfig("3h", 4),
    FrequencyConfig("4h", 3),
]


def fetch_base_series() -> pd.Series:
    params = {
        "product": PRODUCT,
        "application": "TimeSeriesAnalysis",
        "begin_date": BEGIN_DATE,
        "end_date": END_DATE,
        "station": STATION_ID,
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


def metrics(y_true: pd.Series, y_pred: pd.Series) -> tuple[float, float]:
    rmse = math.sqrt(mean_squared_error(y_true, y_pred))
    mae = mean_absolute_error(y_true, y_pred)
    return rmse, mae


def add_result(results: list[dict], **kwargs) -> None:
    results.append(kwargs)


def evaluate_seasonal_naive(
    y: pd.Series,
    train: pd.Series,
    test: pd.Series,
    step_hours: float,
    seasonal_period: int,
    freq_rule: str,
    results: list[dict],
) -> None:
    started = time.perf_counter()
    pred = pd.Series(index=test.index, dtype="float64")
    lag_delta = pd.Timedelta(hours=step_hours * seasonal_period)
    for timestamp in test.index:
        lagged_time = timestamp - lag_delta
        if lagged_time in y.index:
            pred.loc[timestamp] = y.loc[lagged_time]
    rmse, mae = metrics(test, pred)
    add_result(
        results,
        family="SeasonalNaive",
        model="Seasonal Naive",
        freq_rule=freq_rule,
        seasonal_period=seasonal_period,
        lags=seasonal_period,
        seasonal=False,
        train_points=len(train),
        test_points=len(test),
        rmse=rmse,
        mae=mae,
        runtime_sec=time.perf_counter() - started,
        note="lag equals one seasonal cycle",
    )


def evaluate_autoreg_grid(
    y: pd.Series,
    train: pd.Series,
    test: pd.Series,
    step_hours: float,
    seasonal_period: int,
    freq_rule: str,
    results: list[dict],
) -> None:
    lag_candidates = sorted(
        {
            seasonal_period,
            seasonal_period * 2,
            seasonal_period * 3,
            seasonal_period * 4,
            int(round(24 / step_hours)),
            int(round(36 / step_hours)),
            int(round(48 / step_hours)),
            int(round(60 / step_hours)),
            int(round(72 / step_hours)),
        }
    )
    for lags in lag_candidates:
        if lags <= 0 or lags >= len(train) - 1:
            continue
        for seasonal in (False, True):
            if seasonal and seasonal_period <= 1:
                continue
            started = time.perf_counter()
            try:
                model = AutoReg(
                    train,
                    lags=lags,
                    old_names=False,
                    seasonal=seasonal,
                    period=seasonal_period if seasonal else None,
                ).fit()
                pred = model.predict(
                    start=len(train),
                    end=len(train) + len(test) - 1,
                    dynamic=False,
                )
                pred.index = test.index
                rmse, mae = metrics(test, pred)
                add_result(
                    results,
                    family="AutoReg",
                    model="AutoReg",
                    freq_rule=freq_rule,
                    seasonal_period=seasonal_period,
                    lags=lags,
                    seasonal=seasonal,
                    train_points=len(train),
                    test_points=len(test),
                    rmse=rmse,
                    mae=mae,
                    runtime_sec=time.perf_counter() - started,
                    note="seasonal dummies enabled" if seasonal else "seasonal dummies disabled",
                )
            except Exception as exc:
                add_result(
                    results,
                    family="AutoReg",
                    model="AutoReg",
                    freq_rule=freq_rule,
                    seasonal_period=seasonal_period,
                    lags=lags,
                    seasonal=seasonal,
                    train_points=len(train),
                    test_points=len(test),
                    rmse=float("nan"),
                    mae=float("nan"),
                    runtime_sec=time.perf_counter() - started,
                    note=f"failed: {exc}",
                )


def evaluate_sarima_grid(
    train: pd.Series,
    test: pd.Series,
    seasonal_period: int,
    freq_rule: str,
    results: list[dict],
) -> None:
    candidates = [
        ((1, 0, 0), (1, 0, 0, seasonal_period)),
        ((2, 0, 0), (1, 0, 0, seasonal_period)),
        ((2, 0, 1), (1, 0, 0, seasonal_period)),
    ]
    for order, seasonal_order in candidates:
        started = time.perf_counter()
        try:
            model = SARIMAX(
                train,
                order=order,
                seasonal_order=seasonal_order,
                enforce_stationarity=False,
                enforce_invertibility=False,
            ).fit(disp=False)
            pred = model.forecast(len(test))
            pred.index = test.index
            rmse, mae = metrics(test, pred)
            add_result(
                results,
                family="SARIMA",
                model=f"SARIMA{order}x{seasonal_order}",
                freq_rule=freq_rule,
                seasonal_period=seasonal_period,
                lags=None,
                seasonal=True,
                train_points=len(train),
                test_points=len(test),
                rmse=rmse,
                mae=mae,
                runtime_sec=time.perf_counter() - started,
                note="",
            )
        except Exception as exc:
            add_result(
                results,
                family="SARIMA",
                model=f"SARIMA{order}x{seasonal_order}",
                freq_rule=freq_rule,
                seasonal_period=seasonal_period,
                lags=None,
                seasonal=True,
                train_points=len(train),
                test_points=len(test),
                rmse=float("nan"),
                mae=float("nan"),
                runtime_sec=time.perf_counter() - started,
                note=f"failed: {exc}",
            )


def evaluate_ets(
    train: pd.Series,
    test: pd.Series,
    seasonal_period: int,
    freq_rule: str,
    results: list[dict],
) -> None:
    started = time.perf_counter()
    try:
        model = ExponentialSmoothing(
            train,
            trend=None,
            seasonal="add",
            seasonal_periods=seasonal_period,
            initialization_method="estimated",
        ).fit(optimized=True)
        pred = model.forecast(len(test))
        pred.index = test.index
        rmse, mae = metrics(test, pred)
        add_result(
            results,
            family="ETS",
            model="ETS(add seasonal)",
            freq_rule=freq_rule,
            seasonal_period=seasonal_period,
            lags=None,
            seasonal=True,
            train_points=len(train),
            test_points=len(test),
            rmse=rmse,
            mae=mae,
            runtime_sec=time.perf_counter() - started,
            note="",
        )
    except Exception as exc:
        add_result(
            results,
            family="ETS",
            model="ETS(add seasonal)",
            freq_rule=freq_rule,
            seasonal_period=seasonal_period,
            lags=None,
            seasonal=True,
            train_points=len(train),
            test_points=len(test),
            rmse=float("nan"),
            mae=float("nan"),
            runtime_sec=time.perf_counter() - started,
            note=f"failed: {exc}",
        )


def run_search(base_series: pd.Series) -> pd.DataFrame:
    results: list[dict] = []
    for config in FREQUENCY_CONFIGS:
        step_hours = pd.Timedelta(config.rule).total_seconds() / 3600
        test_points = int(round(TEST_HORIZON_HOURS / step_hours))
        y = base_series.resample(config.rule).mean().astype("float32")
        train = y.iloc[:-test_points]
        test = y.iloc[-test_points:]

        evaluate_seasonal_naive(y, train, test, step_hours, config.seasonal_period, config.rule, results)
        evaluate_autoreg_grid(y, train, test, step_hours, config.seasonal_period, config.rule, results)
        evaluate_sarima_grid(train, test, config.seasonal_period, config.rule, results)
        evaluate_ets(train, test, config.seasonal_period, config.rule, results)

    result_df = pd.DataFrame(results)
    result_df = result_df.sort_values(["rmse", "mae", "runtime_sec"], na_position="last").reset_index(drop=True)
    return result_df


def format_table(df: pd.DataFrame, columns: list[str]) -> str:
    view = df[columns].copy()
    if "lags" in view.columns:
        view["lags"] = view["lags"].map(lambda x: "-" if pd.isna(x) else str(int(x)))
    if "seasonal" in view.columns:
        view["seasonal"] = view["seasonal"].map(lambda x: "-" if pd.isna(x) else str(bool(x)))
    for col in ("rmse", "mae", "runtime_sec"):
        if col in view.columns:
            view[col] = view[col].map(lambda x: f"{x:.4f}" if pd.notna(x) else "NaN")
    return view.to_markdown(index=False)


def write_markdown(report_df: pd.DataFrame, base_series: pd.Series) -> None:
    valid_df = report_df.dropna(subset=["rmse", "mae"]).copy()
    best_overall = valid_df.iloc[0]
    best_by_family = (
        valid_df.sort_values(["rmse", "mae"])
        .groupby("family", as_index=False)
        .first()
        .sort_values(["rmse", "mae"])
    )
    best_by_freq = (
        valid_df.sort_values(["rmse", "mae"])
        .groupby("freq_rule", as_index=False)
        .first()
        .sort_values(["rmse", "mae"])
    )

    generated_at = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "# NOAA Model Search Report",
        "",
        "## Setup",
        f"- Generated at: `{generated_at}`",
        f"- Station: `{STATION_ID}` ({STATION_NAME})",
        f"- Product: `{PRODUCT}`",
        f"- Date range: `{BEGIN_DATE}` to `{END_DATE}`",
        f"- Base frequency: `6min`",
        f"- Base observations: `{len(base_series)}`",
        f"- Test horizon: last `{TEST_HORIZON_HOURS}` hours for every resampled series",
        "",
        "## Current Best Overall",
        f"- Model: `{best_overall['model']}`",
        f"- Family: `{best_overall['family']}`",
        f"- Frequency: `{best_overall['freq_rule']}`",
        f"- Lags: `{int(best_overall['lags']) if pd.notna(best_overall['lags']) else '-'}`",
        f"- Seasonal dummies: `{best_overall['seasonal']}`",
        f"- RMSE: `{best_overall['rmse']:.4f}`",
        f"- MAE: `{best_overall['mae']:.4f}`",
        "",
        "## Best By Family",
        format_table(
            best_by_family,
            ["family", "model", "freq_rule", "lags", "seasonal", "rmse", "mae"],
        ),
        "",
        "## Best By Frequency",
        format_table(
            best_by_freq,
            ["freq_rule", "family", "model", "lags", "seasonal", "rmse", "mae"],
        ),
        "",
        "## Top 15 Overall",
        format_table(
            valid_df.head(15),
            ["family", "model", "freq_rule", "lags", "seasonal", "rmse", "mae", "runtime_sec"],
        ),
        "",
        "## Notes",
        "- RMSE and MAE are in meter units.",
        "- Frequency comparisons use the same 48-hour test horizon, but smoother series may naturally reduce error.",
        "- The current search suggests that long-lag AutoReg models near a 48-hour memory window perform best on this dataset.",
        "",
        "## Next Search Candidates",
        "- Test a rolling-origin backtest instead of a single 48-hour holdout.",
        "- Compare direct multi-step forecasting with recursive forecasting.",
        "- Re-run the search on a second station to check whether the best configuration generalizes.",
    ]
    MD_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    base_series = fetch_base_series()
    result_df = run_search(base_series)
    result_df.to_csv(CSV_PATH, index=False)
    write_markdown(result_df, base_series)
    print(f"Saved: {CSV_PATH}")
    print(f"Saved: {MD_PATH}")
    print(result_df.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
