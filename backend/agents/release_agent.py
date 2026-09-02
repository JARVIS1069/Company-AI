"""
ReleaseAgent — the final gate. Only releases after verifying:
  1. approvals  -> President actually signed off (approved_by == "President")
  2. quality gates -> the QA checks embedded in the Reviewer's evidence
     all passed

This re-verifies rather than blindly trusting the "approve_release"
message -- the whole point of a release gate is that it doesn't just
take someone's word for it, it checks the evidence itself.
"""
from datetime import datetime, timezone

from backend.agents.base_agent import BaseAgent, Message
from backend.audit.audit_log import audit_log


class ReleaseAgent(BaseAgent):
    def __init__(self):
        super().__init__("Release", "Release", reports_to="President")
        self.released: list[dict] = []
        self.blocked: list[dict] = []

    def handle_task(self, message: Message) -> Message:
        if message.action == "approve_release":
            verification = self._verify(message.payload)
            task_id = message.payload.get("source_task_id")

            if verification["passed"]:
                record = {
                    "task_id": task_id,
                    "approved_by": message.payload.get("approved_by"),
                    "verification": verification,
                    "released_at": datetime.now(timezone.utc).isoformat(),
                }
                self.released.append(record)
                message.status = "Released"
                audit_log.record(self.name, "RELEASE_TO_PRODUCTION", record)
            else:
                self.blocked.append({"task_id": task_id, "verification": verification})
                message.status = "Blocked"
                audit_log.record(self.name, "RELEASE_BLOCKED", {"task_id": task_id, "verification": verification})
        else:
            message.status = "Acknowledged"

        self.memory.append(message.to_dict())
        return message

    def _verify(self, payload: dict) -> dict:
        """Re-check the evidence rather than trusting the message at face value."""
        approvals_verified = self.can("verify_approvals") and payload.get("approved_by") == "President"

        evidence = payload.get("reviewer_evidence", {})
        qa_checks = evidence.get("qa_checks", {})
        quality_gates_verified = (
            self.can("verify_quality_gates")
            and bool(qa_checks)
            and all(c.get("passed") for c in qa_checks.values())
        )

        return {
            "approvals_verified": approvals_verified,
            "quality_gates_verified": quality_gates_verified,
            "passed": approvals_verified and quality_gates_verified,
        }
