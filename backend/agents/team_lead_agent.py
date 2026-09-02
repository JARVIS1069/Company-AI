"""
TeamLeadAgent — chooses the technical approach for the project, then
fans the work out to three specialists in parallel: DataEngineer,
DataScientist, and MLEngineer. This is the first branching point in
the org chart (one input, three outputs), so it uses
BaseAgent.send_to_many() instead of three separate send() calls.
"""
from backend.agents.base_agent import BaseAgent, Message
import uuid

SPECIALISTS = ["DataEngineer", "DataScientist", "MLEngineer"]

# Actions each specialist reports back with once done. Any of these
# arriving is treated as "one specialist checked in" for that task_id.
REPORT_ACTIONS = {"prepare_dataset", "build_forecast_model", "package_model"}


class TeamLeadAgent(BaseAgent):
    def __init__(self):
        super().__init__("TeamLead", "TeamLead", reports_to="Manager")
        self.technical_approach: dict | None = None
        self.dispatched_tasks: list[Message] = []
        # task_id -> {"expected": {...agent names...}, "results": {agent_name: report}}
        self.pending_results: dict[str, dict] = {}

    def handle_task(self, message: Message) -> Message:
        if message.action == "assign_task":
            plan = message.payload.get("plan", {})

            # Choose the technical approach for this project.
            self.technical_approach = {
                "data_pipeline": "batch ETL from sales + inventory CSVs, daily refresh",
                "forecast_model": "gradient-boosted trees (e.g. LightGBM) baseline, "
                                   "fallback to seasonal naive",
                "serving": "FastAPI microservice, model packaged with joblib",
            }
            message.status = "Approach Chosen"

            # Generate the shared task_id BEFORE dispatching and register
            # tracking state first -- the event bus is synchronous, so a
            # specialist's reply can arrive before send_to_many() returns.
            shared_task_id = f"TASK-{uuid.uuid4().hex[:6].upper()}"
            self.pending_results[shared_task_id] = {
                "expected": set(SPECIALISTS),
                "results": {},
            }

            self.dispatched_tasks = self.send_to_many(
                SPECIALISTS,
                "assign_specialist_task",
                {
                    "task": "Execute your part of: " + message.payload.get("task", ""),
                    "plan": plan,
                    "technical_approach": self.technical_approach,
                },
                priority=message.priority,
                task_id=shared_task_id,
            )

        elif message.action in REPORT_ACTIONS:
            self._record_specialist_result(message)

        else:
            message.status = "Acknowledged"

        self.memory.append(message.to_dict())
        return message

    def _record_specialist_result(self, message: Message) -> None:
        """
        Record one specialist's report. Once ALL expected specialists
        for this task_id have checked in, consolidate their results
        into a single handoff to QAValidator (see design note in
        SKILL/roadmap: consolidated handoff, not 3 separate ones).
        """
        task_id = message.payload.get("task_id")
        bucket = self.pending_results.get(task_id)
        if bucket is None:
            message.status = "Unknown Task"
            return

        bucket["results"][message.from_agent] = message.payload.get("report")
        message.status = "Result Recorded"

        if bucket["expected"] <= bucket["results"].keys():
            self.send(
                "QAValidator",
                "submit_for_qa",
                {"task_id": task_id, "results": bucket["results"]},
                priority="High",
            )
