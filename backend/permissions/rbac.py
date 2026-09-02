"""
Role-Based Access Control (RBAC) for the AI company.

Every role is granted an explicit whitelist of actions it may perform.
BaseAgent checks this before allowing an agent to send a message / take
an action, so permissions are enforced centrally instead of trusting
each agent to behave.
"""

ROLE_PERMISSIONS = {
    "President": {
        "approve_project",
        "approve_budget",
        "approve_risk",
        "approve_release",
        "view_audit_log",
    },
    "VP": {
        "define_kpis",
        "oversee_department",
        "assign_manager_goal",
        "view_audit_log",
    },
    "Manager": {
        "create_plan",
        "create_milestone",
        "assign_task",
        "set_deadline",
        "view_audit_log",
    },
    "TeamLead": {
        "choose_technical_approach",
        "assign_specialist_task",
        "coordinate_agents",
        "submit_for_qa",
        "view_audit_log",
    },
    "DataEngineer": {
        "collect_data",
        "clean_data",
        "prepare_dataset",
    },
    "DataScientist": {
        "analyze_demand",
        "build_forecast_model",
        "train_model",
    },
    "MLEngineer": {
        "evaluate_model",
        "package_model",
        "deploy_model",
    },
    "QAValidator": {
        "test_data_quality",
        "test_forecast_accuracy",
        "test_api_correctness",
        "flag_issue",
        "submit_for_inventory_optimization",
    },
    "InventoryAnalyst": {
        "compute_reorder_points",
        "flag_stockout_risk",
        "generate_inventory_recommendation",
    },
    "Reviewer": {
        "check_evidence",
        "request_changes",
        "approve_for_president",
    },
    "Release": {
        "release_to_production",
        "verify_approvals",
        "verify_quality_gates",
    },
}


def has_permission(role: str, action: str) -> bool:
    """Return True if the given role is allowed to perform the action."""
    return action in ROLE_PERMISSIONS.get(role, set())


def permissions_for(role: str) -> list[str]:
    """Return the sorted list of actions a role is allowed to perform."""
    return sorted(ROLE_PERMISSIONS.get(role, set()))
