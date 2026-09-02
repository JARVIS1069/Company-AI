"""
PresidentAgent — top of the org. Approves project direction/budget/risk
and, later in the workflow, the final release.

Incoming actions handled:
    "request_project_approval" -> approves and kicks off VP with "approve_project"
    "request_release_approval" / "approve_for_president"
        -> approves and kicks off Release with "approve_release"
        (Reviewer sends "approve_for_president" once it has reviewed
        the evidence; both action names lead to the same final
        approval logic since they mean the same thing at this stage.)

Note: incoming action names (the "request_*" ones) are just message
labels -- they aren't permission-checked, since permission checks only
happen on SEND. What President is allowed to *send* is still governed
by ROLE_PERMISSIONS in rbac.py (approve_project, approve_release, ...).
"""
from backend.agents.base_agent import BaseAgent, Message


class PresidentAgent(BaseAgent):
    def __init__(self):
        super().__init__("President", "President", reports_to=None)
        self.approved_projects: list[str] = []
        self.approved_releases: list[str] = []

    def handle_task(self, message: Message) -> Message:
        if message.action == "request_project_approval":
            project = message.payload.get("project", "Unnamed Project")
            self.approved_projects.append(project)
            message.status = "Approved"
            self.send(
                "VP",
                "approve_project",
                {"project": project, "approved_by": "President"},
                priority="High",
            )

        elif message.action in ("request_release_approval", "approve_for_president"):
            self.approved_releases.append(message.task_id)
            message.status = "Approved"
            self.send(
                "Release",
                "approve_release",
                {
                    "source_task_id": message.task_id,
                    "approved_by": "President",
                    "reviewer_evidence": message.payload,
                },
                priority="High",
            )

        else:
            message.status = "Acknowledged"

        self.memory.append(message.to_dict())
        return message
