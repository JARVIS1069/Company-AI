"""
DataEngineerAgent — collects, cleans, and prepares sales and inventory
data. Phase 4: this now runs REAL cleaning (backend/ml/data_prep.py)
against datasets/sales_data.csv -- handling actual missing values and
outliers, not a hardcoded placeholder report.
"""
from backend.agents.base_agent import BaseAgent, Message
from backend.ml.data_prep import prepare_dataset


class DataEngineerAgent(BaseAgent):
    def __init__(self):
        super().__init__("DataEngineer", "DataEngineer", reports_to="TeamLead")
        self.last_report: dict | None = None

    def handle_task(self, message: Message) -> Message:
        if message.action == "assign_specialist_task":
            _, report = prepare_dataset()
            self.last_report = report
            message.status = "Dataset Prepared"
            self.send(
                "TeamLead",
                "prepare_dataset",
                {"task_id": message.task_id, "report": report},
                priority=message.priority,
            )
        else:
            message.status = "Acknowledged"

        self.memory.append(message.to_dict())
        return message
