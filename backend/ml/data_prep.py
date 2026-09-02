"""
Real data preparation for the demand forecasting pipeline.

Replaces DataEngineerAgent's placeholder report with actual work:
    load -> handle missing values -> remove outliers -> engineer features

Feature engineering adds:
    - day_of_week, month (seasonality signals)
    - lag_7 (units sold 7 days ago, same weekday last week)
    - rolling_mean_7, rolling_mean_28 (recent trend)
"""
import numpy as np
import pandas as pd

SALES_DATA_PATH = "datasets/sales_data.csv"


def load_and_clean(path: str = SALES_DATA_PATH) -> tuple[pd.DataFrame, dict]:
    """Load raw sales data, clean it, and return (clean_df, cleaning_report)."""
    df = pd.read_csv(path, parse_dates=["date"])
    df = df.sort_values(["sku", "date"]).reset_index(drop=True)

    rows_loaded = len(df)
    missing_before = int(df["units_sold"].isna().sum())

    # Handle missing values: per-SKU forward/backward fill, then any
    # remainder falls back to the per-SKU median (covers gaps at the
    # very start of a SKU's series where there's nothing to fill from).
    df["units_sold"] = df.groupby("sku")["units_sold"].transform(
        lambda s: s.ffill().bfill()
    )
    still_missing = df["units_sold"].isna()
    if still_missing.any():
        df.loc[still_missing, "units_sold"] = df.groupby("sku")["units_sold"].transform("median")

    # Remove outliers using per-SKU IQR bounds, capping (not dropping,
    # so we don't lose calendar days) extreme values to the bound.
    outliers_capped = 0

    def cap_outliers(group: pd.Series) -> pd.Series:
        nonlocal outliers_capped
        q1, q3 = group.quantile(0.25), group.quantile(0.75)
        iqr = q3 - q1
        lower, upper = q1 - 3 * iqr, q3 + 3 * iqr
        is_outlier = (group < lower) | (group > upper)
        outliers_capped += int(is_outlier.sum())
        return group.clip(lower=max(lower, 0), upper=upper)

    df["units_sold"] = df.groupby("sku")["units_sold"].transform(cap_outliers)
    df["units_sold"] = df["units_sold"].round().astype(int)

    report = {
        "rows_processed": rows_loaded,
        "missing_values_handled": missing_before,
        "outliers_capped": outliers_capped,
        "skus": sorted(df["sku"].unique().tolist()),
        "date_range": [df["date"].min().strftime("%Y-%m-%d"), df["date"].max().strftime("%Y-%m-%d")],
    }
    return df, report


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add seasonality, lag, and rolling-window features per SKU."""
    df = df.copy()
    df["day_of_week"] = df["date"].dt.dayofweek
    df["month"] = df["date"].dt.month
    df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)

    df["lag_7"] = df.groupby("sku")["units_sold"].shift(7)
    df["rolling_mean_7"] = (
        df.groupby("sku")["units_sold"].transform(lambda s: s.shift(1).rolling(7).mean())
    )
    df["rolling_mean_28"] = (
        df.groupby("sku")["units_sold"].transform(lambda s: s.shift(1).rolling(28).mean())
    )

    # Drop the warm-up rows where lag/rolling features aren't available yet
    df = df.dropna(subset=["lag_7", "rolling_mean_7", "rolling_mean_28"]).reset_index(drop=True)
    return df


def prepare_dataset(path: str = SALES_DATA_PATH) -> tuple[pd.DataFrame, dict]:
    """Full pipeline: load, clean, engineer features. Returns (feature_df, report)."""
    clean_df, cleaning_report = load_and_clean(path)
    feature_df = engineer_features(clean_df)
    cleaning_report["rows_after_feature_engineering"] = len(feature_df)
    cleaning_report["status"] = "ready"
    return feature_df, cleaning_report


if __name__ == "__main__":
    feature_df, report = prepare_dataset()
    print(report)
    print(feature_df.head())
