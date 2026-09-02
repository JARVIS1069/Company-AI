"""
MLEngineerAgent — evaluates, packages, and deploys the best model.
Phase 4: reuses the cached trained model (same one DataScientist
trained -- see get_trained_model()'s cache) and actually saves it to
disk with joblib, rather than reporting a hardcoded fake path.
"""
import joblib

from backend.agents.base_agent import BaseAgent, Message
from backend.ml.data_prep import prepare_dataset
from backend.ml.forecasting_model import get_trained_model

ARTIFACT_PATH = "models/forecast_model_v1.joblib"


class MLEngineerAgent(BaseAgent):
    def __init__(self):
        super().__init__("MLEngineer", "MLEngineer", reports_to="TeamLead")
        self.last_report: dict | None = None

    def handle_task(self, message: Message) -> Message:
        if message.action == "assign_specialist_task":
            feature_df, _ = prepare_dataset()
            model, metrics, _ = get_trained_model(feature_df)  # cache hit if DataScientist already ran

            joblib.dump(model, ARTIFACT_PATH)

            self.last_report = {
                "package_format": "joblib",
                "artifact_path": ARTIFACT_PATH,
                "serving_endpoint": "/api/v1/forecast",
                "source_model_MAPE": metrics["MAPE"],
                "status": "packaged",
            }
            message.status = "Model Packaged"
            self.send(
                "TeamLead",
                "package_model",
                {"task_id": message.task_id, "report": self.last_report},
                priority=message.priority,
            )
        else:
            message.status = "Acknowledged"

        self.memory.append(message.to_dict())
        return message
