"""
Real validation logic for Phase 5.

These functions actually inspect the data file and the saved model
artifact on disk, rather than trusting the specialist reports at face
value. QAValidatorAgent and ReviewerAgent call into this module.
"""
import numpy as np
import pandas as pd

EXPECTED_SALES_COLUMNS = {"date", "sku", "units_sold", "price", "promotion_flag"}
MAX_NULL_RATE = 0.05       # fail if more than 5% of units_sold is null in the RAW file
                           # (this checks the raw file BEFORE DataEngineer's cleaning ran,
                           #  i.e. "is the incoming data even usable", not "did cleaning work")


def check_raw_data_quality(path: str = "datasets/sales_data.csv") -> dict:
    """Schema, null-rate, duplicate, and date-continuity checks on the raw file."""
    try:
        df = pd.read_csv(path, parse_dates=["date"])
    except Exception as e:
        return {"passed": False, "detail": f"Could not read {path}: {e}"}

    issues = []

    missing_cols = EXPECTED_SALES_COLUMNS - set(df.columns)
    if missing_cols:
        issues.append(f"missing columns: {missing_cols}")

    null_rate = float(df["units_sold"].isna().mean()) if "units_sold" in df.columns else 1.0
    if null_rate > MAX_NULL_RATE:
        issues.append(f"null rate {null_rate:.1%} exceeds {MAX_NULL_RATE:.0%}")

    dup_count = int(df.duplicated(subset=["date", "sku"]).sum()) if {"date", "sku"} <= set(df.columns) else 0
    if dup_count > 0:
        issues.append(f"{dup_count} duplicate (date, sku) rows")

    gap_summary = {}
    if {"date", "sku"} <= set(df.columns):
        for sku, group in df.groupby("sku"):
            full_range = pd.date_range(group["date"].min(), group["date"].max(), freq="D")
            missing_days = len(full_range) - group["date"].nunique()
            if missing_days > 0:
                gap_summary[sku] = missing_days
    if gap_summary:
        issues.append(f"date gaps per SKU: {gap_summary}")

    passed = len(issues) == 0
    detail = "no issues found" if passed else "; ".join(issues)
    return {
        "passed": passed,
        "detail": detail,
        "rows": len(df),
        "null_rate": round(null_rate, 4),
        "duplicate_rows": dup_count,
    }


def check_model_artifact(artifact_path: str, sample_row: dict) -> dict:
    """
    Load the saved model from disk and actually run a prediction on it,
    rather than just checking that a file path string exists. Confirms
    the artifact is loadable and produces a sane (non-negative, finite)
    output -- this is the closest thing to an "API correctness" check
    without a live running server.
    """
    import joblib

    try:
        model = joblib.load(artifact_path)
    except Exception as e:
        return {"passed": False, "detail": f"Could not load model from {artifact_path}: {e}"}

    try:
        row_df = pd.DataFrame([sample_row])
        prediction = model.predict(row_df)[0]
    except Exception as e:
        return {"passed": False, "detail": f"Model failed to predict: {e}"}

    is_sane = np.isfinite(prediction) and prediction >= 0
    return {
        "passed": bool(is_sane),
        "detail": f"loaded OK, sample prediction={round(float(prediction), 2)}",
    }


def check_inventory_calculations(recommendations: list[dict]) -> dict:
    """
    Sanity-check each recommendation's math rather than just checking
    that recommendations exist: reorder_point should equal roughly
    (avg_daily_demand_forecast * lead_time_days) + safety_stock, and
    no values should be negative.
    """
    if not recommendations:
        return {"passed": False, "detail": "no recommendations to check"}

    issues = []
    for rec in recommendations:
        sku = rec.get("sku", "?")
        avg_demand = rec.get("avg_daily_demand_forecast", 0)
        lead_time = rec.get("lead_time_days", 0)
        safety_stock = rec.get("safety_stock", 0)
        reorder_point = rec.get("reorder_point", 0)

        if any(v < 0 for v in (avg_demand, lead_time, safety_stock, reorder_point)):
            issues.append(f"{sku}: negative value found")
            continue

        expected = avg_demand * lead_time + safety_stock
        # Allow small rounding tolerance
        if abs(reorder_point - expected) > 2:
            issues.append(f"{sku}: reorder_point {reorder_point} != expected ~{round(expected)}")

    passed = len(issues) == 0
    detail = f"{len(recommendations)} recommendation(s) checked" if passed else "; ".join(issues)
    return {"passed": passed, "detail": detail}
