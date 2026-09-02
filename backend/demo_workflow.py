"""
Phase 2 sanity check — President through QAValidator.
Run directly, no server needed:

    python -m backend.demo_workflow

Part 1: the full happy-path cascade, President -> ... -> QAValidator,
which now runs real checks (data quality / forecast accuracy / API
correctness) against the consolidated specialist report and passes it
to InventoryAnalyst (still a plain BaseAgent stub for now).

Part 2: proves the QA FAIL path also works -- feeds QAValidator a
report with MAPE above the threshold and confirms it flags TeamLead
instead of forwarding to InventoryAnalyst.
"""
from backend.agents.base_agent import BaseAgent, Message
from backend.agents.president_agent import PresidentAgent
from backend.agents.vp_agent import VPAgent
from backend.agents.manager_agent import ManagerAgent
from backend.agents.team_lead_agent import TeamLeadAgent
from backend.agents.data_engineer_agent import DataEngineerAgent
from backend.agents.data_scientist_agent import DataScientistAgent
from backend.agents.ml_engineer_agent import MLEngineerAgent
from backend.agents.qa_validator_agent import QAValidatorAgent
from backend.agents.inventory_analyst_agent import InventoryAnalystAgent
from backend.agents.reviewer_agent import ReviewerAgent
from backend.agents.release_agent import ReleaseAgent
from backend.audit.audit_log import audit_log


def run_happy_path():
    president = PresidentAgent()
    vp = VPAgent()
    manager = ManagerAgent()
    team_lead = TeamLeadAgent()
    data_engineer = DataEngineerAgent()
    data_scientist = DataScientistAgent()
    ml_engineer = MLEngineerAgent()
    qa_validator = QAValidatorAgent()
    inventory_analyst = InventoryAnalystAgent()
    reviewer = ReviewerAgent()
    release = ReleaseAgent()

    print("=== PART 1: Full happy path, President -> ... -> Release (RELEASED) ===")
    kickoff = Message(
        "User", "President", "request_project_approval",
        {"project": "Demand Forecasting & Inventory Optimization"},
    )
    president.receive(kickoff)

    print(f"\nQA verdict: {qa_validator.last_verdict}")
    print(f"\nReviewer verdict: {reviewer.last_verdict}")
    print(f"\nRelease record: {release.released}")
    print(f"\nRelease blocked list (should be empty): {release.blocked}")

    print("\n--- Full audit trail ---")
    for entry in audit_log.all():
        detail_action = entry["detail"].get("action", "")
        print(f"[{entry['timestamp']}] {entry['actor']:<14} {entry['event_type']:<10} {detail_action}")


def run_qa_fail_path():
    print("\n\n=== PART 2: QA FAIL path (bad MAPE) -> flags TeamLead instead of forwarding ===")
    team_lead = TeamLeadAgent()
    qa_validator = QAValidatorAgent()

    bad_results = {
        "DataEngineer": {"status": "ready", "rows_processed": 12000},
        "DataScientist": {"status": "trained", "MAPE": 0.42},  # fails threshold (< 0.15)
        "MLEngineer": {"status": "packaged", "serving_endpoint": "/api/v1/forecast"},
    }
    bad_submission = Message("TeamLead", "QAValidator", "submit_for_qa",
                              {"task_id": "TASK-BADCASE", "results": bad_results})
    qa_validator.receive(bad_submission)

    print(f"\nQA verdict: {qa_validator.last_verdict}")
    print(f"\nTeamLead inbox (should contain a flag_issue message): "
          f"{[m.to_dict() for m in team_lead.inbox]}")


def run_release_block_path():
    print("\n\n=== PART 3: Release BLOCKS a forged approval with fake/missing evidence ===")
    release = ReleaseAgent()

    # Someone/something claims President approved it, but the embedded
    # evidence shows a QA check actually failed. Release must catch this
    # itself, not just trust "approved_by": "President".
    forged = Message(
        "President", "Release", "approve_release",
        {
            "source_task_id": "TASK-FORGED",
            "approved_by": "President",
            "reviewer_evidence": {
                "qa_checks": {
                    "data_quality": {"passed": True},
                    "forecast_accuracy": {"passed": False},  # this should block release
                }
            },
        },
    )
    release.receive(forged)

    print(f"\nRelease record (should be empty): {release.released}")
    print(f"\nRelease blocked list: {release.blocked}")


def run_reviewer_bad_math_path():
    print("\n\n=== PART 4: Reviewer catches BAD inventory math -> request_changes to TeamLead ===")
    team_lead = TeamLeadAgent()
    reviewer = ReviewerAgent()

    bad_recommendation = Message(
        "InventoryAnalyst", "Reviewer", "generate_inventory_recommendation",
        {
            "task_id": "TASK-BADMATH",
            "qa_checks": {
                "data_quality": {"passed": True},
                "forecast_accuracy": {"passed": True},
                "api_correctness": {"passed": True},
            },
            "inventory_recommendations": [
                {
                    "sku": "SKU-999",
                    "avg_daily_demand_forecast": 50,
                    "lead_time_days": 5,
                    "safety_stock": 20,
                    "reorder_point": 999,  # should be ~270 (50*5 + 20) -- clearly wrong
                }
            ],
        },
    )
    reviewer.receive(bad_recommendation)

    print(f"\nReviewer verdict: {reviewer.last_verdict}")
    print(f"\nTeamLead inbox (should contain request_changes): "
          f"{[m.to_dict() for m in team_lead.inbox]}")


if __name__ == "__main__":
    run_happy_path()
    run_qa_fail_path()
    run_release_block_path()
    run_reviewer_bad_math_path()
