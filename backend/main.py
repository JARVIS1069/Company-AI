"""
FastAPI entrypoint for the Company AI backend.

Phase 1 scope: stand up the 11-agent org using BaseAgent, wire them to
the shared event bus, and expose endpoints to inspect the org chart,
send a message between agents (RBAC-enforced), and read the audit log.

Role-specific behavior (what Manager actually does when it receives a
task, etc.) is added in Phase 2 by giving each agent its own
`handle_task` override -- the plumbing here doesn't change.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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
from backend.orchestrator.event_bus import event_bus
from backend.audit.audit_log import audit_log
from backend.permissions.rbac import permissions_for

app = FastAPI(title="Company AI — Multi-Agent Org", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Instantiate the org. Every entry is a plain BaseAgent for now (Phase 1);
# in Phase 2 these become thin subclasses that override handle_task().
# `reports_to` records the org chart as data, not as class inheritance.
# ---------------------------------------------------------------------------
ORG: dict[str, BaseAgent] = {
    "President": PresidentAgent(),
    "VP": VPAgent(),
    "Manager": ManagerAgent(),
    "TeamLead": TeamLeadAgent(),
    "DataEngineer": DataEngineerAgent(),
    "DataScientist": DataScientistAgent(),
    "MLEngineer": MLEngineerAgent(),
    "QAValidator": QAValidatorAgent(),
    "InventoryAnalyst": InventoryAnalystAgent(),
    "Reviewer": ReviewerAgent(),
    "Release": ReleaseAgent(),
}
# Note: BaseAgent.__init__ already subscribes each agent to the event bus.


class SendMessageRequest(BaseModel):
    from_agent: str
    to_agent: str
    action: str
    payload: dict = {}
    priority: str = "Normal"


class KickoffRequest(BaseModel):
    project: str = "Demand Forecasting & Inventory Optimization"


@app.get("/")
def root():
    return {"service": "company-ai-backend", "status": "ok", "agents": list(ORG.keys())}


@app.get("/org")
def get_org():
    """Return the org chart with each agent's role, manager, and permissions."""
    return {
        name: {
            "role": agent.role,
            "reports_to": agent.reports_to,
            "permissions": permissions_for(agent.role),
        }
        for name, agent in ORG.items()
    }


@app.post("/message")
def send_message(req: SendMessageRequest):
    """Send an RBAC-checked message from one agent to another."""
    if req.from_agent not in ORG:
        raise HTTPException(404, f"Unknown agent '{req.from_agent}'")
    if req.to_agent not in ORG:
        raise HTTPException(404, f"Unknown agent '{req.to_agent}'")

    try:
        msg = ORG[req.from_agent].send(
            req.to_agent, req.action, payload=req.payload, priority=req.priority
        )
    except PermissionError as e:
        raise HTTPException(403, str(e))
    return msg.to_dict()


@app.post("/kickoff")
def kickoff_project(req: KickoffRequest):
    """
    Kick off the full pipeline over HTTP, the same way demo_workflow.py
    does: simulate an external request landing on President's desk.

    This calls receive() directly rather than send(), because
    "request_project_approval" is a REQUEST arriving at President from
    outside the org (the user), not an action President performs --
    permission checks only apply to what an agent SENDS, not what it
    receives. This will take a few seconds: it trains a real model
    (DataScientist) as part of the cascade.
    """
    kickoff = Message("User", "President", "request_project_approval", {"project": req.project})
    result = ORG["President"].receive(kickoff)
    return {
        "kickoff_result": result.to_dict(),
        "release_record": ORG["Release"].released,
        "release_blocked": ORG["Release"].blocked,
    }


@app.get("/audit-log")
def get_audit_log():
    return audit_log.all()


@app.get("/audit-log/{actor}")
def get_audit_log_for_actor(actor: str):
    if actor not in ORG:
        raise HTTPException(404, f"Unknown agent '{actor}'")
    return audit_log.for_actor(actor)


@app.get("/history")
def get_history():
    """Full message history as delivered by the event bus."""
    return event_bus.history()
