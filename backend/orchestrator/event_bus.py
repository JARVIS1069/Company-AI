"""
Simple in-memory publish/subscribe bus used for inter-agent messaging.

Every agent subscribes with its own name. When one agent sends a
message "to" another, the bus delivers it to that agent's callback
(BaseAgent.receive) and keeps a full history for the audit trail /
API to inspect. This can be swapped for Redis, Kafka, etc. later
without changing any agent code.
"""
from collections import defaultdict
from typing import Callable


class EventBus:
    def __init__(self):
        self._subscribers: dict[str, list[Callable]] = defaultdict(list)
        self._history: list = []

    def subscribe(self, agent_name: str, callback: Callable):
        self._subscribers[agent_name].append(callback)

    def publish(self, to_agent: str, message):
        self._history.append(message)
        for callback in self._subscribers.get(to_agent, []):
            callback(message)

    def history(self) -> list[dict]:
        return [m.to_dict() if hasattr(m, "to_dict") else m for m in self._history]


# Single shared bus for the whole backend process.
event_bus = EventBus()
