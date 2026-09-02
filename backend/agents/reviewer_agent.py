"""
ReviewerAgent — checks the evidence bundle (QA checks + inventory
recommendations, plus the underlying specialist reports) against
requirements. This is the second and final quality gate before
release:

    passes  -> "approve_for_president" sent up to President
    fails   -> "request_changes" sent back to TeamLead

Requirements checked: all QA checks must have passed, there must be at
least one inventory recommendation, AND (Phase 5) each recommendation's
math is sanity-checked directly rather than just trusting it exists --
see backend/ml/validation.py:check_inventory_calculations().
"""
from backend.agents.base_agent import BaseAgent, Message
from backend.ml.validation import check_inventory_calculations


class ReviewerAgent(BaseAgent):
    def __init__(self):
        super().__init__("Reviewer", "Reviewer", reports_to="InventoryAnalyst")
        self.last_verdict: dict | None = None

    def handle_task(self, message: Message) -> Message:
        if message.action == "generate_inventory_recommendation":
            requirements, approved = self._check_requirements(message.payload)
            self.last_verdict = {
                "task_id": message.payload.get("task_id"),
                "requirements": requirements,
                "approved": approved,
            }

            if approved:
                message.status = "Approved for President"
                self.send(
                    "President",
                    "approve_for_president",
                    {
                        "task_id": message.payload.get("task_id"),
                        "results": message.payload.get("results"),
                        "qa_checks": message.payload.get("qa_checks"),
                        "inventory_recommendations": message.payload.get("inventory_recommendations"),
                        "review_requirements": requirements,
                        "reviewed_by": "Reviewer",
                    },
                    priority="High",
                )
            else:
                message.status = "Changes Requested"
                self.send(
                    "TeamLead",
                    "request_changes",
                    {
                        "task_id": message.payload.get("task_id"),
                        "requirements": requirements,
                        "reason": "Evidence did not meet review requirements",
                    },
                    priority="High",
                )
        else:
            message.status = "Acknowledged"

        self.memory.append(message.to_dict())
        return message

    @staticmethod
    def _check_requirements(payload: dict) -> tuple[dict, bool]:
        qa_checks = payload.get("qa_checks", {})
        recommendations = payload.get("inventory_recommendations", [])

        all_qa_passed = bool(qa_checks) and all(c.get("passed") for c in qa_checks.values())
        has_recommendations = len(recommendations) > 0
        inventory_calc_check = check_inventory_calculations(recommendations)

        requirements = {
            "all_qa_checks_passed": {"passed": all_qa_passed, "detail": qa_checks},
            "inventory_recommendations_present": {
                "passed": has_recommendations,
                "detail": f"{len(recommendations)} recommendation(s)",
            },
            "inventory_calculations_correct": inventory_calc_check,
        }
        approved = all_qa_passed and has_recommendations and inventory_calc_check["passed"]
        return requirements, approved
