"""
Generates a realistic synthetic dataset for the Demand Forecasting &
Inventory Optimization use case, since no real dataset was provided.

Produces:
    datasets/sales_data.csv       - daily sales per SKU, 2 years
    datasets/inventory_levels.csv - current stock + lead time per SKU

Sales data intentionally includes:
    - weekly seasonality (weekend lift)
    - yearly seasonality (holiday bump in Nov/Dec)
    - a mild upward trend
    - random noise
    - ~2% missing values (to exercise cleaning logic)
    - occasional outlier spikes (to exercise outlier handling)

This makes the "cleaning" and "forecasting" steps do real work instead
of running against already-perfect data.
"""
import numpy as np
import pandas as pd

SKUS = [
    {"sku": "SKU-001", "base_demand": 40, "price": 12.99, "lead_time_days": 5, "current_stock": 180},
    {"sku": "SKU-002", "base_demand": 15, "price": 24.50, "lead_time_days": 7, "current_stock": 60},
    {"sku": "SKU-003", "base_demand": 90, "price": 6.49,  "lead_time_days": 3, "current_stock": 200},
    {"sku": "SKU-004", "base_demand": 25, "price": 18.00, "lead_time_days": 6, "current_stock": 90},
]

START_DATE = "2024-01-01"
END_DATE = "2025-12-31"
SEED = 42


def generate_sales_data() -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    dates = pd.date_range(START_DATE, END_DATE, freq="D")
    rows = []

    for sku in SKUS:
        base = sku["base_demand"]
        for i, date in enumerate(dates):
            # Trend: slow ramp up over the two years
            trend = base * (1 + 0.0002 * i)

            # Weekly seasonality: weekends sell more
            weekday_factor = 1.25 if date.weekday() >= 5 else 1.0

            # Yearly seasonality: holiday bump in Nov/Dec
            holiday_factor = 1.6 if date.month in (11, 12) else 1.0

            expected = trend * weekday_factor * holiday_factor
            noise = rng.normal(0, expected * 0.12)
            units_sold = max(0, round(expected + noise))

            # Occasional outlier spike (~0.5% of rows) - e.g. bulk order
            if rng.random() < 0.005:
                units_sold = round(units_sold * rng.uniform(4, 8))

            promotion_flag = 1 if rng.random() < 0.05 else 0
            if promotion_flag:
                units_sold = round(units_sold * rng.uniform(1.3, 1.8))

            rows.append({
                "date": date.strftime("%Y-%m-%d"),
                "sku": sku["sku"],
                "units_sold": units_sold,
                "price": sku["price"],
                "promotion_flag": promotion_flag,
            })

    df = pd.DataFrame(rows)

    # Inject ~2% missing values into units_sold to simulate real-world gaps
    missing_mask = rng.random(len(df)) < 0.02
    df.loc[missing_mask, "units_sold"] = np.nan

    return df


def generate_inventory_levels() -> pd.DataFrame:
    return pd.DataFrame([
        {"sku": s["sku"], "current_stock": s["current_stock"], "lead_time_days": s["lead_time_days"]}
        for s in SKUS
    ])


if __name__ == "__main__":
    sales_df = generate_sales_data()
    inventory_df = generate_inventory_levels()

    sales_df.to_csv("datasets/sales_data.csv", index=False)
    inventory_df.to_csv("datasets/inventory_levels.csv", index=False)

    print(f"sales_data.csv: {len(sales_df)} rows, {sales_df['units_sold'].isna().sum()} missing values")
    print(inventory_df)
