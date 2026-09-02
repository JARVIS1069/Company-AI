"""
Real inventory optimization for InventoryAnalystAgent.

Replaces the placeholder fixed-catalog calculation with reorder points
and stockout risk computed from the model's actual 14-day forecast per
SKU, plus real current stock / lead time from inventory_levels.csv.

    reorder_point = expected demand during lead time + safety stock
    safety_stock  = z_score * std_dev(forecast) * sqrt(lead_time_days)
                    (classic safety stock formula: uncertainty in
                    demand, scaled by how long we're exposed to it)
"""
import numpy as np
import pandas as pd

INVENTORY_LEVELS_PATH = "datasets/inventory_levels.csv"
Z_SCORE_95PCT = 1.65  # ~95% service level


def load_inventory_levels(path: str = INVENTORY_LEVELS_PATH) -> pd.DataFrame:
    return pd.read_csv(path)


def compute_recommendations(
    forecasts_by_sku: dict[str, list[float]],
    inventory_df: pd.DataFrame,
) -> list[dict]:
    """
    forecasts_by_sku: {sku: [day1_forecast, day2_forecast, ...]} from
    forecasting_model.forecast_next_n_days().
    """
    recommendations = []

    for _, row in inventory_df.iterrows():
        sku = row["sku"]
        lead_time_days = int(row["lead_time_days"])
        current_stock = int(row["current_stock"])

        forecast = forecasts_by_sku.get(sku, [])
        if not forecast:
            continue

        avg_daily_demand = float(np.mean(forecast))
        demand_std = float(np.std(forecast)) if len(forecast) > 1 else avg_daily_demand * 0.2

        expected_demand_during_lead_time = avg_daily_demand * lead_time_days
        safety_stock = round(Z_SCORE_95PCT * demand_std * np.sqrt(lead_time_days))
        reorder_point = round(expected_demand_during_lead_time + safety_stock)
        stockout_risk = current_stock < reorder_point

        recommendations.append({
            "sku": sku,
            "avg_daily_demand_forecast": round(avg_daily_demand, 1),
            "lead_time_days": lead_time_days,
            "reorder_point": reorder_point,
            "safety_stock": safety_stock,
            "current_stock": current_stock,
            "stockout_risk": stockout_risk,
            "recommended_action": "Reorder now" if stockout_risk else "No action needed",
        })

    return recommendations


if __name__ == "__main__":
    from backend.ml.data_prep import prepare_dataset
    from backend.ml.forecasting_model import train_and_evaluate, forecast_next_n_days

    feature_df, _ = prepare_dataset()
    model, metrics = train_and_evaluate(feature_df)
    print(metrics)

    inventory_df = load_inventory_levels()
    forecasts_by_sku = {
        sku: forecast_next_n_days(model, feature_df, sku, n_days=14)
        for sku in feature_df["sku"].unique()
    }
    recs = compute_recommendations(forecasts_by_sku, inventory_df)
    for r in recs:
        print(r)
