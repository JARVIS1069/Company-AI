"""
BaseAgent: the single class every agent in the company inherits from.

Design decision: FLAT inheritance, not a chain that mirrors the org
chart. Every agent (President, VP, Manager, ... Release) inherits
directly from BaseAgent. Who-reports-to-whom is stored as *data*
(`reports_to`), not as a class hierarchy -- so ReleaseAgent doesn't
end up inheriting QAValidator's or Reviewer's methods just because
they sit below it on the org chart. This keeps roles decoupled while
still giving every agent the same shape: permissions, messaging,
memory, and audit logging all come for free from this one class.

Role-specific behavior is added by overriding `handle_task` in a
lightweight subclass (Phase 2), not by adding new plumbing here.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from backend.permissions.rbac import has_permission
from backend.orchestrator.event_bus import event_bus
from backend.audit.audit_log import audit_log


class Message:
    """The structured contract every agent-to-agent handoff uses."""

    def __init__(
        self,
        from_agent: str,
        to_agent: str,
        action: str,
        payload: Optional[dict] = None,
        priority: str = "Normal",
        task_id: Optional[str] = None,
    ):
        self.task_id = task_id or f"TASK-{uuid.uuid4().hex[:6].upper()}"
        self.from_agent = from_agent
        self.to_agent = to_agent
        self.action = action
        self.payload = payload or {}
        self.priority = priority
        self.status = "Pending"
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "from": self.from_agent,
            "to": self.to_agent,
            "action": self.action,
            "payload": self.payload,
            "priority": self.priority,
            "status": self.status,
            "timestamp": self.timestamp,
        }


class BaseAgent:
    """Every agent in the company is (or inherits from) a BaseAgent."""

    def __init__(self, name: str, role: str, reports_to: Optional[str] = None):
        self.name = name
        self.role = role
        self.reports_to = reports_to
        self.inbox: list[Message] = []
        self.memory: list[dict] = []

        # Every agent auto-subscribes to the shared event bus under its
        # own name, so `event_bus.publish("Manager", msg)` reaches it.
        event_bus.subscribe(self.name, self.receive)

    # ---- permission-checked actions -------------------------------------
    def can(self, action: str) -> bool:
        return has_permission(self.role, action)

    def send(
        self,
        to_agent: str,
        action: str,
        payload: Optional[dict] = None,
        priority: str = "Normal",
    ) -> Message:
        """Send a structured message to another agent, enforcing RBAC."""
        if not self.can(action):
            audit_log.record(self.name, "PERMISSION_DENIED", {"action": action, "to": to_agent})
            raise PermissionError(
                f"{self.role} ('{self.name}') is not permitted to perform '{action}'"
            )

        msg = Message(self.name, to_agent, action, payload, priority)
        audit_log.record(self.name, "SEND", msg.to_dict())
        event_bus.publish(to_agent, msg)
        return msg

    def send_to_many(
        self,
        to_agents: list[str],
        action: str,
        payload: Optional[dict] = None,
        priority: str = "Normal",
        task_id: Optional[str] = None,
    ) -> list[Message]:
        """
        Fan a task out to several agents at once (e.g. TeamLead assigning
        DataEngineer, DataScientist, and MLEngineer in parallel). Each
        recipient gets its own Message with a shared task_id so their
        work can be correlated back to the same handoff.

        Pass `task_id` explicitly if the caller needs to register
        tracking state (e.g. TeamLead.pending_results) BEFORE any
        replies can arrive. The event bus delivers synchronously, so a
        recipient can call back into the sender before send_to_many
        even returns -- if the sender only registers state afterwards,
        that reply will arrive as "unknown". Generating the id up front
        and registering state first avoids that race.
        """
        if not self.can(action):
            audit_log.record(self.name, "PERMISSION_DENIED", {"action": action, "to": to_agents})
            raise PermissionError(
                f"{self.role} ('{self.name}') is not permitted to perform '{action}'"
            )

        shared_task_id = task_id or f"TASK-{uuid.uuid4().hex[:6].upper()}"
        sent: list[Message] = []
        for to_agent in to_agents:
            msg = Message(self.name, to_agent, action, payload, priority, task_id=shared_task_id)
            audit_log.record(self.name, "SEND", msg.to_dict())
            event_bus.publish(to_agent, msg)
            sent.append(msg)
        return sent

    def receive(self, message: Message) -> Message:
        """Called by the event bus when a message arrives for this agent."""
        self.inbox.append(message)
        audit_log.record(self.name, "RECEIVE", message.to_dict())
        return self.handle_task(message)

    def handle_task(self, message: Message) -> Message:
        """
        Default behavior: acknowledge and remember the task.
        Role-specific agents override this to actually do their job
        (e.g. DataEngineerAgent cleans data, QAValidatorAgent runs tests).
        """
        message.status = "Acknowledged"
        self.memory.append(message.to_dict())
        return message

    def __repr__(self) -> str:
        return f"<Agent name={self.name!r} role={self.role!r} reports_to={self.reports_to!r}>"
