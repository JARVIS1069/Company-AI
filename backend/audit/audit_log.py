"""
Append-only audit trail for the AI company.

Every send / receive / permission-denial / approval gets recorded here
with a timestamp. This is the system's source of truth for "what
happened and who did it" -- the core deliverable of the whole demo.
"""
import json
import threading
from datetime import datetime, timezone


class AuditLog:
    def __init__(self):
        self._entries: list[dict] = []
        self._lock = threading.Lock()

    def record(self, actor: str, event_type: str, detail: dict) -> dict:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor": actor,
            "event_type": event_type,
            "detail": detail,
        }
        with self._lock:
            self._entries.append(entry)
        return entry

    def all(self) -> list[dict]:
        return list(self._entries)

    def for_actor(self, actor: str) -> list[dict]:
        return [e for e in self._entries if e["actor"] == actor]

    def export_json(self, path: str) -> None:
        with open(path, "w") as f:
            json.dump(self._entries, f, indent=2)


# Single shared audit log for the whole backend process.
audit_log = AuditLog()
