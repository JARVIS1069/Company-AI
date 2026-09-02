"""
InventoryAnalystAgent — turns the QA-approved forecast into reorder
points and stockout-risk recommendations, then hands off to Reviewer.

Phase 4: uses the ACTUAL trained model (same cached model DataScientist
trained) to forecast the next 14 days per SKU, and real current stock /
lead times from datasets/inventory_levels.csv -- via
backend/ml/inventory_optimizer.py -- instead of a fixed placeholder
catalog.
"""
from backend.agents.base_agent import BaseAgent, Message
from backend.ml.data_prep import prepare_dataset
from backend.ml.forecasting_model import get_trained_model, forecast_next_n_days
from backend.ml.inventory_optimizer import load_inventory_levels, compute_recommendations


class InventoryAnalystAgent(BaseAgent):
    def __init__(self):
        super().__init__("InventoryAnalyst", "InventoryAnalyst", reports_to="QAValidator")
        self.last_recommendation: dict | None = None

    def handle_task(self, message: Message) -> Message:
        if message.action == "submit_for_inventory_optimization":
            feature_df, _ = prepare_dataset()
            model, _, _ = get_trained_model(feature_df)  # cache hit, no retraining

            inventory_df = load_inventory_levels()
            forecasts_by_sku = {
                sku: forecast_next_n_days(model, feature_df, sku, n_days=14)
                for sku in feature_df["sku"].unique()
            }
            recommendations = compute_recommendations(forecasts_by_sku, inventory_df)

            self.last_recommendation = {
                "task_id": message.payload.get("task_id"),
                "recommendations": recommendations,
            }
            message.status = "Recommendations Generated"

            self.send(
                "Reviewer",
                "generate_inventory_recommendation",
                {
                    "task_id": message.payload.get("task_id"),
                    "results": message.payload.get("results"),
                    "qa_checks": message.payload.get("qa_checks"),
                    "inventory_recommendations": recommendations,
                },
                priority=message.priority,
            )
        else:
            message.status = "Acknowledged"

        self.memory.append(message.to_dict())
        return message
