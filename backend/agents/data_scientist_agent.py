"""
DataScientistAgent — analyzes demand patterns and builds the
forecasting model. Phase 4: trains a real LightGBM model on the
cleaned dataset and reports its ACTUAL evaluated MAPE/RMSE/MAE from a
held-out time-based test split, not hardcoded numbers.
"""
from backend.agents.base_agent import BaseAgent, Message
from backend.ml.data_prep import prepare_dataset
from backend.ml.forecasting_model import get_trained_model


class DataScientistAgent(BaseAgent):
    def __init__(self):
        super().__init__("DataScientist", "DataScientist", reports_to="TeamLead")
        self.last_report: dict | None = None

    def handle_task(self, message: Message) -> Message:
        if message.action == "assign_specialist_task":
            feature_df, _ = prepare_dataset()
            _, metrics, _ = get_trained_model(feature_df)
            self.last_report = metrics
            message.status = "Forecast Model Built"
            self.send(
                "TeamLead",
                "build_forecast_model",
                {"task_id": message.task_id, "report": metrics},
                priority=message.priority,
            )
        else:
            message.status = "Acknowledged"

        self.memory.append(message.to_dict())
        return message
