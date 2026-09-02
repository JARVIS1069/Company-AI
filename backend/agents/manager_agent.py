"""
ManagerAgent — turns a VP goal into a concrete plan: milestones, tasks,
and deadlines, then assigns the work to TeamLead to execute.
"""
from datetime import datetime, timedelta, timezone

from backend.agents.base_agent import BaseAgent, Message

DEFAULT_MILESTONES = [
    {"name": "Data Prepared", "days_from_now": 3},
    {"name": "Forecast Model Ready", "days_from_now": 7},
    {"name": "Inventory Recommendations Ready", "days_from_now": 9},
    {"name": "Validated & Reviewed", "days_from_now": 11},
]


class ManagerAgent(BaseAgent):
    def __init__(self):
        super().__init__("Manager", "Manager", reports_to="VP")
        self.plan: dict | None = None
        self.milestones: list[dict] = []

    def handle_task(self, message: Message) -> Message:
        if message.action == "assign_manager_goal":
            goal = message.payload.get("goal")
            kpis = message.payload.get("kpis", [])

            now = datetime.now(timezone.utc)
            self.milestones = [
                {
                    "name": m["name"],
                    "deadline": (now + timedelta(days=m["days_from_now"])).isoformat(),
                }
                for m in DEFAULT_MILESTONES
            ]
            self.plan = {"goal": goal, "kpis": kpis, "milestones": self.milestones}
            message.status = "Plan Created"

            self.send(
                "TeamLead",
                "assign_task",
                {
                    "task": "Prepare Sales Dataset, Build Forecast, Optimize Inventory",
                    "plan": self.plan,
                },
                priority="High",
            )
        else:
            message.status = "Acknowledged"

        self.memory.append(message.to_dict())
        return message
