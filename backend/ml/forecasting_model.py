"""
Real demand forecasting model.

Replaces DataScientistAgent's placeholder metrics with an actual
trained LightGBM model, evaluated on a held-out time-based test split
(last 60 days per SKU), reporting real MAPE / RMSE / MAE.
"""
import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error, mean_squared_error

FEATURES = ["day_of_week", "month", "is_weekend", "lag_7", "rolling_mean_7", "rolling_mean_28", "promotion_flag"]
TARGET = "units_sold"
TEST_DAYS = 60  # last N days per SKU held out for evaluation

# In-memory cache: since DataScientist, MLEngineer, and InventoryAnalyst
# each independently call prepare_dataset() (they run in parallel, per
# the org chart's fan-out from TeamLead), we cache the trained model so
# it's only actually trained once per process instead of 2-3x over.
_MODEL_CACHE: dict = {}


def get_trained_model(feature_df: pd.DataFrame) -> tuple["LGBMRegressor", dict, pd.DataFrame]:
    """Train once and cache; subsequent calls return the same model + metrics."""
    if "model" not in _MODEL_CACHE:
        model, metrics = train_and_evaluate(feature_df)
        _MODEL_CACHE["model"] = model
        _MODEL_CACHE["metrics"] = metrics
        _MODEL_CACHE["feature_df"] = feature_df
    return _MODEL_CACHE["model"], _MODEL_CACHE["metrics"], _MODEL_CACHE["feature_df"]


def time_based_split(df: pd.DataFrame, test_days: int = TEST_DAYS) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Per-SKU time split: last `test_days` days of each SKU's series go to test."""
    cutoff = df.groupby("sku")["date"].transform(lambda s: s.max() - pd.Timedelta(days=test_days))
    train_df = df[df["date"] <= cutoff].reset_index(drop=True)
    test_df = df[df["date"] > cutoff].reset_index(drop=True)
    return train_df, test_df


def train_and_evaluate(feature_df: pd.DataFrame) -> tuple[LGBMRegressor, dict]:
    """Train a LightGBM model with SKU as a categorical feature, evaluate on holdout."""
    df = feature_df.copy()
    df["sku_code"] = df["sku"].astype("category").cat.codes
    feature_cols = FEATURES + ["sku_code"]

    train_df, test_df = time_based_split(df)

    model = LGBMRegressor(
        n_estimators=200,
        max_depth=5,
        learning_rate=0.05,
        random_state=42,
        verbosity=-1,
    )
    model.fit(train_df[feature_cols], train_df[TARGET])

    predictions = model.predict(test_df[feature_cols])
    predictions = np.clip(predictions, 0, None)  # demand can't be negative

    y_true = test_df[TARGET].values
    # Avoid divide-by-zero in MAPE for any zero-demand test rows
    mape_mask = y_true > 0
    mape = float(mean_absolute_percentage_error(y_true[mape_mask], predictions[mape_mask]))
    rmse = float(np.sqrt(mean_squared_error(y_true, predictions)))
    mae = float(mean_absolute_error(y_true, predictions))

    metrics = {
        "model_type": "LightGBM (gradient-boosted trees)",
        "MAPE": round(mape, 4),
        "RMSE": round(rmse, 2),
        "MAE": round(mae, 2),
        "train_rows": len(train_df),
        "test_rows": len(test_df),
        "status": "trained",
    }
    return model, metrics


def forecast_next_n_days(model: LGBMRegressor, feature_df: pd.DataFrame, sku: str, n_days: int = 14) -> list[float]:
    """
    Roll the model forward n_days for one SKU, feeding each day's
    prediction back in as history for the next day's lag/rolling
    features (since we don't have real future data to look up).
    """
    df = feature_df.copy()
    df["sku_code"] = df["sku"].astype("category").cat.codes
    sku_history = df[df["sku"] == sku].sort_values("date").copy()
    sku_code = sku_history["sku_code"].iloc[0]

    history_units = sku_history[TARGET].tolist()
    last_date = sku_history["date"].max()

    forecasts = []
    for i in range(1, n_days + 1):
        future_date = last_date + pd.Timedelta(days=i)
        lag_7 = history_units[-7] if len(history_units) >= 7 else np.mean(history_units)
        rolling_mean_7 = np.mean(history_units[-7:])
        rolling_mean_28 = np.mean(history_units[-28:]) if len(history_units) >= 28 else np.mean(history_units)

        row = pd.DataFrame([{
            "day_of_week": future_date.dayofweek,
            "month": future_date.month,
            "is_weekend": int(future_date.dayofweek >= 5),
            "lag_7": lag_7,
            "rolling_mean_7": rolling_mean_7,
            "rolling_mean_28": rolling_mean_28,
            "promotion_flag": 0,
            "sku_code": sku_code,
        }])
        pred = max(0.0, float(model.predict(row)[0]))
        forecasts.append(round(pred, 1))
        history_units.append(pred)

    return forecasts


if __name__ == "__main__":
    from backend.ml.data_prep import prepare_dataset

    feature_df, _ = prepare_dataset()
    model, metrics = train_and_evaluate(feature_df)
    print(metrics)

    for sku in feature_df["sku"].unique():
        forecast = forecast_next_n_days(model, feature_df, sku, n_days=14)
        print(f"{sku} next 14 days forecast: {forecast}")
