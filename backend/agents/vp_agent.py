"""
VPAgent — turns the President-approved project into concrete KPIs,
then hands a goal down to Manager to plan against.
"""
from backend.agents.base_agent import BaseAgent, Message

DEFAULT_KPIS = [
    "forecast_MAPE_below_15pct",
    "stockout_rate_below_5pct",
    "inventory_turnover_improved",
]


class VPAgent(BaseAgent):
    def __init__(self):
        super().__init__("VP", "VP", reports_to="President")
        self.kpis: list[str] = []

    def handle_task(self, message: Message) -> Message:
        if message.action == "approve_project":
            project = message.payload.get("project", "Unnamed Project")
            self.kpis = list(DEFAULT_KPIS)
            message.status = "KPIs Defined"
            self.send(
                "Manager",
                "assign_manager_goal",
                {
                    "project": project,
                    "goal": "Forecast demand and optimize inventory to hit KPIs",
                    "kpis": self.kpis,
                },
                priority="High",
            )
        else:
            message.status = "Acknowledged"

        self.memory.append(message.to_dict())
        return message
